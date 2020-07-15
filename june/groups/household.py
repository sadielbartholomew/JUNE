from enum import IntEnum

from june.groups import Group, Supergroup


class Household(Group):
    __slots__ = (
        "area",
        "kid_max_age",
        "young_adult_max_age",
        "adult_max_age",
        "residents",
        "n_kids",
        "n_young_adults",
        "n_adults",
        "n_old_adults",
    )

    class SubgroupType(IntEnum):
        kids = 0
        young_adults = 1
        adults = 2
        old_adults = 3

    def __init__(
        self,
        area=None,
        n_kids=None,
        n_young_adults=None,
        n_adults=None,
        n_old_adults=None,
    ):
        super().__init__()
        self.area = area
        self.kid_max_age = 17
        self.young_adult_max_age = 34
        self.adult_max_age = 64
        self.residents = ()
        self.n_kids = n_kids
        self.n_young_adults = n_young_adults
        self.n_adults = n_adults
        self.n_old_adults = n_old_adults

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
    def young_adults(self):
        return self.subgroups[self.SubgroupType.young_adults]

    @property
    def adults(self):
        return self.subgroups[self.SubgroupType.adults]

    @property
    def old_adults(self):
        return self.subgroups[self.SubgroupType.old_adults]


class HouseholdSingle(Household):
    def __init__(self, area=None):
        super().__init__(area=area)


class Households(Supergroup):
    def __init__(self):
        pass
