import ast
from datetime import timedelta

import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd
from datetime import datetime

from config import settings

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
    routing = ast.literal_eval(DUMMY_SETTINGS.get('routing', False))

    # time params
    start_date = pd.to_datetime(DUMMY_SETTINGS.get('start_date', datetime.now()))
    end_date = pd.to_datetime(DUMMY_SETTINGS.get('end_date', datetime.now() + timedelta(hours=10)))

    def __new__(cls):
        if cls.graph is None:
            cls.graph = cls.download_graph(network_type=cls.network_type)
        if cls.routing:
            cls.init_routing()

    def __init__(self):
        self.graph = self.download_graph()

        self.points = None
        self.lines = None
        self.polygons = None

    @classmethod
    def download_graph(cls, network_type='all_private'):
        """
       Downloads OSM Data and generate random points as pandas DataFrame
       :return:
        """

        if cls.bbox:
            G = ox.graph_from_bbox(*cls.bbox, network_type=network_type)
        elif cls.address:
            G = ox.graph_from_place(cls.address, network_type=network_type)
        else:
            raise ValueError('bbox veya adres parametresi doldurulmalıdır')

        G = ox.project_graph(G, cls.crs)
        return G

    @classmethod
    def init_routing(cls):
        cls.graph = ox.speed.add_edge_speeds(cls.graph)
        cls.graph = ox.speed.add_edge_travel_times(cls.graph)

    def set_lines_from_db(self):
        """

        :return:
        """
        pass

    def set_lines_by_osmnx(self):
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

    def set_random_points_in_area(self) -> gpd.GeoDataFrame:
        """
        Downloads OSM Data and generate random points as pandas DataFrame
        :return:
        """

        Gp = ox.project_graph(self.graph)
        count = DUMMY_SETTINGS.get('sample_count', 1000)
        random_points = ox.utils_geo.sample_points(ox.get_undirected(Gp), count)

        self.points = random_points
        return random_points
