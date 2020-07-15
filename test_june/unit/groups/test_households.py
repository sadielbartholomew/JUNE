import pandas as pd
import pytest
from june.groups.household import Household, HouseholdSingle #Households
from june.demography import Person

class TestHousehold:
    def test__add_leisure(self):
        household = Household(n_kids=1, n_young_adults=2, n_adults=3, n_old_adults=4)
        assert household.n_kids == 1
        assert household.n_young_adults == 2
        assert household.n_adults == 3
        assert household.n_old_adults == 4
        p = Person.from_attributes(sex="f", age=8)
        household.add(p, activity="leisure")
        assert p not in household.residents
        assert p in household.kids
        p = Person.from_attributes(sex="f", age=18)
        household.add(p, activity="leisure")
        assert p in household.young_adults
        assert p not in household.residents
        p = Person.from_attributes(sex="f", age=48)
        household.add(p, activity="leisure")
        assert p in household.adults
        assert p not in household.residents
        p = Person.from_attributes(sex="f", age=78)
        household.add(p, activity="leisure")
        assert p in household.old_adults
        assert p not in household.residents
        assert household.size == 4

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
        household = HouseholdSingle(area="test", n_young_adults=1)
        assert household.area == "test"
        assert household.n_young_adults == 1
        household = HouseholdSingle(area="test", n_adults=1)
        assert household.area == "test"
        assert household.n_adults == 1
        household = HouseholdSingle(area="test", n_old_adults=1)
        assert household.area == "test"
        assert household.n_old_adults == 1
        household = HouseholdSingle(area="test", n_old_adults=1, n_adults=1)
        assert household.area == "test"
        assert household.n_old_adults == 1
