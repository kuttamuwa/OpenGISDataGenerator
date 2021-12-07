import ast
import random
import uuid
from datetime import datetime, timedelta

import geopandas as gpd
import numpy as np
import pandas as pd
from mimesis import Person, Generic
from mimesis.locales import TR
from mimesis.enums import Gender

from config import settings

DUMMY_SETTINGS = settings.DUMMY
generic = Generic(locale=TR)


class DummyDataManipulator:
    crs = DUMMY_SETTINGS.get('crs')

    # dates
    start_date = pd.to_datetime(DUMMY_SETTINGS.get('start_date', datetime.now()))
    end_date = pd.to_datetime(DUMMY_SETTINGS.get('end_date', datetime.now() + timedelta(hours=10)))
    date_mixing = ast.literal_eval(DUMMY_SETTINGS.get('date_mixing', True))

    # distances
    random_distance = DUMMY_SETTINGS.get('constant', True)
    minimum_distance = DUMMY_SETTINGS.get('minimum_distance')
    maximum_distance = DUMMY_SETTINGS.get('maximum_distance')
    avg_speed = DUMMY_SETTINGS.get('avg_speed', 1.4)

    # person
    dummy_person = Person(locale='tr')
    min_age = DUMMY_SETTINGS.get('min_age', 16)
    max_age = DUMMY_SETTINGS.get('max_age', 70)

    @classmethod
    def random_date(cls):
        start_u = cls.start_date.value//10**9
        end_u = cls.end_date.value//10**9

        return pd.to_datetime(np.random.randint(start_u, end_u, 1), unit='s')[0]

    @classmethod
    def add_dummy_fields(cls, points: gpd.GeoDataFrame, add_time=True):
        points['PersonID'] = [uuid.uuid4() for _ in range(len(points))]
        points['Age'] = [cls.dummy_person.age(cls.min_age, cls.max_age) for _ in range(len(points))]
        points['Quality'] = [random.randint(0, 5) for _ in range(len(points))]
        points['Gender'] = [random.choice([Gender.MALE, Gender.FEMALE]).name for _ in range(len(points))]
        if add_time:
            points['Timestamp'] = [cls.random_date() for _ in range(len(points))]

        return points

    @classmethod
    def generate_points_along_line(cls, lines: gpd.GeoDataFrame):
        """
        Downloads OSM data if reload = True
        Generate points along lines and sum up.

        :return:
        """

        points = []

        for _, l in lines.iterrows():
            start_date = cls.random_date()

            how_many_people = np.random.randint(0, 3)
            distances = np.random.randint(cls.minimum_distance, cls.maximum_distance, how_many_people)
            distances.sort()

            for d in distances:
                adding_seconds = d // cls.avg_speed
                subpoints = l.geometry.interpolate(d)
                start_date += timedelta(seconds=adding_seconds)

                p = {'geometry': subpoints,
                     'wayid': l.osmid, # which way id is snapped?
                     'Timestamp': start_date}
                points.append(p)

        # points
        points_gdf = gpd.GeoDataFrame(points, crs=cls.crs)
        points_gdf = points_gdf[points_gdf['wayid'].apply(lambda x: str(x).isdigit())]
        points_gdf.drop_duplicates('geometry', inplace=True)
        points_gdf.reset_index(inplace=True)
        points_gdf.rename(columns={'index': 'ROWID'}, inplace=True)
        points_gdf.drop(columns=['wayid'], inplace=True)

        points_gdf['DTYPE'] = 'DYNAMIC'

        return gpd.GeoDataFrame(points, geometry='geometry')
