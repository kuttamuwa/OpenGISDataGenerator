import ast
import warnings
from datetime import datetime
from datetime import timedelta

import geopandas as gpd
import osmnx as ox
import pandas as pd

from config import settings
from db.connector import db
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
        print("Loading graph..")
        if cls.bbox:
            G = ox.graph_from_bbox(*cls.bbox, network_type=network_type)
        elif cls.address:
            G = ox.graph_from_place(cls.address, network_type=network_type)
        else:
            raise ValueError('bbox veya adres parametresi doldurulmalıdır')

        G = ox.project_graph(G, cls.crs)
        print("Graph is loaded.")
        cls.graph = G

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
            self._load_points()
            self._load_lines()
            # self._load_polygons()  # Not Implemented

        except Exception as err:
            warnings.warn("Uncompatibility issues around data. Downloading again... \n"
                          f"Error : {err}")
            self.download_graph()
            # self.load()

    def download_lines(self):
        """
        Get lines from osmnx
        :return:
        """
        if self.lines is None:
            lines = ox.graph_to_gdfs(self.graph, nodes=False)
            lines.drop_duplicates('geometry', inplace=True)
            lines['length'] = lines['geometry'].length
            self.lines = lines

            return lines

    def generate_random_points_in_area(self, snap=True) -> gpd.GeoDataFrame:
        """
        Downloads OSM Data and generate random points as pandas DataFrame
        :return:
        """

        Gp = ox.project_graph(self.graph, to_crs=self.crs)
        random_points = ox.utils_geo.sample_points(ox.get_undirected(Gp), self.count)
        random_points = gpd.GeoDataFrame(random_points, geometry='geometry')
        random_points = DummyDataManipulator.add_dummy_fields(random_points)

        # if snap:
        #     print("Snapping points..")
        #     for _, l in self.lines.iterrows():
        #         geom = l.geometry
        #         geom.interpolate()

        self.points = random_points
        return random_points

    def download_poi(self):
        raise NotImplementedError

    def _load_lines(self):
        print("Lines are loading..")
        try:
            if self.lines is None:
                self.lines = gpd.read_postgis("SELECT * FROM LINES", con=db, crs=self.crs, geom_col='geometry')
        except Exception:
            self.download_lines()

    def _load_points(self):
        print("Points are loading..")
        try:
            if self.points is None:
                self.points = gpd.read_postgis("SELECT * FROM POINTS", con=db, crs=self.crs, geom_col='geometry')
        except Exception:
            self.generate_random_points_in_area()

    def _load_polygons(self):
        """
        POI
        :return: 
        """
        # print("Polygons are loading..")
        try:
            if self.polygons is None:
                self.polygons = gpd.read_postgis("SELECT * FROM POLYGONS", con=db, crs=self.crs, geom_col='geometry')
        except Exception:
            self.download_poi()


ds = DataStore()
dummy = DummyDataManipulator()
