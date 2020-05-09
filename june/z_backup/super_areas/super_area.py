import numpy as np
from june.groups.group import Group


class SuperArea(Group):
    """
    Stores information about the MSOA, like the total number of companies, etc.
    The n_companies_* represent the number of companies in a given msoa
    by sector - here we take the nomis definition of sector which gives
    categories such as:
        A: Agriculture, forestry and fishing
        B: Mining and quarrying
        C: Manufacturing
        ...

    This same level of detail is given at the sex-disaggregated level and can
    be used in the Person class in order to distribute jobs to people which
    can be matched up with the businesses at the msoa level.
    """

    def __init__(
        self,
        coordinates,
        areas: list,
        name: str,
        relevant_groups: list
    ):
        """
        """
        super().__init__(name, "super_area")
        self.coordinates = coordinates  # Lon. & Lat
        self.areas = areas              # Output Area
        # collect people
        self.work_people = []
        for relevant_group in relevant_groups:
            setattr(self, relevant_group, [])


class SuperAreas:
    def __init__(self, world):
        self.world = world
        self.members = []
        self.names_in_order = None  # for fast search
