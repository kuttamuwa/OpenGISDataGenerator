import ast
import random

from mimesis import Person

import geopandas as gpd
import osmnx as ox

from config import settings

DUMMY_SETTINGS = settings.DUMMY


class DummyDataGenerator:
    bbox = ast.literal_eval(DUMMY_SETTINGS.get('bbox'))
    address = DUMMY_SETTINGS.get('address')

    dummy_person = Person(locale='tr')

    def __init__(self):
        self.points = self.generate_random_points()
        self.add_dummy_fields()

    def generate_random_points(self, network_type='all_private') -> gpd.GeoDataFrame:
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

        Gp = ox.project_graph(G)

        random_points = ox.utils_geo.sample_points(ox.get_undirected(Gp), DUMMY_SETTINGS.get('sample_count'))
        # _, lines = ox.graph_to_gdfs(G)  # _ is nodes

        # cleaning
        # lines.drop(columns=['lanes', 'maxspeed', 'bridge', 'junction'], inplace=True)

        return random_points

    def add_dummy_fields(self):
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

    def add_x_step(self):
        """
        Recursive function
        :return:
        """


if __name__ == '__main__':
    # test
    d = DummyDataGenerator()
