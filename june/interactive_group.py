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
        infector_ids = []
        trans_prob = []
        susceptible_ids = []
        infector_subgroup_sizes = []
        self.subgroups_infector = []
        self.subgroups_susceptible = []
        self.has_susceptible = False
        self.has_infector = False
        for i, subgroup in enumerate(group.subgroups):
            subgroup_size = subgroup.size
            subgroup_infected = subgroup.infected
            sus_ids = [person.id for person in subgroup.people if person.susceptible]
            if len(sus_ids) != 0:
                self.has_susceptible = True
                self.subgroups_susceptible.append(i)
                susceptible_ids.append(np.array(sus_ids))
            inf_ids = [person.id for person in subgroup_infected]
            if len(inf_ids) != 0:
                tprob = sum(
                        person.health_information.infection.transmission.probability
                        for person in subgroup_infected 
                )
                if tprob != 0.0:
                    self.has_infector = True
                    self.subgroups_infector.append(i)
                    trans_prob.append(tprob)
                    infector_ids.append(np.array(inf_ids))
                    infector_subgroup_sizes.append(subgroup_size)
        
        self.must_timestep = self.has_susceptible and self.has_infector 
        if self.must_timestep is False:
            self.spec = None
            self.infector_ids = None
            self.transmission_probabilities = None
            self.susceptible_ids = None
            self.infector_subgroup_sizes = None
            self.size = None
            self.school_years = None
            return 
        self.spec = group.spec
        self.infector_ids = np.array(infector_ids)
        self.transmission_probabilities = np.array(trans_prob)
        self.susceptible_ids = np.array(susceptible_ids)
        self.subgroups_susceptible = tuple(self.subgroups_susceptible)
        self.subgroups_infector = tuple(self.subgroups_infector)
        self.infector_subgroup_sizes = tuple(infector_subgroup_sizes)
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
