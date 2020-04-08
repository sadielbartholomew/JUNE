class CompnayError(BaseException):
    """Class for throwing company related errors."""
    pass

class School:
    """
    The Company class represents a household and contains information about 
    its workers(19 - 74 years old).
    """

    def __init__(self, school_id, coordinates, n_pupils, age_min, age_max):
        self.id = school_id
        self.pupils= {}
        self.coordinates = coordinates
        #self.residents = group(self.id,"household")
        self.n_pupils_max = n_pupils
        self.n_pupils = 0
        self.age_min = age_min
        self.age_max = age_max

