import numpy as np
from scipy import stats
from covid.groups.people import Person
from scipy.stats import rv_discrete

class PersonError(BaseException):
    pass

class PersonDistributor:
    """
    Creates the population of the given area with sex and age given
    by the census statistics
    """
    def __init__(self, people, area, companysector_by_sex_df, workflow_dict):
        self.area = area
        self.people = people
        self.STUDENT_THRESHOLD = area.world.config["people"]["student_age_group"]
        self.ADULT_THRESHOLD = area.world.config["people"]["adult_threshold"]
        self.OLD_THRESHOLD = area.world.config["people"]["old_threshold"]
        self._init_random_variables()
        self.no_kids_area = False
        self.no_students_area = False
        self.companysector_by_sex_df = companysector_by_sex_df
        self.workflow_dict = workflow_dict


    def _init_random_variables(self):
        """
        Reads the frequencies for this area for different attributes based on
        the census data, and initializes random variables following
        the discrete distributions.
        """
        # age data
        age_freq = self.area.census_freq["age_freq"]
        age_kids_freq = age_freq.values[: self.ADULT_THRESHOLD]
        # check if there are no kids in the area, and if so,
        # declare it a no kids area.
        if np.sum(age_kids_freq) == 0.0:
            self.no_kids_area = True
        else:
            age_kid_freqs_norm = age_kids_freq / np.sum(age_kids_freq)
            self.area.kid_age_rv = stats.rv_discrete(
                values=(np.arange(0, self.ADULT_THRESHOLD), age_kid_freqs_norm)
            )
        age_adults_freq = age_freq.values[self.ADULT_THRESHOLD :]
        adult_freqs_norm = age_adults_freq / np.sum(age_adults_freq)
        self.area.adult_age_rv = stats.rv_discrete(
            values=(np.arange(self.ADULT_THRESHOLD, len(age_freq)), adult_freqs_norm)
        )
        self.area.age_rv = stats.rv_discrete(
            values=(np.arange(0, len(age_freq)), age_freq.values)
        )
        # sex data
        sex_freq = self.area.census_freq["sex_freq"]
        self.area.sex_rv = stats.rv_discrete(
            values=(np.arange(0, len(sex_freq)), sex_freq.values)
        )
        
        # work msoa area/flow data
        self.area.work_msoa_man_rv = stats.rv_discrete(
            values=(
                np.arange(0, len(self.workflow_dict["female_work_msoa"])),
                self.workflow_dict["female_work_dist"]
            )
        )
        self.area.work_msoa_woman_rv = stats.rv_discrete(
            values=(
                np.arange(0, len(self.workflow_dict["male_work_msoa"])),
                self.workflow_dict["male_work_dist"]
            )
        )

        # company data
        ## TODO add company data intilialisation from dict of distibutions in industry_distibutions.py


    def _assign_industry(self, sex, employed = True):
        '''
        :param gender: (string) male/female
        :param employed: (bool) - for now we assume all people are employed
        Note: in this script self.area.name is used and assumed to be (string) OArea code
        THIS MIGHT NEED CHANGING

        :returns: (string) letter of inductry sector
        
        Given a person's sex, their employment status, their msoarea,
        use the industry_by_sex_dict to assign each person an industry
        according to the generated probability distribution
        '''
        
        if employed == False:
            industry = 'NA'

        else:
            # access relevant probability distribtion according to the person's sex
            if sex == 'male':
                # MAY NEED TO CHANGE THE USE OF self.area TO BE CORRECT LOOKUP VALUE
                # ADD try/except statements in to allow for an area not existing (after testing though)
                # ADD industry_dict to self.area as in populate_area()
                distribution = self.companysector_by_sex_df[self.area.name]['m']
            else:
                distribution = self.companysector_by_sex_df[self.area.name]['f']

            # assign industries to numbers A->U = 1-> 21
            industry_dict = {1:'A',2:'B',3:'C',4:'D',5:'E',6:'F',7:'G',8:'H',9:'I',10:'J',
                                 11:'K',12:'L',13:'M',14:'N',15:'O',16:'P',17:'Q',18:'R',19:'S',20:'T',21:'U'}

            numbers = np.arange(1,22)
            # create discrete probability distribution
            random_variable = rv_discrete(values=(numbers,distribution))
            # generate sample from distribution
            industry_id = random_variable.rvs(size=1)
            # accss relevant indudtry label
            industry = industry_dict[industry_id[0]]
        
        return industry


    def assign_work_msoarea(self, age, sex):
        #TODO: Maybe we can put this function somewhere else?
        if age < self.ADULT_THRESHOLD:
            # too young to work
            return None
        elif age > self.OLD_THRESHOLD:
            # too old to work
            return None
        else:
            if sex == 1:
                return self.workflow_dict["female_work_msoa"][
                    self.area.work_msoa_woman_rv(size=1)[0]
                ]
            elif sex == 0:
                return self.workflow_dict["male_work_msoa"][
                    self.area.work_msoa_man_rv(size=1)[0]
                ]
            else:
                print("We are not yet able take care of non-binary people :-(")



    def populate_area(self):
        """
        Creates all people living in this area, with the charactersitics
        given by the random variables declared in _init_random_variables.
        The dictionaries with the form self.area._* are meant to be used
        by the household distributor as the pool of people available to c
        create households.
        """
        self.area._kids = {}
        self.area._men = {}
        self.area._women = {}
        self.area._oldmen = {}
        self.area._oldwomen = {}
        self.area._student_keys = {}
        # create age keys for men and women TODO # this would be use to match age of couples
        # for d in [self._men, self._women, self._oldmen, self._oldwomen]:
        #    for i in range(self.ADULT_THRESHOLD, self.OLD_THRESHOLD):
        #        d[i] = {}
        for i in range(0, self.area.n_residents):
            age_random = self.area.age_rv.rvs(size=1)[0]
            sex_random = self.area.sex_rv.rvs(size=1)[0]
            work_msoa_rnd = self.assign_work_msoarea(age_random, sex_random)
            person = Person(
                self.people.total_people, self.area, work_msoa_rnd, age_random, sex_random, 0, 0
            )
            self.people.members.append(person)
            self.area.people.append(person)
            self.people.total_people += 1
            # assign person to the right group:
            if age_random < self.ADULT_THRESHOLD:
                self.area._kids[i] = person
            elif age_random < self.OLD_THRESHOLD:
                if sex_random == 0:
                    self.area._men[i] = person
                else:
                    self.area._women[i] = person
                if person.age in [6, 7]:  # that person can be a student
                    self.area._student_keys[i] = person
            else:
                if sex_random == 0:
                    self.area._oldmen[i] = person
                else:
                    self.area._oldwomen[i] = person
            # assign person to an industry
            # add some conditions to allow for employed != True - wither age and/or from a database
            person.industry = self._assign_industry(sex=sex_random)
        
        try:
            assert (
                sum(
                    map(
                        len,
                        [
                            self.area._kids.keys(),
                            self.area._men.keys(),
                            self.area._women.keys(),
                            self.area._oldmen.keys(),
                            self.area._oldwomen.keys(),
                        ],
                    )
                )
                == self.area.n_residents
            )
        except:
            raise (
                "Number of men, women, oldmen, oldwomen, and kids doesnt add up to total population"
            )
