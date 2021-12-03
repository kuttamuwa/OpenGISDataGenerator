import ast
from datetime import datetime, timedelta
import os
import random

import geopandas as gpd
import pandas as pd
import numpy as np
import osmnx as ox
from mimesis import Person
from shapely.geometry import Point

from config import settings

DUMMY_SETTINGS = settings.DUMMY
ox.config(use_cache=True, log_console=True)
crs = {"init": 'epsg:4326'}  # lat lon


class DummyDataGenerator:
    bbox = ast.literal_eval(DUMMY_SETTINGS.get('bbox'))
    address = DUMMY_SETTINGS.get('address')
    distance_delta = DUMMY_SETTINGS.get('footstep_distance', 50)  # meters
    avg_speed = 1.4  # pedestrian speed: meter/second

    start_date = pd.to_datetime(DUMMY_SETTINGS.get('start_date', datetime.now()))
    end_date = pd.to_datetime(DUMMY_SETTINGS.get('end_date', datetime.now() + timedelta(hours=10)))
    date_mixing = ast.literal_eval(DUMMY_SETTINGS.get('date_mixing', True))

    dummy_person = Person(locale='tr')

    def __init__(self):
        self.recursive_count = DUMMY_SETTINGS.get('recursive_count', 2)
        self.recursive_percent = DUMMY_SETTINGS.get('recursive_percent', 50)
        self.graph = self.get_graph()

        self.points = None
        # self.add_dummy_fields_grouping()

    def export_points(self):
        """
        Export shapefile
        :return:
        """
        _path = os.path.abspath('./output')
        name = 'noname.shp' if self.address is None else f"{self.address.split(',')[0]}.shp"

        self.points.to_file(f'{_path}/{name}')

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

    def init_routing(self):
        self.graph = ox.speed.add_edge_speeds(self.graph)
        self.graph = ox.speed.add_edge_travel_times(self.graph)

    @staticmethod
    def _point_to_df(points: [Point], data=None):
        geom = gpd.points_from_xy([p.x for p in points], [p.y for p in points], crs=crs)
        gdf = gpd.GeoDataFrame(data=data, geometry=geom, crs=crs)

        return gdf

    @classmethod
    def get_start_date(cls):
        if cls.date_mixing:
            start_date = pd.to_datetime(pd.date_range(cls.start_date, cls.end_date, periods=1)[0])
        else:
            start_date = cls.start_date

        return start_date

    def generate_points_along_line(self):
        """

        :return:
        """
        nodes, lines = ox.graph_to_gdfs(self.graph)
        points = []

        adding_minute = self.distance_delta // self.avg_speed
        start_date = self.get_start_date()

        for _, l in lines.iterrows():

            distances = np.arange(0, l.geometry.length, self.distance_delta)
            for d in distances:
                subpoints = l.geometry.interpolate(d)
                print(f"first start date : {start_date}")
                start_date += timedelta(minutes=adding_minute)
                print(f"sec start date : {start_date}")

                p = {'geometry': subpoints, 'osmid': l.osmid, 'Timestamp': start_date}
                points.append(p)

            start_date = self.get_start_date()

        gdf = gpd.GeoDataFrame(points)

        # filter if osmid is list
        gdf = gdf[gdf['osmid'].apply(lambda x: str(x).isdigit())]
        gdf.drop_duplicates('geometry', inplace=True)

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
        x['First Name'] = self.dummy_person.first_name()
        x['Last Name'] = self.dummy_person.last_name()
        x['Age'] = self.dummy_person.age(16, 66)
        x['Quality'] = random.randint(0, 5)

        return x

    def add_dummy_fields_grouping(self, use='osmid'):
        grp = self.points.groupby(use)
        df = grp.apply(self.add_dummy_fields_grouped)

        self.points = df
