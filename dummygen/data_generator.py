import ast
import random

import geopandas as gpd
import numpy as np

import osmnx as ox
from mimesis import Person
from shapely.geometry import Point
from shapely.ops import unary_union
from matplotlib import pyplot as plt

from config import settings

DUMMY_SETTINGS = settings.DUMMY
ox.config(use_cache=True, log_console=True)
crs = {"init": 'epsg:4326'}  # lat lon


class DummyDataGenerator:
    bbox = ast.literal_eval(DUMMY_SETTINGS.get('bbox'))
    address = DUMMY_SETTINGS.get('address')
    distance_delta = 0.9

    dummy_person = Person(locale='tr')

    def __init__(self):
        self.recursive_count = DUMMY_SETTINGS.get('recursive_count', 2)
        self.recursive_percent = DUMMY_SETTINGS.get('recursive_percent', 50)
        self.graph = self.get_graph()

        self.points = self.generate_points_along_line()
        self.add_dummy_fields_grouping()

    def get_graph(self, network_type='all_private'):
        """
       Downloads OSM Data and generate random points as pandas DataFrame
       :return:
        """

        if self.bbox:
            G = ox.graph_from_bbox(*self.bbox, network_type=network_type)
        elif self.address:
            G = ox.graph_from_place(self.address, network_type=network_type)
        else:
            raise ValueError('bbox veya adres parametresi doldurulmalıdır')

        return G

    @staticmethod
    def _point_to_df(points: [Point], data=None):
        geom = gpd.points_from_xy([p.x for p in points], [p.y for p in points], crs=crs)
        gdf = gpd.GeoDataFrame(data=data, geometry=geom, crs=crs)

        return gdf

    def generate_points_along_line(self):
        """

        :return:
        """
        nodes, lines = ox.graph_to_gdfs(self.graph)
        points = []

        for _, l in lines.iterrows():
            distances = np.arange(0, l.geometry.length, self.distance_delta)
            for d in distances:
                subpoints = l.geometry.interpolate(d)
                p = {'geometry': subpoints, 'osmid': l.osmid}
                points.append(p)

            # last_point = l.geometry.boundary[1]  # if end point desired
        gdf = gpd.GeoDataFrame(points)

        # filter if osmid is list
        gdf = gdf[gdf['osmid'].apply(lambda x: str(x).isdigit())]

        self.points = gdf

        return gdf

    def generate_random_points(self) -> gpd.GeoDataFrame:
        """
        Downloads OSM Data and generate random points as pandas DataFrame
        :return:
        """

        Gp = ox.project_graph(self.graph)
        count = DUMMY_SETTINGS.get('sample_count', 1000)
        random_points = ox.utils_geo.sample_points(ox.get_undirected(Gp), count)
        # _, lines = ox.graph_to_gdfs(G)  # _ is nodes

        # cleaning
        # lines.drop(columns=['lanes', 'maxspeed', 'bridge', 'junction'], inplace=True)

        return random_points

    def add_dummy_fields_all(self):
        """
        You can add your custom fields
        :return:
        """
        # dummy names
        _len = len(self.points)
        self.points['First Name'] = [self.dummy_person.first_name() for _ in range(_len)]
        self.points['Last Name'] = [self.dummy_person.last_name() for _ in range(_len)]
        self.points['Age'] = [self.dummy_person.age(16, 66) for _ in range(_len)]
        self.points['Quality'] = [random.randint(0, 5) for _ in range(_len)]

    def add_dummy_fields_grouped(self, x):
        x['First Name'] = self.dummy_person.first_name
        x['Last Name'] = self.dummy_person.last_name()

        return x

    def add_dummy_fields_grouping(self, use='osmid'):
        grp = self.points.groupby(use)
        df = grp.apply(self.add_dummy_fields_grouped)

        self.points.merge(df)

    def add_x_step(self):
        """
        Recursive function
        :return:
        """
        raise NotImplementedError
        if self.recursive_percent > 100:
            raise ValueError('Percent cannot exceed 100')

        for _ in range(self.recursive_count):
            new_sample_len = len(self.points) * self.recursive_percent
