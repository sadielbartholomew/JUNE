import numpy as np
import pandas as pd
from scipy import spatial
import matplotlib.pyplot as plt


class CommuteHub:
    """
    Defines hubs around cities through with people commute and assigns people to those commute hubs
    """

    def __init__(self, commutehub_id, lat_lon, city):
        """
        id: (int) id of the commute hub
        lat_lon: (array) lat/lon of the commute hub
        city: (string) name of the city the commute hub is associated to
        passengers: (list) passengers commuting through this commute hub
        commuteunits: (list) commute units associated with the commute hub
        """
        self.id = commutehub_id
        self.lat_lon = lat_lon
        self.city = city # station the hub is affiliated to
        self.passengers = [] # passengers flowing through commute hub
        self.commuteunits = []

class CommuteHubs:
    """
    Initialises commute hubs given the location of the commute cities they are affiliated to

    Assumptions:
    - Each non-London station has 4 commute hubs associated with it
      (this is based on the Network Rail maps showing most major stations have 4 incoming lines)
    - London has 8 commmute hubs associated with it
    - The locations of the hubs are uniformly distibuted around a circle
      (this means we may not exactly account for the correct mixing as we draw from different locations
       the real stations, but we believe this gives a good approximation at the sub-regional level)
    """

    def __init__(self, commutecities, msoa_coordinates, init = False):
        """
        commutecities: (list) members of CommuteCities
        msoa_coordinates (pd.Dataframe) Dataframe containing all MSOA names and their coordinates
        init: (bool) if True, initialise hubs, if False do this manually
        members: (list) list of all commute hubs
        """
        self.commutecities = commutecities
        self.msoa_coordinates = msoa_coordinates
        self.init = init
        self.members = []

        # initialise commute hubs
        if self.init:
            self.init_hubs()

    def _get_msoa_lat_lon(self, msoa):
        'Given an MSOA, get the lat/lon'

        msoa_lat = float(self.msoa_coordinates['Y'][self.msoa_coordinates['MSOA11CD'] == msoa])
        msoa_lon = float(self.msoa_coordinates['X'][self.msoa_coordinates['MSOA11CD'] == msoa])

        return [msoa_lat, msoa_lon]
            
    def init_hubs(self):
        'Initialise all hubs'
        
        ids = 0
        for commutecity in self.commutecities:
            metro_centroid = commutecity.metro_centroid
            metro_msoas = commutecity.metro_msoas
            metro_msoas_lat_lon = []

            # get lat/lon of all metropolitan msoas
            for msoa in metro_msoas:
                metro_msoas_lat_lon.append(self._get_msoa_lat_lon(msoa))

            # find the distance between the metropolitan centriod and all associates metropolitan msoas
            distances = spatial.KDTree(metro_msoas_lat_lon).query(metro_centroid,len(metro_msoas_lat_lon))[0]
            # get distance from metropolitan centroid to furthest away metropolitan msoa
            distance_max = np.max(distances)

            # add fixed offset of 0.005
            distance_away = distance_max + 0.005

            # handle London separately
            # give London 8 hubs
            if commutecity.city == 'London':
                # for now give London 4 hubs, but correct this later

                hubs = np.zeros(4*2).reshape(4,2)
                hubs[:,0] = metro_centroid[0]
                hubs[:,1] = metro_centroid[1]

                hubs[0][1] += distance_away
                hubs[1][1] -= distance_away
                hubs[2][0] += distance_away
                hubs[3][0] -= distance_away
                
            # give non-London stations 4 hubs
            else:
                hubs = np.zeros(4*2).reshape(4,2)
                hubs[:,0] = metro_centroid[0]
                hubs[:,1] = metro_centroid[1]

                hubs[0][1] += distance_away
                hubs[1][1] -= distance_away
                hubs[2][0] += distance_away
                hubs[3][0] -= distance_away

            # loop through all hubs to initialise and append to member and assign to commutecity too
            for hub in hubs:
                commute_hub = CommuteHub(
                    commutehub_id = ids,
                    lat_lon = hub,
                    city = commutecity.city
                )

                ids += 1

                commutecity.commutehubs.append(hub)
                
                self.members.append(commute_hub)
            
