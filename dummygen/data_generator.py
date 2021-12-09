import ast
import random
import uuid
from datetime import datetime, timedelta

import geopandas as gpd
import numpy as np
import pandas as pd
from mimesis import Person, Generic
from mimesis.enums import Gender
from mimesis.locales import TR

from config import settings

loc_settings = settings.LOCATION_SETTINGS
date_settings = settings.DATE_SETTINGS
dynamic_settings = settings.DYNAMIC_POINTS
person_settings = settings.PERSON

generic = Generic(locale=TR)


class DummyDataManipulator:
    crs = loc_settings.crs

    # time params
    start_date = pd.to_datetime(date_settings.get('start_date', datetime.now()))
    end_date = pd.to_datetime(date_settings.get('end_date', datetime.now() + timedelta(hours=10)))
    date_mixing = ast.literal_eval(date_settings.get('date_mixing', True))

    # distances
    minimum_distance = dynamic_settings.minimum_distance
    maximum_distance = dynamic_settings.maximum_distance
    avg_speed = dynamic_settings.avg_speed

    # person
    dummy_person = Person(locale='tr')
    min_age = person_settings.min_age
    max_age = person_settings.max_age

    @classmethod
    def random_date(cls):
        start_u = cls.start_date.value // 10 ** 9
        end_u = cls.end_date.value // 10 ** 9

        return pd.to_datetime(np.random.randint(start_u, end_u, 1), unit='s')[0]

    @classmethod
    def add_dummy_fields(cls, points: gpd.GeoDataFrame, add_time=True, add_person_id=True):
        """
        Adds dummy fields into GeoDataFrame
        :param points:
        :param add_time:
        :param add_person_id:
        :return:
        """
        points['Age'] = [cls.dummy_person.age(cls.min_age, cls.max_age) for _ in range(len(points))]
        points['Quality'] = [random.randint(0, 5) for _ in range(len(points))]
        points['Gender'] = [random.choice([Gender.MALE, Gender.FEMALE]).name for _ in range(len(points))]

        # todo: ?
        points['First Name'] = [cls.dummy_person.first_name() for _ in range(len(points))]
        points['Last Name'] = [cls.dummy_person.last_name() for _ in range(len(points))]

        if add_time:
            points['Timestamp'] = [cls.random_date() for _ in range(len(points))]

        if add_person_id:
            points['PersonID'] = [uuid.uuid4() for _ in range(len(points))]

        return points

    @classmethod
    def add_dummy_fields_fn(cls, x, add_timestamp=True):
        """
        Adds dummy fields into GeoDataFrame
       
        :return:
        """
        _gender = random.choice([Gender.MALE, Gender.FEMALE])
        x['Age'] = cls.dummy_person.age(cls.min_age, cls.max_age)
        x['Quality'] = random.randint(0, 5)
        x['Gender'] = _gender.name
        x['PersonID'] = uuid.uuid4()

        # todo: ?
        x['First Name'] = cls.dummy_person.first_name(gender=_gender)
        x['Last Name'] = cls.dummy_person.last_name(gender=_gender)

        if add_timestamp:
            print("Will added timestamp")
            x['Timestamp'] = cls.random_date()

        return x

    @classmethod
    def generate_points_along_line(cls, lines: gpd.GeoDataFrame, add_dummy=True):
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
                     'wayid': l.osmid,  # which way id is snapped?
                     'Timestamp': start_date}
                points.append(p)

        # points
        points_gdf = gpd.GeoDataFrame(points, crs=cls.crs)
        points_gdf = points_gdf[points_gdf['wayid'].apply(lambda x: str(x).isdigit())]
        points_gdf.drop_duplicates('geometry', inplace=True)
        points_gdf.reset_index(inplace=True)
        points_gdf.rename(columns={'index': 'ROWID'}, inplace=True)
        points_gdf.set_geometry('geometry', inplace=True)
        # points_gdf.drop(columns=['wayid'], inplace=True)

        # dummy
        if add_dummy:
            points_grouped = points_gdf.groupby('wayid')
            points_grouped = points_grouped.apply(cls.add_dummy_fields_fn, add_timestamp=False)
            points_gdf = points_grouped

        points_gdf['DTYPE'] = 'DYNAMIC'
        points_gdf.drop(columns=['wayid'], inplace=True)

        return points_gdf
