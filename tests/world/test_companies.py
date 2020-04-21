from collections import Counter
from covid.world import World
import pandas as pd
from covid.inputs import Inputs
import seaborn as sns
import pickle

sns.set_context("paper")


def test_number_companies():
    """ 
    Check the number of companies in the world is correct
    """
    world = World.from_pickle()
    inputs = Inputs()
    assert len(world.schools.members) == len(inputs.school_df)


def test_all_kids_school():
    """
    Check that all kids in ages between 5 and 17 are assigned a school 
    """
    world = World.from_pickle()
    KIDS_LOW = 5
    KIDS_UP = 17
    lost_kids = 0
    for i in range(len(world.areas.members)):
        for j in range(len(world.areas.members[i].people)):
            if (world.areas.members[i].people[j].age >= KIDS_LOW) and (
                world.areas.members[i].people[j].age <= KIDS_UP
            ):
                if world.areas.members[i].people[j].school is None:
                    lost_kids += 1

    assert lost_kids == 0
