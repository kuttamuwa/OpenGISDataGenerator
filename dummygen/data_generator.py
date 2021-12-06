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
    random_distance = ast.literal_eval(DUMMY_SETTINGS.get('constant', True))
    minimum_distance = ast.literal_eval(DUMMY_SETTINGS.get('minimum_distance'))
    maximum_distance = ast.literal_eval(DUMMY_SETTINGS.get('maximum_distance'))
    avg_speed = DUMMY_SETTINGS.get('avg_speed', 1.4)

    # person
    dummy_person = Person(locale='tr')
    min_age = ast.literal_eval(DUMMY_SETTINGS.get('min_age', 16))
    max_age = ast.literal_eval(DUMMY_SETTINGS.get('max_age', 70))

    @classmethod
    def random_date(cls):
        if cls.date_mixing:
            start_date = pd.to_datetime(pd.date_range(cls.start_date, cls.end_date, periods=1)[0])
        else:
            start_date = cls.start_date

        return start_date

    def add_dummy_fields_grouped(self, x):
        _gender = random.choice([Gender.MALE, Gender.FEMALE])
        x['First Name'] = self.dummy_person.first_name(gender=_gender)
        x['PersonID'] = uuid.uuid4()  # todo: test et
        x['Last Name'] = self.dummy_person.last_name(gender=_gender)
        x['Age'] = self.dummy_person.age(self.min_age, self.max_age)
        x['Quality'] = random.randint(0, 5)
        x['Gender'] = _gender

        return x

    def add_dummy_fields(self, points: gpd.GeoDataFrame, use='wayid'):
        grp = points.groupby(use)
        df = grp.apply(self.add_dummy_fields_grouped)

        return df

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
