import logging
from itertools import count
from typing import List, Dict, Optional

import numpy as np
import pandas as pd
import yaml
from scipy import stats

from june import paths
from june.demography import Person, Population
from june.geography import Geography

default_workflow_file = paths.data_path / "processed/flow_in_msoa_wu01ew_2011.csv"
default_sex_per_sector_per_superarea_file = paths.data_path / "processed/census_data/company_data/industry_by_sex_ew.csv"
default_areas_map_path = paths.data_path / "processed/geographical_data/oa_msoa_region.csv"
default_config_file = paths.configs_path / "defaults/distributors/worker_distributor.yaml"
logger = logging.getLogger(__name__)


class WorkerDistributor:
    """
    This class distributes people to their work. Work is understood as the main
    activity any individuum pursues during the week, e.g. for pupils it is
    learning in schools and for adults it is their work in companies and
    key sectors for which data was provided.
    """

    def __init__(
            self,
            workflow_df: pd.DataFrame,
            sex_per_sector_df: pd.DataFrame,
            age_range: List[int],
            sub_sector_ratio: dict,
            sub_sector_distr: dict,
            non_geographical_work_location: dict,
    ):
        """
        Parameters
        ----------
        workflow_df
            DataFrame that contains information about where man and woman go to work
            with respect to their SuperArea of residence.
        sector_by_sex_df
            DataFrame that contains information on the nr. of man and woman working
            in different sectors per Area (note that it is thus not provided for the
            SuperArea).
        sub_sector_ratio 
            For each region containing the ratio of man and woman respectively that
            work in any key sector type. (e.g. for healthcare, how many man work
            in the key occupations, such as nurses within that sector)
        sub_sector_distr
            For each region containing how many of man and woman respectively
            work in any key sector jobs, such as primary teachers or medical
            practitioners.
        non_geographical_work_location:
            Special work place locations in dataset that do not correspond to a
            SuperArea name but to special cases such as:
            "home", "oversea", "offshore", ...
            They are the key of the dictionary. The value carries the action
            on what should be done with these workers. Currently they are:
            "home": let them work from home
            "bind": randomly select a SuperArea to send the worker to work in
        """
        self.workflow_df = workflow_df
        self.sex_per_sector_df = sex_per_sector_df
        self.age_range = age_range
        self.sub_sector_ratio = sub_sector_ratio
        self.sub_sector_distr = sub_sector_distr
        self.non_geographical_work_location = non_geographical_work_location
        self._boundary_workers_counter = count()
        self.n_boundary_workers = 0

    def distribute(
            self,
            geography: Geography,
            population: Population,
    ):
        """
        Assign any person within the eligible working age range a location
        (SuperArea) of their work, and the sector (e.g. "P"=educatioin) of
        their work.
        
        Parameters
        ----------
        """
        self.geography = geography
        for area in iter(geography.areas):  # TODO a.t.m. only for_geography() supported
            wf_area_df = self.workflow_df.loc[(area.super_area.name,)]
            self._work_place_lottery(area.name, wf_area_df, len(area.people))
            for idx, person in enumerate(area.people):
                if self.age_range[0] <= person.age <= self.age_range[1]:
                    self._assign_work_location(idx, person, wf_area_df)
                    self._assign_work_sector(idx, person)
        logger.info(f"There are {self.n_boundary_workers} who had to be told to stay real")

    def _work_place_lottery(
            self,
            area_name: str,
            wf_area_df: pd.DataFrame,
            n_workers: int
    ):
        """
        Create lottery that randomly assigns people a sector and location
        of work.
        """
        # work msoa area/flow data
        work_msoa_man_rv = stats.rv_discrete(
            values=(
                np.arange(0, len(wf_area_df.index.values)),
                wf_area_df["n_man"].values,
            )
        )
        self.work_msoa_man_rnd = work_msoa_man_rv.rvs(size=n_workers)
        work_msoa_woman_rv = stats.rv_discrete(
            values=(
                np.arange(0, len(wf_area_df.index.values)),
                wf_area_df["n_woman"].values,
            )
        )
        self.work_msoa_woman_rnd = work_msoa_woman_rv.rvs(size=n_workers)
        # companies data
        numbers = np.arange(1, 22)
        m_col = [col for col in self.sex_per_sector_df.columns.values if "m " in col]

        f_col = [col for col in self.sex_per_sector_df.columns.values if "f " in col]
        self.sector_dict = {
            (idx + 1): col.split(" ")[-1] for idx, col in enumerate(m_col)
        }
        try:
            # fails if no female work in this Area
            distribution_female = self.sex_per_sector_df.loc[area_name][f_col].fillna(0).values
            self.sector_distribution_female = stats.rv_discrete(
                values=(numbers, distribution_female)
            )
            self.sector_female_rnd = self.sector_distribution_female.rvs(size=n_workers)
        except:
            pass
        try:
            # fails if no male work in this Area
            distribution_male = self.sex_per_sector_df.loc[area_name][m_col].fillna(0).values
            self.sector_distribution_male = stats.rv_discrete(
                values=(numbers, distribution_male)
            )
            self.sector_male_rnd = self.sector_distribution_male.rvs(size=n_workers)
        except:
            pass

    def _assign_work_location(self, i: int, person: Person, wf_area_df: pd.DataFrame):
        """
        Employ people in any given sector.
        """
        if person.sex == "f":
            work_location = wf_area_df.index.values[self.work_msoa_woman_rnd[i]]
        else:
            work_location = wf_area_df.index.values[self.work_msoa_man_rnd[i]]
        super_area = [
            super_area
            for super_area in self.geography.super_areas
            if super_area.name == work_location
        ]
        if len(super_area) != 0:
            super_area = super_area[0]
            super_area.add_worker(person)
        elif work_location in list(self.non_geographical_work_location.keys()):
            if self.non_geographical_work_location[work_location] == "home":
                person.work_super_area = "home"
            elif self.non_geographical_work_location[work_location] == "bind":
                self._select_rnd_superarea(person)
        else:
            # TODO count people who work outside of the region we currently simulate
            self._select_rnd_superarea(person)
            self.n_boundary_workers = next(self._boundary_workers_counter)
   
    def _select_rnd_superarea(self, person: Person):
        """
        Selects random SuperArea to send a worker to work in
        """
        idx = np.random.choice(np.arange(len(self.geography.super_areas)))
        self.geography.super_areas.members[idx].add_worker(person)

    def _assign_work_sector(self, i: int, person: Person):
        """
        Employ people in a given SuperArea.
        """
        if person.sex == "f":
            sector_idx = self.sector_female_rnd[i]
        else:
            sector_idx = self.sector_male_rnd[i]
        person.sector = self.sector_dict[sector_idx]

        if person.sector in list(self.sub_sector_ratio.keys()):
            self._assign_sub_sector(person)

    def _assign_sub_sector(self, person):
        """
        Assign sub-sector job as defined in config
        """
        MC_random = np.random.uniform()
        ratio = self.sub_sector_ratio[person.sector][person.sex]
        distr = self.sub_sector_distr[person.sector][person.sex]
        if MC_random < ratio:
            sub_sector_idx = stats.rv_discrete(
                values=(np.arange(len(distr)), distr)
            ).rvs(size=1)
            person.sub_sector = (
                self.sub_sector_distr[person.sector]["label"][sub_sector_idx[0]]
            )

    @classmethod
    def for_geography(
            cls,
            geography: Geography,
            workflow_file: str = default_workflow_file,
            sex_per_sector_file: str = default_sex_per_sector_per_superarea_file,
            config_file: str = default_config_file,
    ) -> "WorkerDistributor":
        """
        Parameters
        ----------
        geography
            an instance of the geography class
        """
        area_names = [super_area.name for super_area in geography.super_areas]
        if len(area_names) == 0:
            raise CompanyError("Empty geography!")
        return cls.for_super_areas(
            area_names,
            workflow_file,
            sex_per_sector_file,
            config_file,
        )

    @classmethod
    def for_zone(
            cls,
            filter_key: Dict[str, list],
            areas_maps_path: str = default_areas_map_path,
            workflow_file: str = default_workflow_file,
            sex_per_sector_file: str = default_sex_per_sector_per_superarea_file,
            config_file: str = default_config_file,
    ) -> "WorkerDistributor":
        """
        
        Example
        -------
            filter_key = {"region" : "North East"}
            filter_key = {"msoa" : ["EXXXX", "EYYYY"]}
        """
        if len(filter_key.keys()) > 1:
            raise NotImplementedError("Only one type of area filtering is supported.")
        if "oa" in len(filter_key.keys()):
            raise NotImplementedError("Company data only for the SuperArea (MSOA) and above.")
        geo_hierarchy = pd.read_csv(areas_maps_path)
        zone_type, zone_list = filter_key.popitem()
        area_names = geo_hierarchy[geo_hierarchy[zone_type].isin(zone_list)]["msoa"]
        if len(area_names) == 0:
            raise CompanyError("Region returned empty area list.")
        return cls.for_super_areas(
            area_names,
            workflow_file,
            sex_per_sector_file,
            config_file,
        )

    @classmethod
    def for_super_areas(
            cls,
            area_names: List[str],
            workflow_file: str = default_workflow_file,
            sex_per_sector_file: str = default_sex_per_sector_per_superarea_file,
            config_file: str = default_config_file,
    ) -> "WorkerDistributor":
        """
        """
        return cls.from_file(
            area_names,
            workflow_file,
            sex_per_sector_file,
            config_file,
        )

    @classmethod
    def from_file(
            cls,
            area_names: Optional[List[str]] = [],
            workflow_file: str = default_workflow_file,
            sex_per_sector_file: str = default_sex_per_sector_per_superarea_file,
            config_file: str = default_config_file,
    ) -> "WorkerDistributor":
        """
        Parameters
        ----------
        area_names
            List of SuperArea names for which to initiate WorkerDistributor
        workflow_file
            Filename to data containing information about where man and woman
            go to work with respect to their SuperArea of residence.
        sex_per_sector_file
        education_sector_file
        healthcare_sector_file
        """
        workflow_df = _load_workflow_df(workflow_file, area_names)
        sex_per_sector_df = _load_sex_per_sector(sex_per_sector_file, area_names)
        with open(config_file) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return WorkerDistributor(
            workflow_df,
            sex_per_sector_df,
            **config,
        )


