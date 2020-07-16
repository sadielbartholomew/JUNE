import pandas as pd
import pytest
import numpy as np
from june.demography.geography import Area
from june.groups.household import (
    Household,
    HouseholdSingle,
    HouseholdCouple,
    HouseholdFamily,
    HouseholdStudent,
    HouseholdCommunal,
)  # Households
from june.demography import Person


class TestHousehold:
    def test__add_leisure(self):
        household = Household()
        p = Person.from_attributes(sex="f", age=8)
        household.add(p, activity="leisure")
        assert p not in household.residents
        assert p in household.kids
        assert household.n_kids == 1
        p = Person.from_attributes(sex="f", age=18)
        household.add(p, activity="leisure")
        assert p in household.young_adults
        assert p not in household.residents
        assert household.n_young_adults == 1
        p = Person.from_attributes(sex="f", age=48)
        household.add(p, activity="leisure")
        assert p in household.adults
        assert p not in household.residents
        assert household.n_adults == 1
        p = Person.from_attributes(sex="f", age=78)
        household.add(p, activity="leisure")
        assert p in household.old_adults
        assert p not in household.residents
        assert household.size == 4
        assert household.n_old_adults == 1

    def test__add_resident(self):
        household = Household()
        p = Person.from_attributes(sex="f", age=8)
        household.add(p, activity="residence")
        assert p in household.residents
        assert p in household.kids
        p = Person.from_attributes(sex="f", age=18)
        household.add(p, activity="residence")
        assert p in household.young_adults
        assert p in household.residents
        p = Person.from_attributes(sex="f", age=48)
        household.add(p, activity="residence")
        assert p in household.adults
        assert p in household.residents
        p = Person.from_attributes(sex="f", age=78)
        household.add(p, activity="residence")
        assert p in household.old_adults
        assert p in household.residents


class TestHouseholdSingle:
    def test__household_single(self):
        household = HouseholdSingle(area="test")
        assert household.area == "test"


class TestHouseholdSingle:
    def test__household_single(self):
        household = HouseholdSingle(area="test")
        assert household.area == "test"


class TestHouseholdCouple:
    def test__household_couple(self):
        household = HouseholdCouple(old_couple=True)
        assert household.old_couple is True
        household = HouseholdCouple(old_couple=False)
        assert household.old_couple is False


class TestHouseholdFamily:
    def test__household_family(self):
        household = HouseholdFamily(
            n_kids_min=1, single_parent=True, multi_generational=False
        )
        assert household.n_kids_min == 1
        assert household.single_parent is True
        assert household.multi_generational is False


class TestHouseholdStudent:
    def test__household_student(self):
        household = HouseholdStudent()
        assert household.max_size == np.inf


class TestHouseholdCommunal:
    def test__household_student(self):
        household = HouseholdCommunal()
        assert household.max_size == np.inf


class TestHouseholdsCreation:
    def test__households_from_compositions(self):
        compositions = {
            "single": {1: {"old": True, "number": 10}, 2: {"old": False, "number": 5}},
            "couple": {1: {"old": True, "number": 15}, 2: {"old": False, "number": 7}},
            "families": {
                1: {"kids": 1, "young_adults" : 0,  "adults": 1, "old_adults": 0, "number": 5},
                2: {"kids": "2+", "young_adults" : 0, "adults": 2, "old_adults": 0, "number": 4},
                3: {"kids": 1, "young_adults" : 0, "adults": 2, "old_adults": 1, "number": 3},
                4: {"kids": 0, "young_adults" : 2, "adults": 2, "old_adults": 0, "number": 2},
            },
            "students" : {"number" : 10},
            "communal" : {"number" : 3},
            "other" : {"kids": 0, "young_adults" : "2+", "adults": "1+", "old_adults": 1, "number": 2}
        }
        households = Households.from_household_compositions(compositions)
        assert len(households) == 5 + 7 + 5 + 4 + 3 + 2 + 10 + 3 + 2
