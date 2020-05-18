from typing import List
from june.exc import GroupException


class Supergroup:
    """
    A group containing a collection of groups of the same specification,
    like households, carehomes, etc.
    This class is meant to be used as template to inherit from, and it
    integrates basic functionality like iteration, etc.
    It also includes a method to delete information about people in the
    groups.
    """

    def __init__(self):
        """
        Parameters
        ----------
        references_to_people
            a list of attributes that contain references to people. This is
            used to erase circular information before using pickle.
        """
        self.members = []
        self.group_type = self.__class__.__name__

    def __iter__(self):
        return iter(self.members)

    def __len__(self):
        return len(self.members)

    def __getitem__(self, item):
        return self.members[item]

    @classmethod
    def for_geography(cls):
        raise NotImplementedError(
            "Geography initialization not available for this supergroup."
        )

    @classmethod
    def from_file(cls):
        raise NotImplementedError(
            "From file initialization not available for this supergroup."
        )

    @classmethod
    def for_box_mode(cls):
        raise NotImplementedError("Supergroup not available in box mode")

    def erase_people_from_groups_and_subgroups(self):
        """
        Erases all people from subgroups.
        Erases all subgroup references to group.
        """
        for group in self:
            for subgroup in group.subgroups:
                subgroup._people.clear()
                subgroup.group = None

