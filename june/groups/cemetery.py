from june.groups import Group


class Cemetery(Group):
    def __init__(self):
        super().__init__("Cemetery", "cemetery")

    def must_timestep(self):
        return False

    def update_status_lists(self, time=1, delta_time=1):
        pass

    def set_active_members(self):
        pass


class Cemeteries:
    def __init__(self, world):
        self.world = world
        self.members = [Cemetery()]

    def get_nearest(self, person):
        return self.members[0]
