import logging
import datetime
import numpy as np
import pickle
import yaml
from itertools import chain
from typing import Optional, List
from pathlib import Path

from june import paths
from june.activity import ActivityManager, activity_hierarchy
from june.demography import Person, Activities
from june.exc import SimulatorError
from june.groups.leisure import Leisure
from june.infection.symptom_tag import SymptomTag
from june.infection import InfectionSelector
from june.infection_seed import InfectionSeed
from june.interaction import Interaction, InteractiveGroup
from june.logger.logger import Logger
from june.policy import Policies, MedicalCarePolicies, InteractionPolicies
from june.time import Timer
from june.world import World

default_config_filename = paths.configs_path / "config_example.yaml"

logger = logging.getLogger(__name__)


class Simulator:
    ActivityManager = ActivityManager

    def __init__(
        self,
        world: World,
        interaction: Interaction,
        timer: Timer,
        activity_manager: ActivityManager,
        infection_selector: InfectionSelector = None,
        infection_seed: Optional["InfectionSeed"] = None,
        save_path: str = "results",
        checkpoint_dates: List[datetime.date] = None,
        light_logger: bool = False,
    ):
        """
        Class to run an epidemic spread simulation on the world.

        Parameters
        ----------
        world: 
            instance of World class
        save_path:
            path to save logger results
        """
        self.activity_manager = activity_manager
        self.world = world
        self.interaction = interaction
        self.infection_selector = infection_selector
        self.infection_seed = infection_seed
        self.light_logger = light_logger
        self.timer = timer
        if checkpoint_dates is None:
            self.checkpoint_dates = ()
        else:
            self.checkpoint_dates = checkpoint_dates
        self.sort_people_world()
        if save_path is not None:
            self.save_path = Path(save_path)
            self.save_path.mkdir(exist_ok=True, parents=True)
        if not self.world.box_mode and save_path is not None:
            self.logger = Logger(save_path=self.save_path)
        else:
            self.logger = None

    @classmethod
    def from_file(
        cls,
        world: World,
        interaction: Interaction,
        infection_selector=None,
        policies: Optional[Policies] = None,
        infection_seed: Optional[InfectionSeed] = None,
        leisure: Optional[Leisure] = None,
        config_filename: str = default_config_filename,
        save_path: str = "results",
    ) -> "Simulator":

        """
        Load config for simulator from world.yaml

        Parameters
        ----------
        save_path
        leisure
        infection_seed
        policies
        interaction
        world
        config_filename
            The path to the world yaml configuration

        Returns
        -------
        A Simulator
        """
        with open(config_filename) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        if world.box_mode:
            activity_to_groups = None
        else:
            activity_to_groups = config["activity_to_groups"]
        time_config = config["time"]
        if "checkpoint_dates" in config:
            if isinstance(config["checkpoint_dates"], datetime.date):
                checkpoint_dates = [config["checkpoint_dates"]]
            else:
                checkpoint_dates = []
                for date_str in config["checkpoint_dates"].split():
                    checkpoint_dates.append(
                        datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    )
        else:
            checkpoint_dates = None
        weekday_activities = [
            activity for activity in time_config["step_activities"]["weekday"].values()
        ]
        weekend_activities = [
            activity for activity in time_config["step_activities"]["weekend"].values()
        ]
        all_activities = set(
            chain.from_iterable(weekday_activities + weekend_activities))

        cls.check_inputs(time_config)

        timer = Timer(
            initial_day=time_config["initial_day"],
            total_days=time_config["total_days"],
            weekday_step_duration=time_config["step_duration"]["weekday"],
            weekend_step_duration=time_config["step_duration"]["weekend"],
            weekday_activities=time_config["step_activities"]["weekday"],
            weekend_activities=time_config["step_activities"]["weekend"],
        )

        activity_manager = cls.ActivityManager(
            world=world,
            all_activities=all_activities,
            activity_to_groups=activity_to_groups,
            leisure=leisure,
            policies=policies,
            timer=timer,
        )
        return cls(
            world=world,
            activity_manager=activity_manager,
            timer=timer,
            infection_selector=infection_selector,
            infection_seed=infection_seed,
            save_path=save_path,
            interaction=interaction,
            checkpoint_dates=checkpoint_dates,
        )

    @classmethod
    def from_checkpoint(
        cls,
        world: World,
        checkpoint_path: str,
        interaction: Interaction,
        infection_selector: Optional[InfectionSelector] = None,
        policies: Optional[Policies] = None,
        infection_seed: Optional[InfectionSeed] = None,
        leisure: Optional[Leisure] = None,
        config_filename: str = default_config_filename,
        save_path: str = "results",
    ):
        """
        Initializes the simulator from a saved checkpoint. The arguments are the same as the standard .from_file()
        initialisation but with the additional path to where the checkpoint pickle file is located.
        The checkpoint saves information about the infection status of all the people in the world as well as the timings.
        Note, nonetheless, that all the past infections / deaths will have the checkpoint date as date.
        """
        simulator = cls.from_file(
            world=world,
            interaction=interaction,
            infection_selector=infection_selector,
            policies=policies,
            infection_seed=infection_seed,
            leisure=leisure,
            config_filename=config_filename,
            save_path=save_path,
        )
        with open(checkpoint_path, "rb") as f:
            checkpoint_data = pickle.load(f)
        first_person_id = simulator.world.people[0].id
        for dead_id in checkpoint_data["dead_ids"]:
            person = simulator.world.people[dead_id - first_person_id]
            person.dead = True
            person.susceptibility = 0.0
            cemetery = world.cemeteries.get_nearest(person)
            cemetery.add(person)
            person.subgroups = Activities(None, None, None, None, None, None, None)
        for recovered_id in checkpoint_data["recovered_ids"]:
            person = simulator.world.people[recovered_id - first_person_id]
            person.susceptibility = 0.0
        for infected_id, health_information in zip(
            checkpoint_data["infected_ids"], checkpoint_data["health_information_list"]
        ):
            person = simulator.world.people[infected_id - first_person_id]
            person.health_information = health_information
            person.susceptibility = 0.0
        # restore timer
        checkpoint_timer = checkpoint_data["timer"]
        simulator.timer.initial_date = checkpoint_timer.initial_date
        simulator.timer.date = checkpoint_timer.date
        simulator.timer.delta_time = checkpoint_timer.delta_time
        simulator.timer.shift = checkpoint_timer.shift
        return simulator

    def sort_people_world(self):
        """
        Sorts world population by id so it is easier to find them later.
        """
        people_ids = np.array([person.id for person in self.world.people])
        ids_sorted_idx = np.argsort(people_ids)
        self.world.people.people = np.array(self.world.people)[ids_sorted_idx]

    def clear_world(self):
        """
        Removes everyone from all possible groups, and sets everyone's busy attribute
        to False.
        """
        for group_name in self.activity_manager.all_groups:
            if group_name in ["care_home_visits", "household_visits"]:
                continue
            grouptype = getattr(self.world, group_name)
            if grouptype is not None:
                for group in grouptype.members:
                    group.clear()

        for person in self.world.people.members:
            person.busy = False
            person.subgroups.leisure = None

    @staticmethod
    def check_inputs(time_config: dict):
        """
        Check that the iput time configuration is correct, i.e., activities are among allowed activities
        and days have 24 hours.

        Parameters
        ----------
        time_config:
            dictionary with time steps configuration
        """

        try:
            assert sum(time_config["step_duration"]["weekday"].values()) == 24
            assert sum(time_config["step_duration"]["weekend"].values()) == 24
        except AssertionError:
            raise SimulatorError("Daily activity durations in config do not add to 24 hours.")

        # Check that all groups given in time_config file are in the valid group hierarchy
        all_groups = activity_hierarchy
        try:
            for step, activities in time_config["step_activities"]["weekday"].items():
                assert all(group in all_groups for group in activities)

            for step, activities in time_config["step_activities"]["weekend"].items():
                assert all(group in all_groups for group in activities)
        except AssertionError:
            raise SimulatorError("Config file contains unsupported activity name.")

    @staticmethod
    def bury_the_dead(world: World, person: "Person", time: float):
        """
        When someone dies, send them to cemetery. 
        ZOMBIE ALERT!! 

        Parameters
        ----------
        time
        person:
            person to send to cemetery
        """
        person.dead = True
        person.susceptibility = 0.0
        cemetery = world.cemeteries.get_nearest(person)
        cemetery.add(person)
        person.health_information.set_dead(time)
        person.subgroups = Activities(None, None, None, None, None, None, None)

    @staticmethod
    def recover(person: "Person", time: float):
        """
        When someone recovers, erase the health information they carry and change their susceptibility.

        Parameters
        ----------
        person:
            person to recover
        time:
            time (in days), at which the person recovers
        """
        # TODO: seems to be only used to set the infection length at the moment, but this is not logged
        # anywhere, so we could get rid of this potentially
        person.health_information.set_recovered(time)
        person.susceptibility = 0.0
        person.health_information = None

    def update_health_status(self, time: float, duration: float):
        """
        Update symptoms and health status of infected people.
        Send them to hospital if necessary, or bury them if they
        have died.

        Parameters
        ----------
        time:
            time now
        duration:
            duration of time step
        """
        ids = []
        symptoms = []
        n_secondary_infections = []
        medical_care_policies = MedicalCarePolicies.get_active_policies(
            policies=self.activity_manager.policies, date=self.timer.date
        )
        for person in self.world.people.infected:
            health_information = person.health_information
            previous_tag = health_information.tag
            health_information.update_health_status(time, duration)
            if (
                previous_tag == SymptomTag.exposed
                and health_information.tag == SymptomTag.mild
            ):
                person.residence.group.quarantine_starting_date = time
            ids.append(person.id)
            symptoms.append(person.health_information.tag.value)
            n_secondary_infections.append(person.health_information.number_of_infected)
            # Take actions on new symptoms
            medical_care_policies.apply(
                person=person, medical_facilities=self.world.hospitals
            )
            if health_information.recovered:
                self.recover(person, time)
            elif health_information.is_dead:
                self.bury_the_dead(self.world, person, time)
        if self.logger is not None:
            self.logger.log_infected(
                self.timer.date, ids, symptoms, n_secondary_infections
            )

    def do_timestep(self):
        """
        Perform a time step in the simulation. First, ActivityManager is called
        to send people to the corresponding subgroups according to the current daytime.
        Then we iterate over all the groups and create an InteractiveGroup object, which
        extracts the relevant information of each group to carry the interaction in it.
        We then pass the interactive group to the interaction module, which returns the ids 
        of the people who got infected. We record the infection locations, update the health
        status of the population, and distribute scores among the infectors to calculate R0.
        """
        if self.activity_manager.policies is not None:
            interaction_policies = InteractionPolicies.get_active_policies(
                policies=self.activity_manager.policies, date=self.timer.date
            )
            interaction_policies.apply(
                date=self.timer.date, interaction=self.interaction
            )
        activities = self.timer.activities
        if not activities or len(activities) == 0:
            logger.info("==== do_timestep(): no active groups found. ====")
            return
        self.activity_manager.do_timestep()

        active_groups = self.activity_manager.active_groups
        group_instances = [
            getattr(self.world, group)
            for group in active_groups
            if group not in ["household_visits", "care_home_visits"]
        ]
        n_people = 0

        for cemetery in self.world.cemeteries.members:
            n_people += len(cemetery.people)
        logger.info(
            f"Date = {self.timer.date}, "
            f"number of deaths =  {n_people}, "
            f"number of infected = {len(self.world.people.infected)}"
        )
        infected_ids = []
        first_person_id = self.world.people[0].id
        for group_type in group_instances:
            for group in group_type.members:
                int_group = InteractiveGroup(group)
                n_people += int_group.size
                if int_group.must_timestep:
                    new_infected_ids = self.interaction.time_step_for_group(
                        self.timer.duration, int_group
                    )
                    if new_infected_ids:
                        n_infected = len(new_infected_ids)
                        if self.logger is not None:
                            self.logger.accumulate_infection_location(
                                group.spec, n_infected
                            )
                        # assign blame of infections
                        tprob_norm = sum(int_group.transmission_probabilities)
                        for infector_id in chain.from_iterable(
                                int_group.infector_ids):
                            infector = self.world.people[infector_id - first_person_id]
                            assert infector.id == infector_id
                            infector.health_information.number_of_infected += (
                                n_infected
                                * infector.health_information.infection.transmission.probability
                                / tprob_norm
                            )
                    infected_ids += new_infected_ids
        people_to_infect = [
            self.world.people[idx - first_person_id] for idx in infected_ids
        ]
        if n_people != len(self.world.people):
            raise SimulatorError(
                f"Number of people active {n_people} does not match "
                f"the total people number {len(self.world.people.members)}"
            )
        # infect people
        if self.infection_selector:
            for i, person in enumerate(people_to_infect):
                assert infected_ids[i] == person.id
                self.infection_selector.infect_person_at_time(person, self.timer.now)
        self.update_health_status(time=self.timer.now, duration=self.timer.duration)
        if self.logger:
            self.logger.log_infection_location(self.timer.date)
            if self.world.hospitals is not None:
                self.logger.log_hospital_capacity(self.timer.date, self.world.hospitals)
        self.clear_world()

    def run(self):
        """
        Run simulation with n_seed initial infections
        """
        logger.info(
            f"Starting group_dynamics for {self.timer.total_days} days at day {self.timer.day}"
        )
        logger.info(
            f"starting the loop ..., at {self.timer.day} days, to run for {self.timer.total_days} days"
        )
        self.clear_world()
        if self.logger:
            self.logger.log_population(
                self.world.people, light_logger=self.light_logger
            )

            self.logger.log_parameters(
                interaction=self.interaction,
                infection_seed=self.infection_seed,
                infection_selector=self.infection_selector,
                activity_manager=self.activity_manager,
            )

            if self.world.hospitals is not None:
                self.logger.log_hospital_characteristics(self.world.hospitals)

        while self.timer.date < self.timer.final_date:
            if self.infection_seed:
                if (
                    self.infection_seed.max_date
                    >= self.timer.date
                    >= self.infection_seed.min_date
                ):
                    self.infection_seed.unleash_virus_per_region(self.timer.date)
            self.do_timestep()
            if (
                self.timer.date.date() in self.checkpoint_dates
                and (self.timer.now + self.timer.duration).is_integer() 
            ):# this saves in the last time step of the day
                saving_date = self.timer.date.date()
                next(self.timer) # we want to save at the next time step so that
                # we can resume consistenly
                logger.info(f"Saving simulation checkpoint at {self.timer.date.date()}")
                self.save_checkpoint(saving_date)
                continue
            next(self.timer)

    def save_checkpoint(self, date: datetime):
        """
        Saves a checkpoint at the given date. We save all the health information of the
        population. We can then load the world back to the checkpoint state using the
        from_checkpoint class method of this class.
        """
        recovered_people_ids = [
            person.id for person in self.world.people if person.recovered
        ]
        dead_people_ids = [person.id for person in self.world.people if person.dead]
        susceptible_people_ids = [
            person.id for person in self.world.people if person.susceptible
        ]
        infected_people_ids = []
        health_information_list = []
        for person in self.world.people.infected:
            infected_people_ids.append(person.id)
            health_information_list.append(person.health_information)
        checkpoint_data = {
            "recovered_ids": recovered_people_ids,
            "dead_ids": dead_people_ids,
            "susceptible_ids": susceptible_people_ids,
            "infected_ids": infected_people_ids,
            "health_information_list": health_information_list,
            "timer" : self.timer,
        }
        with open(self.save_path / f"checkpoint_{str(date)}.pkl", "wb") as f:
            pickle.dump(checkpoint_data, f)
