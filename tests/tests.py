from unittest import TestCase

from dummygen.data_generator import DummyDataManipulator
from dummygen.data_puller import DataStore
from db.connector import db, if_exists
from config import settings

loc_settings = settings.LOCATION_SETTINGS
poi_settings = settings.POI_SETTINGS
osm_settings = settings.OSM_SETTINGS

static_settings = settings.STATIC_POINTS
dynamic_settings = settings.DYNAMIC_POINTS
recursive_settings = settings.RECURSIVE_POINTS

date_settings = settings.DATE_SETTINGS


class DummyDataTests(TestCase):
    dummy = DummyDataManipulator()


class DataStoreTests(TestCase):
    ds = DataStore()

    def test_clean(self, lines=False, pois=False):
        DataStore.delete_mongodb('points')
        if lines:
            DataStore.delete_mongodb('lines')
        if pois:
            DataStore.delete_mongodb('pois')

    def test_run_static_points_shapely(self):
        points = self.ds.generate_random_points_shapely()
        # self.validate_static(points)

    def test_run_static_points_osmnx(self):
        points = self.ds.generate_random_points_osmnx()
        # self.validate_static(points)

    def test_run_recursive_points(self):
        if DataStore.get_point_counts() > 1:
            rec_points = self.ds.recursive_points()
        else:
            raise ValueError("There is no point created previously")

    def test_run_dynamic_points(self):
        dyn_points = DummyDataTests.dummy.generate_points_along_line(self.ds.lines)

        if len(dyn_points) != dynamic_settings.max_count:
            raise ValueError


db.gis.stations.insert_one(
    {
        "id": "1",
        "name": "station 1",
        "contact": {
            "mail": "station1@mail.com"
        },
        "geometry": {
            "coordinates": [
                50,
                60
            ],
            "type": "Point"
        },
        "measurements": [
            {
                "name": "temp",
                "unit": "c",
                "values": [
                    {
                        "time": 1482146800,
                        "value": 20
                    }
                ]
            },
            {
                "name": "wind",
                "unit": "km/h",
                "values": [
                    {
                        "time": 1482146833,
                        "value": 155
                    }
                ]
            }
        ]
    }
)

db.gis.stations.create_index({"geometry": "2dsphere"}.items())


dbm.gis.newpoints.insert_one(
    {
        "id": "1",
        "First Name": "Berge",
        "Last Name": "Biçer",
        "geometry": {
            "coordinates": [
                50,
                60
            ],
            "type": "Point"
        },
        "DTYPE": "STATIC",
        "Gender": "MALE",
        "Timestamp": 1482146800,
        "PersonID": "ce3c9e9c-c874-4757-b2a5-6fdec173b01a",
        "ROWID": 0,
    }
)

dbm.gis.newpoints.create_index({"geometry": "2dsphere"}.items())