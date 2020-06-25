from june.demography.person import Person
from .abstract import AbstractGroup
from typing import Set, List
from itertools import chain
import numpy as np
from numba import typed


class Subgroup:
    __slots__ = (
        "group",
        "subgroup_type",
        "people",
        # "size",
        # "size_infected",
        # "size_infectors",
        # "size_recovered",
        # "size_susceptible",
        # "infected",
        # "susceptible",
        # "recovered",
        # "transmission_probabilities",
        # "susceptible_ids",
        # "infector_ids",
    )

    def __init__(self, group, subgroup_type: int):
        """
        A group within a group. For example, children in a household.
        """
        self.group = group
        self.subgroup_type = subgroup_type
        # self.infected = []
        # self.susceptible = []
        # self.recovered = []
        # self.transmission_probabilities = np.array([], dtype=np.float)
        # self.susceptible_ids = np.array([], dtype=np.int)
        # self.infector_ids = np.array([], dtype=np.int)
        self.people = []
        # self.size_infected = 0
        # self.size_infectors = 0
        # self.size_recovered = 0
        # self.size_susceptible = 0
        # self.size = 0

    def _collate(self, attribute: str) -> List[Person]:
        return [person for person in self.people if getattr(person, attribute)]
        #collection = list()
        #for person in self.people:
        #    if getattr(person, attribute):
        #        collection.append(person)
        #return collection

    @property
    def dead(self):
        return self._collate("dead")

    @property
    def infected(self):
        return self._collate("infected")

    @property
    def susceptible(self):
        return self._collate("susceptible")

    @property
    def recovered(self):
        return self._collate("recovered")

    @property
    def size(self):
        return len(self.people)

    @property
    def in_hospital(self):
        return self._collate("in_hospital")

    def __contains__(self, item):
        return item in self.people

    def __iter__(self):
        return iter(self.people)

    def __len__(self):
        return len(self.people)

    def clear(self):
        self.people = []
        # self.recovered = []
        # self.size_recovered = 0
        # self.susceptible = []
        # self.size_susceptible = 0
        # self.infected = []
        # self.size_infected = 0
        # self.people = []
        # self.size = 0
        # self.transmission_probabilities = []
        # self.susceptible_ids = []
        # self.infector_ids = []

    @property
    def contains_people(self) -> bool:
        """
        Whether or not the group contains people.
        """
        return len(self.people) > 0

    def append(self, person: Person):
        """
        Add a person to this group
        """
        # if person.infected:
        #    self.infected.append(person)
        #    self.size_infected += 1
        #    tprob = person.health_information.infection.transmission.probability
        #    if tprob > 0:
        #        self.infector_ids.append(person.id)
        #        self.transmission_probabilities.append(tprob)
        #        #np.append(self.infector_ids, person.id)
        #        #np.append(self.transmission_probabilities, tprob)
        #        self.size_infectors += 1
        #    #np.append(self.infector_ids, person.id)
        #    #np.append(
        #    #    self.transmission_probabilities,
        #    #    person.health_information.infection.transmission.probablity,
        #    #)
        # elif person.susceptible:
        #    self.susceptible.append(person)
        #    self.size_susceptible += 1
        #    self.susceptible_ids.append(person.id)
        #    #np.append(self.susceptible_ids, person.id)
        # else:
        #    self.recovered.append(person)
        #    self.size_recovered += 1
        # self.size += 1
        # self.group.size += 1
        self.people.append(person)
        person.busy = True

    def remove(self, person: Person):
        if person.infected:
            self.infected.remove(person)
            self.size_infected -= 1
        elif person.susceptible:
            self.susceptible.remove(person)
            self.size_susceptible -= 1
        else:
            self.recovered.remove(person)
            self.size_recovered -= 1
        self.size -= 1
        self.people.remove(person)
        self.group.size -= 1
        person.busy=False

    def __getitem__(self, item):
        return list(self.people)[item]
