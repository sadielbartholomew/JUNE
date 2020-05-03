import logging
import numpy as np
import pandas as pd
from scipy.stats import rv_discrete
from tqdm.auto import tqdm
from covid.groups import Group

ic_logger = logging.getLogger(__name__)

class Company(Group):
    """
    The Company class represents a company that contains information about 
    its workers (19 - 74 years old).
    """

    def __init__(self, company_id, msoa, n_employees_max, industry):
        super().__init__(name="Company_%05d" % company_id, spec="company")
        self.id = company_id
        self.msoa = msoa
        # set the max number of employees to be the mean number in a range
        self.n_employees_max = n_employees_max
        self.n_woman = 0
        self.employees = []
        self.industry = industry


class Companies:
    def __init__(
            self,
            compsize_per_msoa_df: pd.DataFrame,
            compsec_per_msoa_df: pd.DataFrame,
        ):
        """
        Create companies and provide functionality to allocate workers.

        Parameters
        ----------
        compsize_per_msoa_df: pd.DataFram
            Nr. of companies within a size-range per MSOA.

        compsec_per_msoa_df: pd.DataFrame
            Nr. of companies per industry sector per MSOA.
        """
        self.members = []
        self.init_companies(
            compsize_per_msoa_df,
            compsec_per_msoa_df,
        )

    @classmethod
    def from_file(
        cls,
        companysize_file: str,
        company_per_sector_per_msoa_file: str,
        ) -> "Companies":
        """
        Parameters
        ----------
        companysize_file: str
        company_per_sector_per_msoa_file: str
        """
        compsize_per_msoa_df = pd.read_csv(companysize_file, index_col=0)
        compsize_per_msoa_df = compsize_per_msoa_df.div(
            compsize_per_msoa_df.sum(axis=1), axis=0
        )
        compsec_per_msoa_df = pd.read_csv(
            company_per_sector_per_msoa_file, index_col=0
        )
        return Companies(compsize_per_msoa_df, compsec_per_msoa_df)

    def _compute_size_mean(self, sizegroup):
        """
        Given company size group calculates mean
        """
        # ensure that read_companysize_census() also returns number of companies
        # in each size category
        size_min, size_max = sizegroup.split('-')
        if size_max == "XXX" or size_max == 'xxx':
            size_mean = 1500
        else:
            size_min = float(size_min)
            size_max = float(size_max)
            size_mean = (size_max - size_min)/2.0

        return int(size_mean)
    
    def init_companies(self, compsize_per_msoa_df, compsec_per_msoa_df):
        """
        Initializes all companies across all msoareas
        """
        companies = []
        
        compsize_labels = compsize_per_msoa_df.columns.values
        compsize_labels_encoded = np.arange(1, len(compsize_labels) + 1)
        
        size_dict = {
            (idx+1): self._compute_size_mean(size_label)
            for idx, size_label in enumerate(compsize_labels)
        }
        
        # Run through each MSOArea
        for idx, msoarea_name in enumerate(compsec_per_msoa_df['msoareas']):
            compsec_in_msoa_df = compsec_per_msoa_df.loc[msoarea_name]
            compsize_freq_df = compsize_per_msoa_df.loc[msoarea_name]
            comp_size_rv = rv_discrete(
                values=(comp_size_col_encoded, compsize_freq_df.values)
            )
            comp_size_rnd_array = comp_size_rv.rvs(
                size=int(compsec_in_msoa_df.sum())
            )
            
            # Run through each industry sector
            for compsec_label, nr_of_comp in compsec_in_msoa_df.iterrows():
                
                # Run through all companies within sector within MSOA
                for i in range(int(nr_of_comp)):
                    company = Company(
                        company_id=i,
                        msoa=msoarea_name,
                        n_employees_max=size_dict[comp_size_rnd_array[i]],
                        industry=compsec_label
                    )
                        
                    companies.append(company)

        self.members = companies
