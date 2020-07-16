from enum import IntEnum
import random
from typing import List
import numpy as np

from june.groups import Group, Supergroup
from june.demography import Person


class Household(Group):
    __slots__ = (
        "area",
        "kid_max_age",
        "young_adult_max_age",
        "adult_max_age",
        "residents",
        "max_size",
    )

    class SubgroupType(IntEnum):
        kids = 0
        young_adults = 1
        adults = 2
        old_adults = 3

    def __init__(
        self, area=None, max_size=np.inf,
    ):
        super().__init__()
        self.area = area
        self.kid_max_age = 17
        self.young_adult_max_age = 34
        self.adult_max_age = 64
        self.residents = ()
        self.max_size = max_size

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
    def __init__(self, area=None):
        super().__init__(area=area, max_size=1)


class HouseholdCouple(Household):
    def __init__(self, area=None):
        super().__init__(area=area, max_size=2)


class HouseholdFamily(Household):
    def __init__(self, area=None, n_kids_min=0, max_size=np.inf):
        super().__init__(area=area, max_size=max_size)
        self.n_kids_min = n_kids_min


class HouseholdStudent(Household):
    def __init__(self, area=None, max_size=np.inf):
        super().__init__(area=area, max_size=max_size)


class HouseholdCommunal(Household):
    def __init__(self, area=None, max_size=np.inf):
        super().__init__(area=area, max_size=max_size)


class HouseholdOther(Household):
    def __init__(self, area=None, max_size=np.inf):
        super().__init__(area=area, max_size=max_size)


class Households(Supergroup):
    def __init__(self, households: List[Household]):
        super().__init__()
        self.members = households

    @classmethod
    def from_household_compositions(household_com
