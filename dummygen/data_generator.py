import ast
import random
import uuid
from datetime import datetime, timedelta

import geopandas as gpd
import numpy as np
import pandas as pd
from mimesis import Person
from mimesis.enums import Gender

from config import settings

DUMMY_SETTINGS = settings.DUMMY


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
        if cls.date_mixing:
            start_date = pd.to_datetime(pd.date_range(cls.start_date, cls.end_date, periods=1)[0])
        else:
            start_date = cls.start_date

        return start_date

    @classmethod
    def add_dummy_fields(cls, points: gpd.GeoDataFrame):
        points['PersonID'] = [uuid.uuid4() for _ in range(len(points))]
        points['PersonID'] = [uuid.uuid4() for _ in range(len(points))]
        points['Age'] = [cls.dummy_person.age(cls.min_age, cls.max_age) for _ in range(len(points))]
        points['Quality'] = [random.randint(0, 5) for _ in range(len(points))]
        points['Gender'] = [random.choice([Gender.MALE, Gender.FEMALE]) for _ in range(len(points))]

        return points

    def generate_points_along_line(self, lines: gpd.GeoDataFrame):
        """
        Downloads OSM data if reload = True
        Generate points along lines and sum up.

        :return:
        """

        points = []

        for _, l in lines.iterrows():
            start_date = pd.to_datetime(pd.date_range(self.start_date, self.end_date, periods=1)[0])

            how_many_people = np.random.randint(0, 3)
            distances = np.random.randint(self.minimum_distance, self.maximum_distance, how_many_people)
            distances.sort()

            for d in distances:
                adding_seconds = d // self.avg_speed
                subpoints = l.geometry.interpolate(d)
                start_date += timedelta(seconds=adding_seconds)

                p = {'geometry': subpoints, 'wayid': l.osmid, 'Timestamp': start_date}
                points.append(p)

        # points
        points_gdf = gpd.GeoDataFrame(points, crs=self.crs)
        points_gdf = points_gdf[points_gdf['wayid'].apply(lambda x: str(x).isdigit())]
        points_gdf.drop_duplicates('geometry', inplace=True)
        points_gdf.reset_index(inplace=True)
        points_gdf.rename(columns={'index': 'ROWID'}, inplace=True)

        return points
