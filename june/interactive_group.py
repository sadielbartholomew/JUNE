import numpy as np
import numba as nb

class InteractiveGroup:
    def __init__(self, group):
        infector_ids = []
        trans_prob = []
        susceptible_ids = []
        infector_subgroup_sizes = []
        self.has_susceptible = False
        self.has_infected = False
        for subgroup in group.subgroups:
            subgroup_size = subgroup.size
            subgroup_infected = subgroup.infected
            sus_ids = [person.id for person in subgroup.people if person.susceptible]
            if len(sus_ids) != 0:
                self.has_susceptible = True
                susceptible_ids.append(np.array(sus_ids))
            inf_ids = [person.id for person in subgroup_infected]
            if len(inf_ids) != 0:
                tprob = sum(
                        person.health_information.infection.transmission.probability
                        for person in subgroup_infected 
                )
                if tprob != 0.0:
                    self.has_infected = True
                    trans_prob.append(tprob)
                    infector_ids.append(np.array(inf_ids))
                    infector_subgroup_sizes.append(subgroup_size)
        
        self.must_timestep = self.has_susceptible and self.has_infected 
        if self.must_timestep is False:
            return 
        self.spec = group.spec
        self.infector_ids = np.array(infector_ids)
        self.transmission_probabilities = np.array(trans_prob)
        self.susceptible_ids = np.array(susceptible_ids)
        self.infector_subgroup_sizes = tuple(infector_subgroup_sizes)
        self.size = group.size
        if self.spec == "school":
            self.school_years = group.years
        else:
            self.school_years = None

