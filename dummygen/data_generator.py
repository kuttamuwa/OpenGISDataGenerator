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

        x['First Name'] = cls.dummy_person.first_name(gender=_gender)
        x['Last Name'] = cls.dummy_person.last_name(gender=_gender)

        if add_timestamp:
            print("Will added timestamp")
            x['Timestamp'] = cls.random_date()

        return x

    @classmethod
    def generate_points_along_line(cls, lines: gpd.GeoDataFrame):
        """
        Generate points along lines and sum up.

        :param lines:
        :return:
        """

        points = []

        # filter
        # lines = lines[lines.length > cls.maximum_distance]

        print(f"Count of lines: {len(lines)}")
        for _, l in lines.iterrows():
            start_date = cls.random_date()

            distances = np.random.randint(0, dynamic_settings.maximum_distance, np.random.randint(1, dynamic_settings.max_step))
            distances.sort()

            _gender = random.choice([Gender.MALE, Gender.FEMALE])
            fname = cls.dummy_person.first_name(gender=_gender)
            lname = cls.dummy_person.last_name(gender=_gender)
            age = cls.dummy_person.age(person_settings.min_age, person_settings.max_age)
            pid = uuid.uuid4()
            q = random.randint(0, 5)

            for d in distances:
                p = {
                    'geometry': l.geometry.interpolate(d),
                    'Timestamp': start_date + timedelta(minutes=float(d // dynamic_settings.avg_speed)),
                    'First Name': fname,
                    'Last Name': lname,
                    'Gender': _gender.name,
                    'PersonID': pid,
                    'Quality': q,
                    'Age': age
                }

                points.append(p)

            if len(points) > dynamic_settings.max_count:
                break

        # points
        points_gdf = gpd.GeoDataFrame(points, crs=cls.crs)
        points_gdf.drop_duplicates('geometry', inplace=True)
        points_gdf.reset_index(inplace=True)
        points_gdf.rename(columns={'index': 'ROWID'}, inplace=True)
        points_gdf.set_geometry('geometry', inplace=True)
        points_gdf['DTYPE'] = 'DYNAMIC'

        print(f"Generated points : {len(points)}")

        return points_gdf
