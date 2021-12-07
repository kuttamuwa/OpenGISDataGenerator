import ast
import warnings
from datetime import datetime
from datetime import timedelta

import geopandas as gpd
import osmnx as ox
import pandas as pd

from config import settings
from db.connector import db, if_exists
from dummygen.data_generator import DummyDataManipulator

DUMMY_SETTINGS = settings.DUMMY

ox.config(use_cache=True, log_console=True)


class DataStore:
    """
    POIleri çekeceğiz -> osmnx
    Lineları çekeceğiz -> osmnx

    POI'lere buffer at
    POI'ler ile müşterilere intersection, contains, within yapalım

    """
    graph = None

    crs = DUMMY_SETTINGS.get('crs')
    bbox = ast.literal_eval(DUMMY_SETTINGS.get('bbox'))
    address = DUMMY_SETTINGS.get('address')
    reload_data = ast.literal_eval(DUMMY_SETTINGS.get('reload', False))
    network_type = DUMMY_SETTINGS.get('network_type', 'all_private')
    routing = DUMMY_SETTINGS.get('routing', False)
    count = DUMMY_SETTINGS.get('count', 1000)

    # time params
    start_date = pd.to_datetime(DUMMY_SETTINGS.get('start_date', datetime.now()))
    end_date = pd.to_datetime(DUMMY_SETTINGS.get('end_date', datetime.now() + timedelta(hours=10)))

    @classmethod
    def download_graph(cls, network_type='all_private'):
        """
       Downloads OSM Data and generate random points as pandas DataFrame
       :return:
        """
        if cls.graph is None:
            print("Loading graph..")
            if cls.bbox:
                G = ox.graph_from_bbox(*cls.bbox, network_type=network_type)
            elif cls.address:
                G = ox.graph_from_place(cls.address, network_type=network_type)
            else:
                raise ValueError('bbox veya adres parametresi doldurulmalıdır')

            G = ox.project_graph(G, cls.crs)
            cls.graph = G
            print("Graph is loaded.")
        else:
            print("Graph is already loaded !")

    @classmethod
    def init_routing(cls):
        cls.graph = ox.speed.add_edge_speeds(cls.graph)
        cls.graph = ox.speed.add_edge_travel_times(cls.graph)

    def __init__(self):
        self.points = None
        self.lines = None
        self.polygons = None

        # load data
        self.load()

    def load(self):
        try:
            self._load_lines()
            self._load_points()
            # self._load_polygons()  # Not Implemented

        except Exception as err:
            warnings.warn("Uncompatibility issues around data. Downloading again... \n"
                          f"Error : {err}")
            self.download_graph()
            self.load()

    def download_lines(self, save=True, set=True):
        """
        Get lines from osmnx
        :return:
        """
        if self.lines is None:
            print("Lines are downloading..")
            lines = ox.graph_to_gdfs(self.graph, nodes=False)
            lines.drop(columns=[i for i in lines.columns if i not in ('geometry', 'osmid', 'length', 'name')],
                       inplace=True)
            lines.drop_duplicates('geometry', inplace=True)
            lines['length'] = lines['geometry'].length

            if set:
                self.lines = lines

            if save:
                self._save_lines()

            return lines

    def generate_points(self):
        self.generate_random_points_in_area()  # static points
        print(f"Static points are generated. Length : {len(self.points)}")

        print("Recursive points are generating..")
        repeated_times = DUMMY_SETTINGS.get('repeated_times', 3)
        sample_count = DUMMY_SETTINGS.get('recursive_sample', 200)

        while repeated_times > 0:
            self.generate_recursive_points(sample_count=sample_count)
            print(f"Recursive Points are generated, \n "
                  f"Length of all points : {len(self.points)}")
            repeated_times += -1
            print(f"Recursive last : {repeated_times}")

        self._save_points()
        print("Recursive points are generated and saved ")

        # different places
        points = DummyDataManipulator.generate_points_along_line(self.lines)
        points = DummyDataManipulator.add_dummy_fields(points, add_time=False)
        self.points = self.points.append(points)
        self._save_points()
        print("Generated points along line and saved !")

    def generate_recursive_points(self, sample_count=None):
        """
        Sampled count of points will be duplicated with different attributes
        :return:
        """

        points = self.points.sample(sample_count)

        # different attributes
        points['Timestamp'] = points['Timestamp'] + timedelta(minutes=30)  # like they're waiting for half hour
        points['DTYPE'] = 'RECURSIVE'

        self.points = self.points.append(points)
        print(f"Appended points with recursive")

    def generate_random_points_in_area(self, save=True, set=True, add_dummy=True) -> gpd.GeoDataFrame:
        """
        Downloads OSM Data and generate random points snapped to roads as pandas DataFrame
        :return:
        """

        Gp = ox.project_graph(self.graph, to_crs=self.crs)
        random_points = ox.utils_geo.sample_points(ox.get_undirected(Gp), self.count)
        random_points = gpd.GeoDataFrame(random_points)
        random_points.rename(columns={0: 'geometry'}, inplace=True)
        random_points.set_geometry('geometry', inplace=True)
        random_points['DTYPE'] = 'STATIC'

        if add_dummy:
            random_points = DummyDataManipulator.add_dummy_fields(random_points, add_time=True)

        if set:
            self.points = random_points

        if save:
            self._save_points()

        return random_points

    def download_poi(self):
        raise NotImplementedError

    def _load_lines(self):
        print("Lines are loading..")
        try:
            if self.lines is None:
                self.lines = gpd.read_postgis("SELECT * FROM LINES", con=db, crs=self.crs, geom_col='geometry')
        except Exception as err:
            warnings.warn(f"Load lines raised error : {err}")
            self.download_lines(save=True)

        finally:
            print(f"Lines are loaded : {self.lines.head(5)}")

    def _load_points(self):
        print("Points are loading..")
        try:
            if self.points is None:
                self.points = gpd.read_postgis("SELECT * FROM POINTS", con=db, crs=self.crs, geom_col='geometry')

        except Exception as err:
            warnings.warn(f"Loading points raised error : {err}")
            self.generate_points()

        finally:
            print(f"Points are loaded: {self.points.head(5)} ")

    def _load_polygons(self):
        """
        POI
        :return: 
        """
        # print("Polygons are loading..")
        try:
            if self.polygons is None:
                self.polygons = gpd.read_postgis("SELECT * FROM POLYGONS", con=db, crs=self.crs, geom_col='geometry')
        except Exception as err:
            warnings.warn(f"Loading polygons raised error : {err}")
            self.download_poi()

    def _save_points(self):
        self.points.to_postgis('points', con=db, if_exists=if_exists)
        print("Points are saved")

    def _save_lines(self):
        self.lines.to_postgis('lines', con=db, if_exists=if_exists)
        print("Lines are saved.")

    def _save_polygons(self):
        self.polygons.to_postgis('polygons', con=db, if_exists=if_exists)
        print("Polygons are saved")


ds = DataStore()
dummy = DummyDataManipulator()
