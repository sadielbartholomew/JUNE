from covid.infection import Infection
from covid.groups import Group 
import numpy as np
import sys
import random

class Single_Interaction:
    def __init__(self,group,mode):
        self.mode = mode
        if not isinstance(group, Group):
            print ("Error in Interaction.__init__, no group:",group)
            return
        self.group = group
        
    def single_time_step(self,time,infection_selector):
        if (self.group.size_infected() == 0 or self.group.size_susceptible() == 0): 
            return
        transmission_probability = 0.
        if self.mode=="Superposition":
            transmission_probability = self.added_transmission_probability(time)
        elif self.mode=="Probabilistic":
            transmission_probability = self.combined_transmission_probability(time)
        for recipient in self.group.get_susceptible():
            susceptibility        = recipient.get_susceptibility()
            recipient_probability = susceptibility
            if recipient_probability>0.:
                if random.random() <= transmission_probability * recipient_probability:
                    recipient.set_infection(infection_selector.make_infection(recipient, time))
                
    def combined_transmission_probability(self, time):
        prob_notransmission   = 1.
        interaction_intensity = self.group.get_intensity()/self.group.size()
        for person in self.group.get_infected():
            prob_notransmission *= (1.-person.transmission_probability(time)*interaction_intensity)
        return 1.-prob_notransmission

    def added_transmission_probability(self, time):
        prob_transmission     = 0.
        interaction_intensity = self.group.get_intensity()/self.group.size()
        for person in self.group.get_infected():
            prob_transmission += person.transmission_probability(time)
        return prob_transmission*interaction_intensity

    def set_group(self,group):
        self.group = group
    
    def group(self):
        return self.group
    
class Interaction:
    def __init__(self,groups,time,mode="Probabilistic"):
        self.groups = groups
        self.time   = time
        self.mode   = mode
        for group in self.groups:
            group.update_status_lists(time)

    def single_time_step(self,time,infection_selector):
        for group in self.groups:
            interaction = Single_Interaction(group,self.mode)
            interaction.single_time_step(time,infection_selector)
