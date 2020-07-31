from enum import IntEnum

import numpy as np
import yaml

from june import paths
from june.infection.health_index import HealthIndexGenerator
from june.infection.health_information import HealthInformation
from june.infection.symptoms import Symptoms
from june.infection.trajectory_maker import TrajectoryMakers
from june.infection.transmission import TransmissionConstant
from june.infection.transmission_xnexp import TransmissionXNExp

default_config_filename = paths.configs_path / "defaults/infection/InfectionXNExp.yaml"
<<<<<<< HEAD
=======
default_trajectories_config_path = (
    paths.configs_path / "defaults/symptoms/trajectories.yaml"
)
>>>>>>> master


class SymptomsType(IntEnum):
    constant = 0
    gaussian = 1
    step = 2
    trajectories = 3


class InfectionSelector:
<<<<<<< HEAD
    def __init__(self, transmission_type: str, health_index_generator=HealthIndexGenerator.from_file(asymptomatic_ratio=0.3)):
=======
    def __init__(
        self,
        transmission_type: str,
        trajectories_config_path: str = default_trajectories_config_path,
        health_index_generator=HealthIndexGenerator.from_file(asymptomatic_ratio=0.3),
    ):
>>>>>>> master
        """
        Selects the type of infection a person is given

        Parameters
        ----------
        transmission_type:
            either constant or xnexp, controls the person's infectiousness profile over time
        asymptomatic_ratio:
            proportion of infected people that are asymptomatic
        """
        self.transmission_type = transmission_type
<<<<<<< HEAD
        self.trajectory_maker = TrajectoryMakers.from_file()
=======
        self.trajectory_maker = TrajectoryMakers.from_file(
            config_path=trajectories_config_path
        )
>>>>>>> master
        self.health_index_generator = health_index_generator

    @classmethod
    def from_file(
        cls,
        config_filename: str = default_config_filename,
<<<<<<< HEAD
        health_index_generator: HealthIndexGenerator = HealthIndexGenerator.from_file(asymptomatic_ratio=0.3)
=======
        trajectories_config_path: str = default_trajectories_config_path,
        health_index_generator: HealthIndexGenerator = HealthIndexGenerator.from_file(
            asymptomatic_ratio=0.3
        ),
>>>>>>> master
    ) -> "InfectionSelector":
        """
        Generate infection selector from default config file
        
        Parameters
        ----------
        asymptomatic_ratio:
            proportion of infected people that are asymptomatic
        config_filename: 
            path to config file 
        """
        with open(config_filename) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
<<<<<<< HEAD
        return InfectionSelector(config["transmission_type"], health_index_generator=health_index_generator)
=======
        return InfectionSelector(
            config["transmission_type"],
            trajectories_config_path=trajectories_config_path,
            health_index_generator=health_index_generator,
        )
>>>>>>> master

    def infect_person_at_time(self, person: "Person", time: float):
        """
        Infects a person at a given time

        Parameters
        ----------
        person:
            person that will be infected
        time:
            time at which infection happens
        """
        infection = self.make_infection(person, time)
        person.health_information = HealthInformation()
        person.health_information.set_infection(infection=infection)

    def make_infection(self, person: "Person", time: float):
        """
        Generates the symptoms and infectiousness of the person being infected

        Parameters
        ----------
        person:
            person that will be infected
        time:
            time at which infection happens
        """

        symptoms = self.select_symptoms(person)
        incubation_period = symptoms.time_exposed()
        transmission = self.select_transmission(
<<<<<<< HEAD
            person=person, incubation_period=incubation_period, max_symptoms_tag=symptoms.max_tag()
=======
            person=person,
            incubation_period=incubation_period,
            max_symptoms_tag=symptoms.max_tag(),
>>>>>>> master
        )
        return Infection(transmission=transmission, symptoms=symptoms, start_time=time)

    def select_transmission(
        self,
        person: "Person",
        incubation_period: float,
        max_symptoms_tag: "SymptomsTag",
    ) -> "Transmission":
        """
        Selects the transmission type specified by the user in the init, 
        and links its parameters to the symptom onset for the person (incubation
        period)

        Parameters
        ----------
        person:
            person that will be infected
        incubation_period:
            time of symptoms onset for person
        """
        if self.transmission_type == "xnexp":
            time_first_infectious = incubation_period - np.random.normal(2.0, 0.5)
            peak_position = (
                incubation_period - np.random.normal(0.7, 0.4) - time_first_infectious
            )
            alpha = 1.5
            n = peak_position / alpha
            return TransmissionXNExp.from_file(
                time_first_infectious=time_first_infectious,
                n=n,
                alpha=alpha,
                max_symptoms=max_symptoms_tag,
            )
        elif self.transmission_type == "constant":
            return TransmissionConstant.from_file()
        else:
            raise NotImplementedError("This transmission type has not been implemented")

    def select_symptoms(self, person: "Person") -> "Symptoms":
        """
        Select the symptoms that a given person has, and how they will evolve
        in the future

        Parameters
        ----------
        person:
            person that will be infected
        """
        health_index = self.health_index_generator(person)
        return Symptoms(health_index=health_index)


class Infection:
    """
    The infection class combines the transmission (infectiousness profile) of the infected
    person, and their symptoms trajectory.
    """

    def __init__(
        self, transmission: "Transmission", symptoms: "Symptoms", start_time: float = -1
    ):
        """
        Parameters
        ----------
        transmission:
            instance of the class that controls the infectiousness profile
        symptoms:
            instance of the class that controls the symptoms' evolution
        start_time:
            time at which the person is infected
        """
        self.start_time = start_time
        self.last_time_updated = start_time
        self.transmission = transmission
        self.symptoms = symptoms
        self.infection_probability = 0.0

    def update_at_time(self, time: float):
        """
        Updates symptoms and infectousness 

        Parameters
        ----------
        time:
            time elapsed from time of infection
        """
        if self.last_time_updated <= time:
            time_from_infection = time - self.start_time
            self.last_time_updated = time
<<<<<<< HEAD
            self.transmission.update_probability_from_delta_time(time_from_infection=time_from_infection)
            self.symptoms.update_severity_from_delta_time(time_from_infection=time_from_infection)
=======
            self.transmission.update_probability_from_delta_time(
                time_from_infection=time_from_infection
            )
            self.symptoms.update_severity_from_delta_time(
                time_from_infection=time_from_infection
            )
>>>>>>> master
            self.infection_probability = self.transmission.probability

    @property
    def still_infected(self):
        return True
