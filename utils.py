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
crs = loc_settings.crs

# time params
start_date = pd.to_datetime(date_settings.get('start_date', datetime.now()))
end_date = pd.to_datetime(date_settings.get('end_date', datetime.now() + timedelta(hours=10)))
date_mixing = ast.literal_eval(date_settings.get('date_mixing', True))


def random_date():
    start_u = start_date.value // 10 ** 9
    end_u = end_date.value // 10 ** 9

    return pd.to_datetime(np.random.randint(start_u, end_u, 1), unit='s')[0]
