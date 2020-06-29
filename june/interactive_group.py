import numpy as np
import numba as nb

class InteractiveGroup:
    """
    Extracts the necessary information about a group to perform an interaction time
    step over it. This step is necessary, since all the information is stored in numpy
    arrays that allow for efficient computation.

    Parameters
    ----------
    - group : group that we want to prepare for interaction.
    """

    def __init__(self, group):
        n_people = len(group.people)
        n_subgroups = len(group.subgroups)
        self.infector_ids = np.nan * np.ones((n_subgroups, n_people))
        self.susceptible_ids = np.nan * np.ones((n_subgroups, n_people))
        self.infector_subgroup_sizes = np.zeros(n_subgroups)
        self.transmission_probabilities = np.zeros(n_subgroups)
        self.has_susceptible = False
        self.has_infected = False
        for i, subgroup in enumerate(group.subgroups):
            subgroup_size = subgroup.size
            subgroup_infected = subgroup.infected
            sus_ids = [person.id for person in subgroup.people if person.susceptible]
            if len(sus_ids) != 0:
                self.has_susceptible = True
                self.susceptible_ids[i][:len(sus_ids)] = sus_ids
            inf_ids = [person.id for person in subgroup_infected]
            if len(inf_ids) != 0:
                tprob = sum(
                    person.health_information.infection.transmission.probability
                    for person in subgroup_infected
                )
                if tprob != 0.0:
                    self.transmission_probabilities[i] = tprob
                    self.infector_ids[i][:len(inf_ids)] = inf_ids
                    self.has_infected = True
                    self.infector_subgroup_sizes[i] = subgroup_size

        self.must_timestep = self.has_susceptible and self.has_infected
        self.spec = group.spec
        self.size = group.size
        if self.spec == "school":
            self.school_years = group.years
        else:
            self.school_years = None


if __name__ == "__main__":
    import time
    from june.groups import Household
    from june.demography import Person

    household = Household()
    i = 0
    for _ in range(0, 10):
        p = Person.from_attributes()
        household.add(p, subgroup_type=i % len(household.subgroups))
    household.clear()
    t1 = time.time()
    for _ in range(300_000):
        interactive_group = InteractiveGroup(household)
    t2 = time.time()
    print(f"took {t2-t1} seconds")
