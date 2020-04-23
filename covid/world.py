import os

import numpy as np
import yaml
from tqdm.auto import tqdm  # for a fancy progress bar

from covid.interaction import *
from covid.commute import CommuteGenerator
from covid.groups import *
from covid.infection import *
from covid.inputs import Inputs
from covid.logger import Logger
from covid.time import Timer


class World:
    """
    Stores global information about the simulation
    """

    def __init__(self, config_file=None, box_mode=False):
        print("Initializing world...")
        self.read_config(config_file)
        relevant_groups = self.get_simulation_groups()
        self.read_defaults()
        self.box_mode = box_mode
        self.timer = Timer(self.config["time"])
        self.people = []
        self.total_people = 0
        print("Reading inputs...")
        self.inputs = Inputs(zone=self.config["world"]["zone"])
        if box_mode:
            box = Box()
            N_people = self.inputs.n_residents.values.sum()
            for i in range(0, N_people):
                person = Person(self, i, None, None, None, None, None, None, 0)
                box.people.append(person)
            self.boxes = Boxes()
            self.boxes.members = [box]
            self.people = People(self)
            self.people.members = box.people
        else:
            print("Initializing commute generator...")
            #self.commute_generator = CommuteGenerator.from_file(
            #    self.inputs.commute_generator_path
            #)
            print("Initializing areas...")
            self.areas = Areas(self)
            areas_distributor = AreaDistributor(self.areas, self.inputs)
            areas_distributor.read_areas_census()
            print("Initializing MSOAreas...")
            self.msoareas = MSOAreas(self)
            msoareas_distributor = MSOAreaDistributor(self.msoareas)
            msoareas_distributor.read_msoareas_census()
            print("Initializing people...")
            self.people = People(self)
            pbar = tqdm(total=len(self.areas.members))
            for area in self.areas.members:
                # get msoa flow data for this oa area
                wf_area_df = self.inputs.workflow_df.loc[(area.msoarea,)]
                person_distributor = PersonDistributor(
                    self.timer,
                    self.people,
                    area,
                    self.msoareas,
                    self.inputs.companysector_by_sex_dict,
                    self.inputs.companysector_by_sex_df,
                    wf_area_df,
                    self.inputs.companysector_specific_by_sex_df,
                )
                person_distributor.populate_area()
                pbar.update(1)
            pbar.close()
            print("Initializing households...")
            pbar = tqdm(total=len(self.areas.members))
            self.households = Households(self)
            for area in self.areas.members:
                household_distributor = HouseholdDistributor(self, area)
                household_distributor.distribute_people_to_household()
                pbar.update(1)
            pbar.close()
            print(relevant_groups)
            if "schools" in relevant_groups:
                print("Initializing schools...")
                self.schools = Schools(self, self.areas, self.inputs.school_df)
                pbar = tqdm(total=len(self.areas.members))
                for area in self.areas.members:
                   self.distributor = SchoolDistributor(self.schools, area)
                   self.distributor.distribute_kids_to_school()
                   pbar.update(1)
                pbar.close()
            else:
                print("schools not needed, skipping...")

            if "companies" in relevant_groups:
                print("Initializing Companies...")
                self.companies = Companies(self)
                pbar = tqdm(total=len(self.msoareas.members))
                for area in self.msoareas.members:
                   self.distributor = CompanyDistributor(self.companies, area)
                   self.distributor.distribute_adults_to_companies()
                   pbar.update(1)
                pbar.close()
            else:
                print("companies not needed, skipping...")
        self.interaction = self.initialize_interaction()
        self.logger = Logger(self, self.config["logger"]["save_path"], box_mode=box_mode)
        print("Done.")

    def to_pickle(self, pickle_obj=os.path.join("..", "data", "world.pkl")):
        """
        Write the world to file. Comes in handy when setting up the world
        takes a long time.
        """
        import pickle

        with open(pickle_obj, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def from_pickle(cls, pickle_obj="/cosma7/data/dp004/dc-quer1/world.pkl"):
        """
        Initializes a world instance from an already populated world.
        """
        import pickle

        with open(pickle_obj, "rb") as f:
            world = pickle.load(f)
        return world

    @classmethod
    def from_config(cls, config_file):
        return cls(config_file)

    def read_config(self, config_file):
        if config_file is None:
            config_file = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "..",
                "configs",
                "config_example.yaml",
            )
        with open(config_file, "r") as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

    def get_simulation_groups(self):
        # only initialize relevant groups
        timesteps_config = self.config["time"]["step_active_groups"]
        active_groups = []
        for daytype in timesteps_config.keys():
            for i, timestep in timesteps_config[daytype].items():
                for group in timestep:
                    active_groups.append(group)
        active_groups = np.unique(active_groups)
        return active_groups

    def read_defaults(self):
        default_config_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..",
            "configs",
            "defaults",
            "world.yaml",
        )
        with open(default_config_path, "r") as f:
            default_config = yaml.load(f, Loader=yaml.FullLoader)
        for key in default_config.keys():
            if key not in self.config:
                self.config[key] = default_config[key]

    def initialize_interaction(self):
        interaction_type = self.config["interaction"]["type"]
        if "parameters" in self.config["interaction"]:
            interaction_parameters = self.config["interaction"]["parameters"]
        else:
            interaction_parameters = {}
        interaction_class_name = "Interaction" + interaction_type.capitalize()
        interaction = globals()[interaction_class_name](interaction_parameters, self)
        return interaction

    def set_active_group_to_people(self, active_groups):
        for group_name in active_groups:
            grouptype = getattr(self, group_name)
            for group in grouptype.members:
                group.set_active_members()

    def set_allpeople_free(self):
        for person in self.people.members:
            person.active_group = None

    def initialize_infection(self, person):
        infection_name = self.config["infection"]["type"]
        infection_name = "Infection" + infection_name.capitalize()
        if "parameters" in self.config["infection"]:
            infection_parameters = self.config["infection"]["parameters"]
        else:
            infection_parameters = {}
        infection = globals()[infection_name](
            person, self.timer, self.config, infection_parameters
        )
        return infection

    def seed_infections_group(self, group, n_infections):
        #    print (n_infections,group.people)
        choices = np.random.choice(group.size, n_infections)
        infecter_reference = self.initialize_infection(None)
        for choice in choices:
            infecter_reference.infect(group.people[choice])
        group.update_status_lists()

    def seed_infections_box(self, n_infections):
        choices = np.random.choice(self.people.members, n_infections, replace=False)
        infecter_reference = self.initialize_infection(None)
        for choice in choices:
            infecter_reference.infect(choice)
        self.boxes.members[0].update_status_lists()

    def do_timestep(self, day_iter):
        active_groups = self.timer.active_groups()
        if active_groups == None or len(active_groups) == 0:
            print("==== do_timestep(): no active groups found. ====")
            return
        # update people (where they are according to time)
        self.set_active_group_to_people(active_groups)
        # infect people in groups
        groups_instances = [getattr(self, group) for group in active_groups]
        self.interaction.groups = groups_instances
        self.interaction.time_step()
        self.set_allpeople_free()

    def group_dynamics(self, n_seed=100):
        print(
            "Starting group_dynamics for ",
            self.timer.total_days,
            " days at day",
            self.timer.day,
        )
        assert sum(self.config["time"]["step_duration"]["weekday"].values()) == 24
        # TODO: move to function that checks the config file (types, values, etc...)
        # initialize the interaction class with an infection selector
        if self.box_mode:
            self.seed_infections_box(n_seed)
        else:
            print("Infecting indivuals in their household.")
            for household in self.households.members:
                self.seed_infections_group(household, 1)
        print(
            "starting the loop ..., at ",
            self.timer.day,
            " days, to run for ",
            self.timer.total_days,
            " days",
        )

        while self.timer.day <= self.timer.total_days:
            self.logger.log_timestep(self.timer.day)
            self.do_timestep(self.timer)
            next(self.timer)


if __name__ == "__main__":
    world = World()
    # world = World.from_pickle()
    world.group_dynamics()
