import numpy as np
import random
import yaml
from scipy import stats
import warnings
from covid.groups import Household, Households
from collections import OrderedDict
from covid.groups import Person
from covid.groups import Area
import pandas as pd
from pathlib import Path

default_config_filename = (
    Path(__file__).parent.parent.parent
    / "configs/defaults/distributors/HouseholdDistributor.yaml"
)

default_age_difference_files_folder = (
    Path(__file__).parent.parent.parent / "data/processed/age_difference"
)


"""
This file contains routines to distribute people to households
according to census data.
"""


class HouseholdError(BaseException):
    """ class for throwing household related errors """


def get_closest_element_in_array(array, value):
    min_idx = np.argmin(np.abs(value - array))
    return array[min_idx]


def count_items_in_dict(dictionary):
    counter = 0
    for age in dictionary:
        counter += len(dictionary[age])
    return counter


def count_remaining_people(dict1, dict2):
    return count_items_in_dict(dict1) + count_items_in_dict(dict2)


class HouseholdDistributor:
    def __init__(
        self,
        first_kid_parent_age_differences: dict,
        second_kid_parent_age_differences: dict,
        couples_age_differences: dict,
        number_of_random_numbers=int(1e6),
        kid_max_age=17,
        student_min_age=18,
        student_max_age=25,
        old_min_age=65,
        old_max_age=99,
        adult_min_age=18,
        adult_max_age=64,
        young_adult_min_age=18,
        young_adult_max_age=35,
        max_age_to_be_parent=64,
        max_household_size=8,
        allowed_household_compositions: dict = None,
    ):
        """
        Tool to populate areas with households and fill them with the correct composition based on census data.
        The most important function is ``distribute_people_to_households`` which takes people in an area and fills 
        them into households.

        Parameters
        ----------
        first_kid_parent_age_differences:
            dictionary where keys are the age differences between a mother and her FIRST kid.
            The values are the probabilities of each age difference.
        second_kid_parent_age_differences:
            dictionary where keys are the age differences between a mother and her SECOND kid.
            The values are the probabilities of each age difference.
        couples_age_differences:
            dictionary where keys are the age differences between a woman and a man at the time of marriage. A value of 20
            means that the man is 20 years older than the woman.
            The values are the probabilities of each age difference.
        number_of_random_numbers:
            Number of random numbers required. This should be set to the number of people living in the area, minimum.
        """
        self.kid_max_age = kid_max_age
        self.student_min_age = student_min_age
        self.student_max_age = student_max_age
        self.old_min_age = old_min_age
        self.old_max_age = old_max_age
        self.adult_min_age = adult_min_age
        self.adult_max_age = adult_max_age
        self.young_adult_min_age = young_adult_min_age
        self.young_adult_max_age = young_adult_max_age
        self.max_age_to_be_parent = max_age_to_be_parent
        self.max_household_size = max_household_size
        self.allowed_household_compositions = allowed_household_compositions
        if self.allowed_household_compositions is None:
            self.allowed_household_compositions = [
                "1 0 >=0 1 0",
                ">=2 0 >=0 1 0",
                "1 0 >=0 2 0",
                ">=2 0 >=0 2 0",
                "1 0 >=0 >=1 >=0",
                ">=2 0 >=0 >=1 >=0",
                "0 0 0 0 >=2",
                "0 >=1 0 0 0",
                "0 0 0 0 1",
                "0 0 0 0 2",
                "0 0 0 1 0",
                "0 0 0 2 0",
                "0 0 >=1 1 0",
                "0 0 >=1 2 0",
                "0 0 >=0 >=0 >=0",
                ">=0 >=0 >=0 >=0 >=0",
            ]

        self._first_kid_parent_age_diff_rv = stats.rv_discrete(
            values=(
                list(first_kid_parent_age_differences.keys()),
                list(first_kid_parent_age_differences.values()),
            ),
        )
        self._second_kid_parent_age_diff_rv = stats.rv_discrete(
            values=(
                list(second_kid_parent_age_differences.keys()),
                list(second_kid_parent_age_differences.values()),
            ),
        )
        self._couples_age_rv = stats.rv_discrete(
            values=(
                list(couples_age_differences.keys()),
                list(couples_age_differences.values()),
            )
        )
        self._random_sex_rv = stats.rv_discrete(values=((0, 1), (0.5, 0.5)))
        self._refresh_random_numbers_list(number_of_random_numbers)

    @classmethod
    def from_file(
        cls,
        husband_wife_filename: str = None,
        parent_child_filename: str = None,
        config_filename: str = default_config_filename,
        number_of_random_numbers=int(1e6),
    ) -> "HouseholdDistributor":
        """
        Initializes a household distributor from file. If they are not specified they are assumed to be in the default
        location.

        Parameters
        ----------
        husband_wife_filename:
            Path of the CSV file containing in one column the age differences between
            wife and husband (relative to the wife) and in the second columns the 
            probability of that age difference.
        parent_child_filename:
            Path of the CSV file containing in one column the age differences between a 
            mother and her kids. The second and third columns must contain the probabilities
            for the first and second kid respectively.
        config_filename:
            Path of the config file defining the different age groups.
        number_of_random_numbers:
            Number of random numbers to initialize. This should be equal to the number of
            people in the area we want to put households in.
        """

        with open(config_filename) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        if husband_wife_filename is None:
            husband_wife_df = pd.read_csv(
                default_age_difference_files_folder / "husband_wife.csv"
            )
        else:
            husband_wife_df = pd.read_csv(husband_wife_filename)
        if parent_child_filename is None:
            parent_child_df = pd.read_csv(
                default_age_difference_files_folder / "parent_child.csv"
            )
        else:
            parent_child_df = pd.read_csv(parent_child_filename)
        return cls.from_df(
            husband_wife_df,
            parent_child_df,
            number_of_random_numbers=number_of_random_numbers,
            **config,
        )

    @classmethod
    def from_df(
        cls, husband_wife_df: pd.DataFrame, parent_child_df: pd.DataFrame, **kwargs,
    ) -> "HouseholdDistributor":
        """
        Initializes a household distributor from dataframes. If they are not specified they are assumed to be in the default
        location.

        Parameters
        ----------
        husband_wife_filename:
            Dataframe containing as index the age differences between wife and husband (relative to the wife)
            and one column with the probability of that age difference.
        parent_child_filename:
            Dataframe containing as index the age differences between a mother and her kids.
            The first and second columns must contain the probabilities for the first and second kid respectively.
        Keyword Arguments:
            Any extra argument that is taken by the __init__ of HouseholdDistributor.
        """
        kids_parents_age_diff_1 = parent_child_df["0"]
        kids_parents_age_diff_2 = parent_child_df["1"]
        couples_age_diff = husband_wife_df
        first_kid_parent_age_differences = kids_parents_age_diff_1.to_dict()
        second_kid_parent_age_differences = kids_parents_age_diff_2.to_dict()
        couples_age_differences = couples_age_diff.to_dict()["frequency"]
        return cls(
            first_kid_parent_age_differences,
            second_kid_parent_age_differences,
            couples_age_differences,
            **kwargs,
        )

    def _refresh_random_numbers_list(self, n=1000000) -> None:
        """
        Samples one million age differences for couples and parents-kids. Sampling in batches makes the code much faster. They are converted to lists so they can be popped.
        """
        # create one million random age difference array to save time
        self._couples_age_differences_list = list(self._couples_age_rv.rvs(size=n))
        self._first_kid_parent_age_diff_list = list(
            self._first_kid_parent_age_diff_rv.rvs(size=n)
        )
        self._second_kid_parent_age_diff_list = list(
            self._second_kid_parent_age_diff_rv.rvs(size=n)
        )
        self._random_sex_list = list(self._random_sex_rv.rvs(size=n))

    def distribute_people_to_households(
        self,
        area: Area,
        number_households_per_composition: dict,
        n_students: int,
        n_people_in_communal: int,
    ) -> Households:
        """
        Given a populated output area, it distributes the people to households. 
        The instance of the Area class, area, should have two dictionary attributes, 
        ``men_by_age`` and ``women_by_age``. The keys of the dictionaries are the ages 
        and the values are the Person instances. The process of creating these dictionaries
        is done in people_distributor.py.
        The ``number_households_per_composition`` argument is a dictionary containing the 
        number of households per each composition. We obtain this from the nomis dataset and 
        should be read by the inputs class in the world init.

        Parameters
        ----------
        area:
            area from which to take people and distribute households.
        number_households_per_composition:
            dictionary containing the different possible household compositions and the number of 
            households with that composition as key.
            Example:
            The area E00062207 has this configuration:
            number_households_per_composition = {
            "0 0 0 0 1"           :   15
            "0 0 0 1 0"           :   20
            "0 0 0 0 2"           :   11
            "0 0 0 2 0"           :   24
            "1 0 >=0 2 0"         :   12
            ">=2 0 >=0 2 0"       :    9
            "0 0 >=1 2 0"         :    6
            "1 0 >=0 1 0"         :    5
            ">=2 0 >=0 1 0"       :    3
            "0 0 >=1 1 0"         :    7
            "1 0 >=0 >=1 >=0"     :    0
            ">=2 0 >=0 >=1 >=0"   :    1
            "0 >=1 0 0 0"         :    0
            "0 0 0 0 >=2"         :    0
            "0 0 >=0 >=0 >=0"     :    1
            ">=0 >=0 >=0 >=0 >=0" :    0
            }
            The encoding follows the rule "1 2 3 4 5" = 1 kid, 2 students (that live in student households), 3 young adults, 4 adults, and 5 old people.
        n_students:
            the number of students living this area.
        n_people_in_communal:
            the number of people living in communal establishments in this area.
        """
        # We use these lists to store households that can accomodate different age groups
        # They will be useful to distribute remaining people at the end.
        households_with_extra_adults = []
        households_with_extra_oldpeople = []
        households_with_extra_kids = []
        households_with_extra_youngadults = []
        households_with_kids = []
        if not area.men_by_age and not area.women_by_age:
            raise HouseholdError("No people in Area!")
        total_number_of_households = 0
        for key in number_households_per_composition:
            total_number_of_households += number_households_per_composition[key]
            if key not in self.allowed_household_compositions:
                raise HouseholdError(f"Household composition {key} not supported")

        # student households
        key = "0 >=1 0 0 0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_all_student_households(
                    area=area,
                    n_students=n_students,
                    student_houses_number=house_number,
                )

        # single person old
        key = "0 0 0 0 1"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_oldpeople_households(
                    people_per_household=1,
                    n_households=house_number,
                    max_household_size=1,
                    extra_people_lists=(
                        households_with_extra_adults,
                        households_with_extra_oldpeople,
                    ),
                    area=area,
                )

        # couples old
        key = "0 0 0 0 2"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_oldpeople_households(
                    people_per_household=2,
                    n_households=house_number,
                    max_household_size=2,
                    extra_people_lists=(
                        households_with_extra_adults,
                        households_with_extra_oldpeople,
                    ),
                    area=area,
                )

        # old people houses with possibly more old people
        key = "0 0 0 0 >=2"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_oldpeople_households(
                    people_per_household=2,
                    n_households=house_number,
                    area=area,
                    extra_people_lists=(households_with_extra_oldpeople,),
                )

        # possible multigenerational, one kid and one adult minimum.
        # even though the number of old people is >=0, we put one old person
        # always if possible.
        key = "1 0 >=0 >=1 >=0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_families_households(
                    n_households=house_number,
                    kids_per_house=1,
                    parents_per_house=1,
                    old_per_house=1,
                    extra_people_lists=(
                        households_with_kids,
                        households_with_extra_youngadults,
                        households_with_extra_adults,
                    ),
                    area=area,
                )
        # same as the previous one but with 2 kids minimum.
        key = ">=2 0 >=0 >=1 >=0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_families_households(
                    n_households=house_number,
                    kids_per_house=2,
                    parents_per_house=1,
                    old_per_house=1,
                    area=area,
                    extra_people_lists=(
                        households_with_extra_kids,
                        households_with_kids,
                        households_with_extra_youngadults,
                        households_with_extra_adults,
                    ),
                )

        # one kid and one parent for sure, possibly extra young adults.
        key = "1 0 >=0 1 0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_families_households(
                    n_households=house_number,
                    kids_per_house=1,
                    parents_per_house=1,
                    old_per_house=0,
                    area=area,
                    extra_people_lists=(
                        households_with_kids,
                        households_with_extra_youngadults,
                    ),
                )
        # same as above with two kids instead.
        key = ">=2 0 >=0 1 0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_families_households(
                    n_households=house_number,
                    kids_per_house=2,
                    parents_per_house=1,
                    old_per_house=0,
                    area=area,
                    extra_people_lists=(
                        households_with_extra_kids,
                        households_with_kids,
                        households_with_extra_youngadults,
                    ),
                )
        # 1 kid and two parents with possibly young adults.
        key = "1 0 >=0 2 0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_families_households(
                    n_households=house_number,
                    kids_per_house=1,
                    parents_per_house=2,
                    old_per_house=0,
                    area=area,
                    extra_people_lists=(
                        households_with_kids,
                        households_with_extra_youngadults,
                    ),
                )
        # same as above but two kids.
        key = ">=2 0 >=0 2 0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_families_households(
                    n_households=house_number,
                    kids_per_house=2,
                    parents_per_house=2,
                    old_per_house=0,
                    area=area,
                    extra_people_lists=(
                        households_with_kids,
                        households_with_extra_kids,
                        households_with_extra_youngadults,
                    ),
                )
        # couple adult, it's possible to have a person < 65 with one > 65
        key = "0 0 0 2 0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_nokids_households(
                    adults_per_household=2,
                    n_households=house_number,
                    max_household_size=2,
                    area=area,
                    extra_people_lists=(
                        households_with_extra_adults,
                        households_with_extra_oldpeople,
                    ),
                )
        # one adult (parent) and one young adult (non-dependable child)
        key = "0 0 >=1 1 0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_youngadult_with_parents_households(
                    adults_per_household=1,
                    n_households=house_number,
                    area=area,
                    extra_people_lists=(households_with_extra_youngadults,),
                )

        # same as above but two adults
        key = "0 0 >=1 2 0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_youngadult_with_parents_households(
                    adults_per_household=2,
                    n_households=house_number,
                    area=area,
                    extra_people_lists=(households_with_extra_youngadults,),
                )

        # single person adult
        key = "0 0 0 1 0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                self.fill_nokids_households(
                    adults_per_household=1,
                    n_households=house_number,
                    max_household_size=1,
                    area=area,
                )

        # other to be filled with remaining young adults, adults, and old people
        key = "0 0 >=0 >=0 >=0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            if house_number > 0:
                for _ in range(house_number):
                    household = self._create_household(area)
                    households_with_extra_youngadults.append(household)
                    households_with_extra_adults.append(household)
                    households_with_extra_oldpeople.append(household)

        # we have so far filled the minimum household configurations.
        # If the area has communal establishments, we fill those next.
        # The remaining people are then assigned to the existing households
        # trying to fit their household composition as much as possible

        remaining_people = count_remaining_people(area.men_by_age, area.women_by_age)
        communal_houses = 0  # this is used to count houses later
        key = ">=0 >=0 >=0 >=0 >=0"
        if key in number_households_per_composition:
            house_number = number_households_per_composition[key]
            communal_houses = house_number
            if n_people_in_communal >= 0 and house_number > 0:
                to_fill_in_communal = min(n_people_in_communal, remaining_people)
                self.fill_all_communal_establishments(
                    n_establishments=house_number,
                    n_people_in_communal=to_fill_in_communal,
                    area=area,
                )

        # remaining people
        self.fill_random_people_to_existing_households(
            households_with_extra_kids,
            households_with_kids,
            households_with_extra_youngadults,
            households_with_extra_adults,
            households_with_extra_oldpeople,
            area=area,
        )

        # make sure we have the correct number of households
        if not (
            total_number_of_households - communal_houses
            <= len(area.households)
            <= total_number_of_households
        ):
            raise HouseholdError("Number of households does not match.")
        # destroy any empty houses
        area.households = [
            household for household in area.households if household.size > 0
        ]

        # create Households super group
        households = Households()
        for household in area.households:
            households.members.append(household)
        return households

    def _create_household(
        self, area: Area, communal: bool = False, max_household_size: int = np.inf
    ) -> Household:
        """Creates household in the area.

        Parameters
        ----------
        area: 
            Area in which to create the household.
        communal:
            Whether it is a communal establishment (True) or not (False).
        max_household_size:
            Maximum number of people allowed in the household.

        """
        household = Household(communal=communal, max_size=max_household_size)
        area.households.append(household)
        return household

    def _add_to_household(
        self, household: Household, person: Person, subgroup=None
    ) -> None:
        """
        Adds person to household and assigns them the correct subgroup.
        """
        if subgroup == "kids":
            household.add(person, household.GroupType.kids)
        elif subgroup == "young_adults":
            household.add(person, household.GroupType.young_adults)
        elif subgroup == "adults":
            household.add(person, household.GroupType.adults)
        elif subgroup == "old":
            household.add(person, household.GroupType.old_adults)
        elif subgroup == "default":
            household.add(person, household.GroupType.adults)
        else:
            raise HouseholdError(f"Subgroup {subgroup} not recognized")

    def _check_if_age_dict_is_empty(self, people_dict: dict, age: int) -> bool:
        """
        Given a people_dict that contains a list of people for each age, it deletes the
        age key if the number of people of that age is 0.

        Parameters
        ----------
        people_dict:
            dictionary with age as keys and list of people of that age as values.
        age:
            age to check if empty.
        """
        if len(people_dict[age]) == 0:
            del people_dict[age]
            return True
        return False

    def _check_if_oldpeople_left(self, area: Area) -> bool:
        """
        Checks whether there are still old people without an allocated household.

        Parameters
        ----------
            area:
                the area to check.
        """
        ret = False
        for age in range(65, 100):
            if age in area.women_by_age or age in area.men_by_age:
                ret = True
                break
        return ret

    def _get_closest_person_of_age(
        self, first_dict: dict, second_dict: dict, age: int, min_age=0, max_age=100
    ) -> Person:
        """
        Tries to find the person with the closest age in first dict inside the min_age and max_age.
        If it fails, it looks into the second_dict. If it fails again it returns None.

        Parameters
        ----------
        first_dict:
            dictionary with lists of people by age as keys. This is the first dictionary to look for a suitable person.
        second_dict:
            dictionary with lists of people by age as keys. This is the second dictionary to look for a suitable person.
        age:
            the target age of the person.
        min_age:
            minimum age the person should have.
        max_age:
            maximum age the person should have.
        """
        if age < min_age or age > max_age:
            return None

        compatible_ages = np.array(list(first_dict.keys()))
        compatible_ages = compatible_ages[
            (min_age <= compatible_ages) & (compatible_ages <= max_age)
        ]
        if len(compatible_ages) == 0:
            compatible_ages = np.array(list(second_dict.keys()))
            compatible_ages = compatible_ages[
                (min_age <= compatible_ages) & (compatible_ages <= max_age)
            ]
            if len(compatible_ages) == 0:
                return None
            first_dict = second_dict
        closest_age = get_closest_element_in_array(compatible_ages, age)
        person = first_dict[closest_age].pop()
        self._check_if_age_dict_is_empty(first_dict, closest_age)
        return person

    def _get_random_person_in_age_bracket(
        self, area: Area, min_age=0, max_age=100
    ) -> Person:
        """
        Returns a random person of random sex within the specified age bracket (inclusive).

        Parameters
        ----------
        area:
            The area to look at.
        min_age:
            The minimum age the person should have.
        max_age:
            The maximum age the person should have.
        """
        sex = self._random_sex_list.pop()
        age = np.random.randint(min_age, max_age + 1)
        if sex == 0:
            person = self._get_closest_person_of_age(
                area.men_by_age, area.women_by_age, age, min_age, max_age
            )
        else:
            person = self._get_closest_person_of_age(
                area.women_by_age, area.men_by_age, age, min_age, max_age
            )
        return person

    def _get_matching_partner(
        self, person: Person, area: Area, under_65=False, over_65=False
    ) -> Person:
        """
        Given a person, it finds a suitable partner with similar age and opposite sex. 
        The age difference is sampled from an observed distribution of age differences 
        in couples in the US and the UK, and it read by __init__. We first try to look
        for a female parent, as it is more common to have a single mother than a single
        father.

        Parameters
        ----------
        person:
            the person instance to find a partner for.
        area:
            the area where to look for a partner.
        under_65:
            whether to restrict the search for a partner under 65 years old.
        over_65:
            whether to restrict the search for a partner over 65 years old.
        """
        sex = int(not person.sex)  # get opposite sex
        sampled_age_difference = self._couples_age_differences_list.pop()
        if under_65:
            target_age = min(person.age - abs(sampled_age_difference), 64)
        else:
            target_age = person.age + sampled_age_difference
        if over_65:
            target_age = max(65, target_age)
        target_age = max(min(self.old_max_age, target_age), 18)
        if sex == 0:
            partner = self._get_closest_person_of_age(
                area.men_by_age,
                area.women_by_age,
                target_age,
                min_age=self.adult_min_age,
            )
            return partner
        else:
            partner = self._get_closest_person_of_age(
                area.women_by_age,
                area.men_by_age,
                target_age,
                min_age=self.adult_min_age,
            )
            return partner

    def _get_matching_parent(self, kid: Person, area: Area) -> Person:
        """
        Given a person under 18 years old (strictly), it finds a matching mother with an age
        difference sampled for the known mother-firstkid age distribution read in the 
        __init__ function.

        Parameters
        ----------
        kid:
            The person to look a parent for.
        area:
            The area in which to look for a parent.
        """
        sampled_age_difference = self._first_kid_parent_age_diff_list.pop()
        target_age = max(
            min(kid.age + sampled_age_difference, self.max_age_to_be_parent),
            self.adult_min_age,
        )
        parent = self._get_closest_person_of_age(
            area.women_by_age,
            area.men_by_age,
            target_age,
            min_age=self.adult_min_age,
            max_age=self.max_age_to_be_parent,
        )
        return parent

    def _get_matching_second_kid(self, parent: Person, area: Area) -> Person:
        """
        Given a parent, it finds a person under 18 years old with an age difference matching
        the distribution of age difference between a mother and their second kid.

        Parameters
        ----------
        parent:
            the parent (usually mother) to match with her second kid.
        area:
            area in which to look for the kid.
        """
        sampled_age_difference = self._second_kid_parent_age_diff_list.pop()
        target_age = min(max(parent.age - sampled_age_difference, 0), self.kid_max_age)
        kid_sex = self._random_sex_list.pop()
        if kid_sex == 0:
            kid = self._get_closest_person_of_age(
                area.men_by_age,
                area.women_by_age,
                target_age,
                min_age=0,
                max_age=self.kid_max_age,
            )
        else:
            kid = self._get_closest_person_of_age(
                area.women_by_age,
                area.men_by_age,
                target_age,
                min_age=0,
                max_age=self.kid_max_age,
            )
        return kid

    def fill_all_student_households(
        self, area: Area, n_students: int, student_houses_number: int
    ) -> None:
        """
        Creates and fills all student households with people in the appropriate age bin (18-25 by default).

        Parameters
        ----------
        area:
            The area in which to create and fill the households.
        n_students:
            Number of students in this area. Found in the NOMIS data.
        student_houses_number:
            Number of student houses in this area.
        """
        if n_students == 0:
            return None
        # students per household
        ratio = max(int(n_students / student_houses_number), 1)
        # get all people in the students age
        # fill students to households
        students_left = n_students
        student_houses = []
        for _ in range(0, student_houses_number):
            household = self._create_household(area)
            student_houses.append(household)
            for _ in range(0, ratio):
                student = self._get_random_person_in_age_bracket(
                    area, min_age=self.student_min_age, max_age=self.student_max_age
                )
                if student is None:
                    raise HouseholdError("Students do not match!")
                self._add_to_household(household, student, subgroup="young_adults")
                students_left -= 1
        assert students_left >= 0
        index = 0
        while students_left:
            household = student_houses[index]
            student = self._get_random_person_in_age_bracket(
                area, min_age=self.student_min_age, max_age=self.student_max_age
            )
            self._add_to_household(household, student, subgroup="young_adults")
            students_left -= 1
            index += 1
            index = index % len(student_houses)

    def fill_oldpeople_households(
        self,
        people_per_household: int,
        n_households: int,
        area: Area,
        extra_people_lists=(),
        max_household_size=np.inf,
    ) -> None:
        """
        Creates and fills households with old people.

        Parameters
        ----------
        area:
            The area in which to create and fill the households.
        n_households:
            Number of households.
        extra_people_lists:
            Tuple of lists where the created households will be added to be used
            later to allocate unallocated people.
        max_household_size:
            The maximum size of the created households.
        """
        for i in range(0, n_households):
            household = self._create_household(
                area, max_household_size=max_household_size
            )
            person = self._get_random_person_in_age_bracket(
                area, min_age=self.old_min_age, max_age=self.old_max_age
            )
            if person is None:
                # no old people left, leave the house and the rest empty and adults can come here later.
                for array in extra_people_lists:
                    array.append(household)
                for _ in range(i + 1, n_households):
                    household = self._create_household(
                        area, max_household_size=max_household_size
                    )
                    for array in extra_people_lists:
                        array.append(household)
                return None
            self._add_to_household(household, person, subgroup="old")
            if people_per_household > 1 and person is not None:
                partner = self._get_matching_partner(person, area, over_65=True)
                # if partner is None:
                #    partner = self._get_matching_partner(person, area, under_65=True)
                if partner is not None:
                    self._add_to_household(household, partner, subgroup="old")
            if household.size < household.max_size:
                for array in extra_people_lists:
                    array.append(household)

    def fill_families_households(
        self,
        n_households: int,
        kids_per_house: int,
        parents_per_house: int,
        old_per_house: int,
        area: Area,
        max_household_size=np.inf,
        extra_people_lists=(),
    ) -> None:
        """
        Creates and fills households with families. The strategy is the following:
            - Put the first kid in the household.
            - Find a parent for the kid based on the age difference between parents and their first kid.
            - Find a partner for the first parent, based on age differences at time of marriage.
            - Add a second kid using the age difference with the mother.
            - Fill an extra old person if necessary for multigenerational families.
        Parameters
        ----------
        area:
            The area in which to create and fill the households.
        n_households:
            Number of households.
        kids_per_house:
            Number of kids (<18) in the house.
        old_per_house:
            Number of old people in the house.
        extra_people_lists:
            Tuple of lists where the created households will be added to be used
            later to allocate unallocated people.
        max_household_size:
            The maximum size of the created households.
        """
        for i in range(0, n_households):
            household = self._create_household(
                area, max_household_size=max_household_size
            )
            first_kid = self._get_random_person_in_age_bracket(
                area, min_age=0, max_age=self.kid_max_age
            )
            if first_kid is None:
                # fill with young adult instead
                first_kid = self._get_random_person_in_age_bracket(
                    area,
                    min_age=self.young_adult_min_age,
                    max_age=self.young_adult_max_age,
                )
                if first_kid is None:
                    for array in extra_people_lists:
                        array.append(household)
                    for _ in range(i + 1, n_households):
                        household = self._create_household(
                            area, max_household_size=max_household_size
                        )
                        for array in extra_people_lists:
                            array.append(household)
                    return None
            self._add_to_household(household, first_kid, subgroup="kids")
            first_parent = self._get_matching_parent(first_kid, area)
            if first_parent is None:
                raise HouseholdError(
                    "Orphan kid. Check household configuration and population."
                )
            self._add_to_household(household, first_parent, subgroup="adults")
            for array in extra_people_lists:
                array.append(household)
            if old_per_house > 0:
                for _ in range(old_per_house):
                    random_old = self._get_random_person_in_age_bracket(
                        area, min_age=self.old_min_age, max_age=self.old_max_age
                    )
                    if random_old is None:
                        break
                    self._add_to_household(household, random_old, subgroup="old")

            if parents_per_house == 2 and first_parent is not None:
                second_parent = self._get_matching_partner(first_parent, area)
                if second_parent is not None:
                    # return None
                    self._add_to_household(household, second_parent, subgroup="adults")

            if kids_per_house == 2:
                second_kid = self._get_matching_second_kid(first_parent, area)
                if second_kid is None:
                    second_kid = self._get_random_person_in_age_bracket(
                        area,
                        min_age=self.young_adult_min_age,
                        max_age=self.young_adult_max_age,
                    )
                if second_kid is not None:
                    self._add_to_household(household, second_kid, subgroup="kids")

    def fill_nokids_households(
        self,
        adults_per_household: int,
        n_households: int,
        area: Area,
        extra_people_lists=(),
        max_household_size=np.inf,
    ) -> None:
        """
        Fils households with one or two adults.

        Parameters
        ----------
        adults_per_household:
            number of adults to fill in the household can be one or two.
        n_households:
            number of households with this configuration
        area:
            the area in which to put the household
        extra_people_lists:
            whether to include the created households in a list for extra people to be put in.
        max_household_size:
            maximum size of the created households.
        """
        for _ in range(0, n_households):
            household = self._create_household(
                area, max_household_size=max_household_size
            )
            if self._check_if_oldpeople_left(area):
                # if there are old people left, then put them here together with another adult.
                first_adult = self._get_random_person_in_age_bracket(
                    area, min_age=self.old_min_age, max_age=self.old_max_age
                )
                if first_adult is None:
                    raise HouseholdError("But you said there were old people left!")
            else:
                first_adult = self._get_random_person_in_age_bracket(
                    area, min_age=self.adult_min_age, max_age=self.adult_max_age
                )
            # first_adult = self._get_random_person_in_age_bracket(
            #    area, min_age=self.adult_min_age, max_age=self.adult_max_age
            # )
            if first_adult is not None:
                self._add_to_household(household, first_adult, subgroup="adults")
            if adults_per_household == 1:
                if household.size < household.max_size:
                    for array in extra_people_lists:
                        array.append(household)
                continue
            # second_adult = self._get_matching_partner(first_adult, area, under_65=True)
            if first_adult is not None:
                second_adult = self._get_matching_partner(first_adult, area)
                if second_adult is not None:
                    self._add_to_household(household, second_adult, subgroup="adults")
            if household.size < household.max_size:
                for array in extra_people_lists:
                    array.append(household)

    def fill_youngadult_households(
        self,
        youngadults_per_household: int,
        n_households: int,
        area: Area,
        extra_people_lists=(),
    ) -> None:
        """
        Fils households with young adults (18 to 35) years old. 

        Parameters
        ----------
        youngadults_per_household:
            number of adults to fill in the household. Can be any positive number.
        n_households:
            number of households with this configuration
        area:
            the area in which to put the household
        extra_people_lists:
            whether to include the created households in a list for extra people to be put in.
        """
        for _ in range(0, n_households):
            household = self._create_household(area)
            for _ in range(youngadults_per_household):
                person = self._get_random_person_in_age_bracket(
                    area,
                    min_age=self.young_adult_min_age,
                    max_age=self.young_adult_max_age,
                )
                if person is not None:
                    self._add_to_household(household, person, subgroup="young_adults")
            for array in extra_people_lists:
                array.append(household)

    def fill_youngadult_with_parents_households(
        self,
        adults_per_household: int,
        n_households: int,
        area: Area,
        extra_people_lists=(),
    ) -> None:
        """
        Fils households with one young adult (18 to 35) and one or two adults. 

        Parameters
        ----------
        youngadults_per_household:
            number of adults to fill in the household. Can be one or two.
        n_households:
            number of households with this configuration
        area:
            the area in which to put the household
        extra_people_lists:
            whether to include the created households in a list for extra people to be put in.
        """
        for _ in range(0, n_households):
            household = self._create_household(area)
            for array in extra_people_lists:
                array.append(household)
            youngadult = self._get_random_person_in_age_bracket(
                area, min_age=self.young_adult_min_age, max_age=self.young_adult_max_age
            )
            if youngadult is not None:
                self._add_to_household(household, youngadult, subgroup="young_adults")
            for _ in range(adults_per_household):
                if youngadult is not None:
                    adult = self._get_random_person_in_age_bracket(
                        area, min_age=youngadult.age + 18, max_age=self.adult_max_age
                    )
                else:
                    adult = self._get_random_person_in_age_bracket(
                        area, min_age=self.adult_min_age, max_age=self.adult_max_age
                    )
                if adult is not None:
                    self._add_to_household(household, adult, subgroup="adults")

    def fill_all_communal_establishments(
        self, n_establishments: int, n_people_in_communal: int, area: Area
    ) -> None:
        """
        Fils all comunnal establishments with the remaining people that have not been allocated somewhere else. 

        Parameters
        ----------
        n_establishments:
            number of communal establishments.
        n_people_in_communal:
            number of people in each communal establishment
        area:
            the area in which to put the household
        """
        ratio = max(int(n_people_in_communal / n_establishments), 1)
        people_left = n_people_in_communal
        communal_houses = []
        no_adults = False
        for _ in range(0, n_establishments):
            for i in range(ratio):
                if i == 0:
                    person = self._get_random_person_in_age_bracket(area, min_age=18)
                    if person is None:
                        no_adults = True
                        break
                    household = self._create_household(area, communal=True)
                    communal_houses.append(household)
                    self._add_to_household(household, person, subgroup="default")
                    people_left -= 1
                else:
                    person = self._get_random_person_in_age_bracket(area)
                    self._add_to_household(household, person, subgroup="default")
                    people_left -= 1
            if no_adults:
                break

        index = 0
        while people_left > 0:
            person = self._get_random_person_in_age_bracket(area)
            household = communal_houses[index]
            self._add_to_household(household, person, subgroup="default")
            people_left -= 1
            index += 1
            index = index % len(communal_houses)

    def _remove_household_from_all_lists(self, household, lists: list) -> None:
        """
        Removes the given households from all the lists in lists.

        Parameters
        ----------

        household
            an instance of Household.
        lists
            list of lists of households.
        """
        for lis in lists:
            try:
                lis.remove(household)
            except ValueError:
                pass

    def _check_if_household_is_full(self, household: Household):
        """
        Checks if a household is full or has the maximum household size allowed by the Distributor.

        Parameters
        ----------
        household:
            the household to check.
        """
        size = household.size
        condition = (size >= household.max_size) or (size >= self.max_household_size)
        return condition

    def fill_random_people_to_existing_households(
        self,
        households_with_extra_kids: list,
        households_with_kids: list,
        households_with_extra_youngadults: list,
        households_with_extra_adults: list,
        households_with_extra_oldpeople: list,
        area,
    ) -> None:
        """
        The people that have not been associated a household yet are distributed in the following way.
        Given the lists in the arguments, we assign each age group according to this preferences:
        Kids -> households_with_extra_kids, households_with_kids, any
        Young adults -> households_with_extra_youngadults, households_with_adults, any
        Adults -> households_with_extra_adults, any
        Old people -> households_with_extra_oldpeople, any.
        
        When we allocate someone to any house, we prioritize the houses that have a small
        number of people (less than the max_household_size parameter defined in the __init__)

        Parameters
        ----------
        number_to_fill
            number of remaining people to distribute into spare households.
        households_with_extra_kids
            list of households that take extra kids.
        households_with_kids
            list of households that already have kids. 
        households_with_extra_youngadults
            list of households that take extra young adults.
        households_with_extra_oldpeople
            list of households that take extra old people
        area
            area where households are.
        """
        households_with_space = [
            household
            for household in area.households
            if household.size < household.max_size
        ]
        all_households = households_with_space.copy()
        available_lists = [
            all_households,
            households_with_space,
            households_with_extra_kids,
            households_with_kids,
            households_with_extra_youngadults,
            households_with_extra_adults,
            households_with_extra_oldpeople,
        ]
        available_ages = list(area.men_by_age.keys()) + list(area.women_by_age.keys())
        available_ages = np.sort(np.unique(available_ages))
        people_left_dict = OrderedDict({})
        for age in available_ages:
            people_left_dict[age] = []
            if age in area.men_by_age:
                people_left_dict[age] += area.men_by_age[age]
            if age in area.women_by_age:
                people_left_dict[age] += area.women_by_age[age]
            np.random.shuffle(people_left_dict[age])  # mix men and women

        # fill old people first
        for age in range(self.old_min_age, self.old_max_age + 1):
            if age in people_left_dict:
                for person in people_left_dict[age]:
                    # old with old,
                    # otherwise random
                    household = self._find_household_for_nonkid(
                        [households_with_extra_oldpeople,]
                    )
                    if household is None:
                        household = self._find_household_for_nonkid(
                            [households_with_space, all_households,]
                        )
                    # if household is None:
                    #    household = self._find_household_for_nonkid([area.households])
                    self._add_to_household(household, person, subgroup="old")
                    if self._check_if_household_is_full(household):
                        self._remove_household_from_all_lists(
                            household, available_lists
                        )

        # now young adults
        for age in range(self.young_adult_min_age, self.young_adult_max_age + 1):
            if age in people_left_dict:
                for person in people_left_dict[age]:
                    household = self._find_household_for_nonkid(
                        [households_with_extra_youngadults,]
                    )
                    if household is None:
                        household = self._find_household_for_nonkid(
                            [households_with_space, all_households,]
                        )
                    # if household is None:
                    #    household = self._find_household_for_nonkid([area.households])
                    self._add_to_household(household, person, subgroup="young_adults")
                    if self._check_if_household_is_full(household):
                        self._remove_household_from_all_lists(
                            household, available_lists
                        )
        ## now adults
        for age in range(self.young_adult_max_age + 1, self.adult_max_age + 1):
            if age in people_left_dict:
                for person in people_left_dict[age]:
                    household = self._find_household_for_nonkid(
                        [households_with_extra_adults,]
                    )
                    if household is None:
                        household = self._find_household_for_nonkid(
                            [households_with_space, all_households,]
                        )
                    # if household is None:
                    #    household = self._find_household_for_nonkid([area.households])
                    self._add_to_household(household, person, subgroup="adults")
                    if self._check_if_household_is_full(household):
                        self._remove_household_from_all_lists(
                            household, available_lists
                        )

        ## and lastly, kids
        for age in range(0, self.kid_max_age + 1):
            if age in people_left_dict:
                for person in people_left_dict[age]:
                    household = self._find_household_for_kid(
                        [households_with_extra_kids,]
                    )
                    if household is None:
                        household = self._find_household_for_nonkid(
                            [
                                households_with_kids,
                                # households_with_space,
                                # all_households,
                            ]
                        )
                    if household is None:
                        household = self._find_household_for_nonkid(
                            [households_with_space, all_households]
                        )
                    self._add_to_household(household, person, subgroup="kids")
                    if self._check_if_household_is_full(household):
                        self._remove_household_from_all_lists(
                            household, available_lists
                        )

    def _find_household_for_kid(self, priority_lists):
        """
        Finds a suitable household for a kid. It first tries to search for a place in priority_lists[0],
        then 1, etc.

        Parameters
        ----------
        priority_lists:
            list of lists of households. The list should be sorted according to priority allocation.
        """
        for lis in priority_lists:
            list2 = [household for household in lis if household.size > 0]
            if len(list2) == 0:
                continue
            household = np.random.choice(list2)
            return household

    def _find_household_for_nonkid(self, priority_lists):
        """
        Finds a suitable household for a person over 18 years old (who can live alone).
        It first tries to search for a place in priority_lists[0], then 1, etc.

        Parameters
        ----------
        priority_lists:
            list of lists of households. The list should be sorted according to priority allocation.
        """
        for lis in priority_lists:
            if len(lis) == 0:
                continue
            household = np.random.choice(lis)
            return household