def _load_workflow_df(
        workflow_file: str,
        area_names: Optional[List[str]] = []
) -> pd.DataFrame:
    wf_df = pd.read_csv(
        workflow_file,
        delimiter=",",
        delim_whitespace=False,
        skiprows=1,
        usecols=[0, 1, 3, 4],
        names=["msoa", "work_msoa", "n_man", "n_woman"],
    )
    if len(area_names) != 0:
        wf_df = wf_df[wf_df["msoa"].isin(area_names)]
    # convert into ratios
    wf_df = wf_df.groupby(["msoa", "work_msoa"]).agg(
        {"n_man": "sum", "n_woman": "sum"}
    )
    wf_df["n_man"] = (
        wf_df.groupby(level=0)["n_man"]
            .apply(lambda x: x / float(x.sum(axis=0)))
            .values
    )
    wf_df["n_woman"] = (
        wf_df.groupby(level=0)["n_woman"]
            .apply(lambda x: x / float(x.sum(axis=0)))
            .values
    )
    return wf_df


def _load_sex_per_sector(
        sector_by_sex_file: str,
        area_names: Optional[List[str]] = [],
) -> pd.DataFrame:
    sector_by_sex_df = pd.read_csv(sector_by_sex_file, index_col=0)
    # define all columns in csv file relateing to males
    m_columns = [col for col in sector_by_sex_df.columns.values if "m " in col]
    m_columns.remove('m all')
    m_columns.remove('m R S T U')
    f_columns = [col for col in sector_by_sex_df.columns.values if "f " in col]
    f_columns.remove('f all')
    f_columns.remove('f R S T U')

    uni_columns = [col for col in sector_by_sex_df.columns.values if "all " in col]
    sector_by_sex_df = sector_by_sex_df.drop(
        uni_columns + ['m all', 'm R S T U', 'f all', 'f R S T U'], axis=1,
    )

    if len(area_names) != 0:
        geo_hierarchy = pd.read_csv(default_areas_map_path)
        area_names = geo_hierarchy[geo_hierarchy["msoa"].isin(area_names)]["oa"]
        sector_by_sex_df = sector_by_sex_df.loc[area_names]
        if (np.sum(sector_by_sex_df["m Q"]) == 0) and \
                (np.sum(sector_by_sex_df["f Q"]) == 0):
            logger.info(f"There exists no Healthcare sector in this geography.")
        if (np.sum(sector_by_sex_df["m P"]) == 0) and \
                (np.sum(sector_by_sex_df["f P"]) == 0):
            logger.info(f"There exists no Education sector in this geography.")

    # convert counts to ratios
    sector_by_sex_df.loc[:, m_columns] = sector_by_sex_df.loc[:, m_columns].div(
        sector_by_sex_df[m_columns].sum(axis=1), axis=0
    )
    sector_by_sex_df.loc[:, f_columns] = sector_by_sex_df.loc[:, f_columns].div(
        sector_by_sex_df[f_columns].sum(axis=1), axis=0
    )
    return sector_by_sex_df
