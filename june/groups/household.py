from enum import IntEnum
import random
from typing import List
import numpy as np

from june.groups import Group, Supergroup
from june.demography import Person


class Household(Group):
    __slots__ = (
        "type",
        "area",
        "kid_max_age",
        "young_adult_max_age",
        "adult_max_age",
        "residents",
        "_kids",
        "_young_adults",
        "_adults",
        "_old_adults" "",
    )

    class SubgroupType(IntEnum):
        kids = 0
        young_adults = 1
        adults = 2
        old_adults = 3

    def __init__(
        self, area=None, kids=None, young_adults=None, adults=None, old_adults=None
    ):
        super().__init__()
        self.spec = "household"
        self.type = self.get_spec().split("_")[-1]
        self.area = area
        self.kid_max_age = 17
        self.young_adult_max_age = 34
        self.adult_max_age = 64
        self.residents = ()
        # these are the desired values according to census:
        self._kids = kids
        self._young_adults = young_adults
        self._adults = adults
        self._old_adults = old_adults

    def add(self, person, activity="residence"):
        if person.age <= self.kid_max_age:
            subgroup = self.SubgroupType.kids
        elif person.age <= self.young_adult_max_age:
            subgroup = self.SubgroupType.young_adults
        elif person.age <= self.adult_max_age:
            subgroup = self.SubgroupType.adults
        else:
            subgroup = self.SubgroupType.old_adults
        self[subgroup].append(person)
        if activity == "leisure":
            person.subgroups.leisure = self[subgroup]
        elif activity == "residence":
            person.subgroups.residence = self[subgroup]
            self.residents = tuple((*self.residents, person))
        else:
            raise ValueError("activity not supported")

    def get_leisure_subgroup(self, person):
        if person.age <= self.kid_max_age:
            return self.subgroups[self.SubgroupType.kids]
        elif person.age <= self.young_adult_max_age:
            return self.subgroups[self.SubgroupType.young_adults]
        elif person.age <= self.adult_max_age:
            return self.subgroups[self.SubgroupType.adults]
        else:
            return self.subgroups[self.SubgroupType.old_adults]

    @property
    def max_size(self):
        attr_names = ["_kids", "_young_adults", "_adults", "_old_adults"]
        return sum(
            [
                getattr(self, name)
                for name in attr_names
                if getattr(self, name) is not None
            ]
        )

    @property
    def kids(self):
        return self.subgroups[self.SubgroupType.kids]

    @property
    def n_kids(self):
        return len(self.kids)

    @property
    def young_adults(self):
        return self.subgroups[self.SubgroupType.young_adults]

    @property
    def n_young_adults(self):
        return len(self.young_adults)

    @property
    def adults(self):
        return self.subgroups[self.SubgroupType.adults]

    @property
    def n_adults(self):
        return len(self.adults)

    @property
    def old_adults(self):
        return self.subgroups[self.SubgroupType.old_adults]

    @property
    def n_old_adults(self):
        return len(self.old_adults)


class HouseholdSingle(Household):
    def __init__(
        self, area=None, kids=None, young_adults=None, adults=None, old_adults=None
    ):
        super().__init__(
            area=area,
            kids=kids,
            young_adults=young_adults,
            adults=adults,
            old_adults=old_adults,
        )


class HouseholdCouple(Household):
    def __init__(
        self, area=None, kids=None, young_adults=None, adults=None, old_adults=None
    ):
        super().__init__(
            area=area,
            kids=kids,
            young_adults=young_adults,
            adults=adults,
            old_adults=old_adults,
        )


class HouseholdFamily(Household):
    def __init__(
        self, area=None, kids=None, young_adults=None, adults=None, old_adults=None
    ):
        super().__init__(
            area=area,
            kids=kids,
            young_adults=young_adults,
            adults=adults,
            old_adults=old_adults,
        )


class HouseholdStudent(Household):
    def __init__(
        self, area=None, kids=None, young_adults=None, adults=None, old_adults=None
    ):
        super().__init__(
            area=area,
            kids=kids,
            young_adults=young_adults,
            adults=adults,
            old_adults=old_adults,
        )


class HouseholdCommunal(Household):
    def __init__(
        self, area=None, kids=None, young_adults=None, adults=None, old_adults=None
    ):
        super().__init__(
            area=area,
            kids=kids,
            young_adults=young_adults,
            adults=adults,
            old_adults=old_adults,
        )


class HouseholdOther(Household):
    def __init__(
        self, area=None, kids=None, young_adults=None, adults=None, old_adults=None
    ):
        super().__init__(
            area=area,
            kids=kids,
            young_adults=young_adults,
            adults=adults,
            old_adults=old_adults,
        )


class Households(Supergroup):
    def __init__(self, households: List[Household]):
        super().__init__()


#        self.members = households

# @classmethod
# def from_household_compositions(household_com
