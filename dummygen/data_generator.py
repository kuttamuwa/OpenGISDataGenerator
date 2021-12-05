import ast
import os
import random
from datetime import datetime, timedelta

import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd
from mimesis import Person
from shapely.geometry import Point

from config import settings
from db.connector import db, points_table_name, lines_table_name, if_exists
from dummygen import export_shp_fiona_schema

DUMMY_SETTINGS = settings.DUMMY
ox.config(use_cache=True, log_console=True)
crs = {"init": 'epsg:3857'}  # x y


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
        # self.recursive_count = DUMMY_SETTINGS.get('recursive_count', 2)
        # self.recursive_percent = DUMMY_SETTINGS.get('recursive_percent', 50)
        self.graph = self.get_graph()

        self.points = None
        self.lines_gdf = None

    def export_points_shapefile(self):
        """
        Export shapefile
        :return:
        """
        _path = os.path.abspath('./output')
        name = 'noname.shp' if self.address is None else f"{self.address.split(',')[0]}.shp"

        self.points.to_file(f'{_path}/{name}', schema=export_shp_fiona_schema)

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

        G = ox.project_graph(G, to_crs=crs['init'])
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
        Generate points along lines and sum up.

        :return:
        """
        lines = ox.graph_to_gdfs(self.graph, nodes=False)
        lines.drop_duplicates('geometry', inplace=True)
        lines['length'] = lines['geometry'].length
        lines = lines[lines['length'] > self.distance_delta]  # minimum value

        points = []
        liness = []

        adding_seconds = self.distance_delta // self.avg_speed
        for _, l in lines.iterrows():
            start_date = self.get_start_date()
            distances = np.arange(0, l.geometry.length, self.distance_delta)
            for d in distances:
                subpoints = l.geometry.interpolate(d)
                start_date += timedelta(seconds=adding_seconds)

                p = {'geometry': subpoints, 'wayid': l.osmid, 'Timestamp': start_date}
                points.append(p)
            liness.append(l)

        gdf = gpd.GeoDataFrame(points, crs=crs['init'])
        # filter if osmid is list
        gdf = gdf[gdf['wayid'].apply(lambda x: str(x).isdigit())]
        gdf.drop_duplicates('geometry', inplace=True)
        gdf.reset_index(inplace=True)
        gdf.rename(columns={'index': 'ROWID'}, inplace=True)

        # lines
        lines_gdf = gpd.GeoDataFrame(lines, crs=crs['init'])
        lines_gdf.drop(columns=[i for i in lines_gdf.columns if i not in ('length', 'geometry', 'osmid')])
        self.lines_gdf = gpd.GeoDataFrame(lines, crs=crs['init'])

        self.points = gdf

        return gdf

    def generate_random_points_in_area(self) -> gpd.GeoDataFrame:
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

    def add_dummy_fields_grouping(self, use='wayid'):
        grp = self.points.groupby(use)
        df = grp.apply(self.add_dummy_fields_grouped)

        self.points = df

    def export_points(self):
        self.points.to_postgis(points_table_name, con=db, if_exists=if_exists)

    def export_lines(self):
        self.lines_gdf.to_postgis(lines_table_name, con=db, if_exists=if_exists)