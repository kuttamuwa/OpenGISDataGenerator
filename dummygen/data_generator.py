import os
import geopandas as gpd
from config import settings
import osmnx as ox
import ast


DUMMY_SETTINGS = settings.DUMMY


class DummyDataGenerator:
    fields = DUMMY_SETTINGS.get('fields')
    bbox = ast.literal_eval(DUMMY_SETTINGS.get('bbox'))
    address = DUMMY_SETTINGS.get('address')

    def __init__(self):
        self.ways = self.retrieve_ways()
        self.columns = self.columns_from_config()

    def retrieve_ways(self, network_type='walk') -> gpd.GeoDataFrame:
        """
        Downloads OSM Data and extract ways as pandas DataFrame
        :return:
        """
        if self.bbox:
            G = ox.graph_from_bbox(*self.bbox)
        elif self.address:
            G = ox.graph_from_place(self.address)
        else:
            raise ValueError('bbox veya adres parametresi doldurulmalıdır')

        fig = ox.plot_graph(G)


    @classmethod
    def columns_from_config(cls):
        columns = {}
        for f in cls.fields:
            name, _type = f
            columns[name] = _type

        return columns


if __name__ == '__main__':
    # test
    d = DummyDataGenerator()
