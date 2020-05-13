import os
import pickle
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import numpy as np
import yaml
import pickle
from tqdm.auto import tqdm  # for a fancy progress bar

from june.groups import Hospitals
from june.box.box_mode import Boxes, Box
from june.geography import Geography
from june.demography import Demography, People
from june.logger_creation import logger
from june.distributors import (
    SchoolDistributor,
    HospitalDistributor,
    HouseholdDistributor,
    CareHomeDistributor,
    WorkerDistributor,
)

logger = logging.getLogger(__name__)


class World:
    """
    This Class creates the world that will later be simulated.
    The world will be stored in pickle, but a better option needs to be found.
    
    Note: BoxMode = Demography +- Sociology - Geography
    """

    def __init__(
        self,
        geography: Geography,
        demography: Demography,
        include_households: bool = True,
            include_commute: bool = True,
        box_mode = False
    ):
        """
        Initializes a world given a geography and a demography. For now, households are
        a special group because they require a mix of both groups (we need to fix
        this later). 

        Parameters
        ----------
        geography
            an instance of the Geography class specifying the "board"
        demography
            an instance of the Demography class with generators to generate people with 
            certain demographic attributes
        include_households
            whether to include households in the world or not (defualt = True)
        """
        self.box_mode = box_mode
        if self.box_mode:
            self.hospitals = Hospitals.for_box_mode()
            self.people = demography.populate(geography.areas)
            self.boxes = Boxes([Box()])
            self.boxes.members[0].set_population(self.people)
            return None
        self.areas = geography.areas
        self.super_areas = geography.super_areas
        print("populating the world's geography with the specified demography...")
        self.people = demography.populate(self.areas)

        if hasattr(geography, "carehomes"):
            self.carehomes = geography.carehomes
            CareHomeDistributor().populate_carehome_in_areas(self.areas)
        if include_households:
            household_distributor = HouseholdDistributor.from_file()
            self.households = household_distributor.distribute_people_and_households_to_areas(
                self.areas
            )
        if (
            hasattr(geography, "companies")
            or hasattr(geography, "hospitals")
            or hasattr(geography, "schools")
        ):
            worker_distr = WorkerDistributor.for_geography(
                geography
            )  # atm only for_geography()
            worker_distr.distribute(geography, self.people)

        if hasattr(geography, "schools"):
            self.schools = geography.schools
            school_distributor = SchoolDistributor(geography.schools)
            school_distributor.distribute_kids_to_school(self.areas)
            school_distributor.distribute_teachers_to_schools_in_super_areas(self.super_areas)

        if hasattr(geography, "companies"):
            self.companies = geography.companies

        if include_commute:
            # CommuteCity
            self.commutecities = CommuteCities(self.inputs.uk_pcs_coordinates,self.inputs.msoa_coordinates) # FILE READIN
            self.commutecities.init_non_london(self.inputs.non_london_stat_pcs) # FILE READIN
            # Crucial that London is initialise second, after non-London
            self.commutecities.init_london(self.inputs.london_stat_pcs) # FILE READIN

            self.commutecity_distributor = CommuteCityDistributor(self.commutecities.members, self.super_areas.members)
            self.commutecity_distributor.distribute_people()

            # CommuteHub
            self.commutehubs = CommuteHubs(self.commutecities.members, self.inputs.msoa_coordinates, init=True) # FILE READIN

            self.commutehub_distributor = CommuteHubDistributor(self.inputs.msoa_oa_coordinates, self.commutecities.members) # FILE READIN
            self.commutehub_distributor.distribute_people()

            # CommuteUnit
            self.commuteunits = CommuteUnits(self.commutehubs.members, init=True)

            self.commuteunit_distributor = CommuteUnitDistributor(self.commutehubs.members)
            # unit distirbutor is dynamic and should be called at each time step - leave this until later
            #self.commuteunit_distributor.distribute_people()

            #CommuteCityUnit
            self.commutecityunits = CommuteCityUnits(self.commutecities.members, init = True)

            self.commutecityunit_distributor = CommuteCityDistributor(self.commutecities.members)
                        
        if hasattr(geography, "hospitals"):
            self.hospitals = geography.hospitals
            hospital_distributor = HospitalDistributor(geography.hospitals)
            hospital_distributor.distribute_medics_to_super_areas(self.super_areas)
        
        if hasattr(geography, "cemeteries"):
            self.cemeteries = geography.cemeteries

    @classmethod
    def from_geography(cls, geography: Geography, box_mode = False):
        """
        Initializes the world given a geometry. The demography is calculated
        with the default settings for that geography.
        """
        demography = Demography.for_geography(geography)
        return cls(geography, demography, box_mode=box_mode)

    def to_pickle(self, save_path):
        with open(save_path, "wb") as f:
            pickle.dump(self, f)
