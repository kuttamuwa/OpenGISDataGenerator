"""
Dummy Location Generator

Dependency: OSM (osmnx)

Purpose: Collects

@Author: Umut Ucok, 2021

"""
import ast
import random
import uuid
import warnings
from datetime import datetime
from datetime import timedelta

import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd
import shapely.geometry
from colorama import Fore
from mimesis import Person, Generic
from mimesis.enums import Gender
from mimesis.locales import TR
from pymongo import GEOSPHERE
from shapely.geometry import Point, LineString

from config import settings
from db.connector import db, if_exists
from utils import random_date

loc_settings = settings.LOCATION_SETTINGS
date_settings = settings.DATE_SETTINGS
dynamic_settings = settings.DYNAMIC_POINTS
person_settings = settings.PERSON
crs = loc_settings.crs

loc_settings = settings.LOCATION_SETTINGS
poi_settings = settings.POI_SETTINGS
osm_settings = settings.OSM_SETTINGS

static_settings = settings.STATIC_POINTS
recursive_settings = settings.RECURSIVE_POINTS

address = loc_settings.address
reload_data = ast.literal_eval(loc_settings.reload)
bbox = static_settings.bbox

network_type = osm_settings.network_type
use_osmnx = ast.literal_eval(osm_settings.use_osmnx)

poi_tags = ast.literal_eval(poi_settings.poi_tags)
poi_center = poi_settings.poi_center
poi_buffer_distance = poi_settings.poi_buffer_distance

# time params
start_date = pd.to_datetime(date_settings.get('start_date', datetime.now()))
end_date = pd.to_datetime(date_settings.get('end_date', datetime.now() + timedelta(hours=10)))
date_mixing = ast.literal_eval(date_settings.get('date_mixing', True))

# person
dummy_person = Person(locale='tr')
min_age = person_settings.min_age
max_age = person_settings.max_age

generic = Generic(locale=TR)

ox.config(use_cache=True, log_console=True,
          # default_crs=DUMMY_SETTINGS.crs
          )


def save(lines: gpd.GeoDataFrame, table_name: str):
    # epsg = int(crs.split(':')[-1])
    # lines.to_crs(epsg=epsg, inplace=True)
    lines['geometry'] = lines['geometry'].apply(lambda x: shapely.geometry.mapping(x))

    geodict = lines.to_dict(orient='records')

    collection = db.gis.get_collection(table_name)
    collection.create_index([("geometry", GEOSPHERE)])

    if if_exists == 'replace':
        collection.drop()

    collection.insert_many(geodict)


def read_lines(column_list=('osmid', 'name', 'length', 'geometry')):
    results = []
    for v in db.gis.lines.find():
        data = {k: v[k] for k in column_list}
        results.append(data)

    gdf = gpd.GeoDataFrame(results)
    if gdf.empty:
        raise ValueError

    gdf['geometry'] = gdf['geometry'].apply(lambda x: LineString(x['coordinates']))
    gdf.set_geometry('geometry', inplace=True)
    gdf.set_crs(epsg=4326, inplace=True)

    return gdf


def read_points(column_list=('geometry', 'DTYPE', 'Age',
                             'Quality', 'Gender',
                             # 'First Name', 'Last Name',
                             'Timestamp', 'PersonID')):
    results = []
    for v in db.gis.points.find():
        data = {k: v[k] for k in column_list}
        results.append(data)

    gdf = gpd.GeoDataFrame(results)
    if gdf.empty:
        raise ValueError

    gdf['geometry'] = gdf['geometry'].apply(lambda x: Point(x['coordinates']))
    gdf.set_geometry('geometry', inplace=True)
    gdf.set_crs(epsg=4326, inplace=True)

    return gdf


def download_lines(graph_obj):
    lines = ox.graph_to_gdfs(graph_obj, nodes=False)
    lines.drop(columns=[i for i in lines.columns if i not in ('geometry', 'osmid', 'length', 'name')],
               inplace=True)
    lines.drop_duplicates('geometry', inplace=True)
    save(lines, 'lines')


def download_pois():
    poi_gdf = ox.geometries_from_point(poi_center, tags=poi_tags, dist=poi_buffer_distance)
    poi_gdf['GEO_TYPE'] = poi_gdf.geometry.type

    # projection
    poi_gdf.to_crs(crs=crs, inplace=True)

    if poi_gdf.empty:
        warnings.warn("There is no downloaded POI around your center ! "
                      "Please set another poi_center ! ")

    else:
        print(f"Downloaded poi : {poi_gdf.head(5)} \n"
              f"Length : {len(poi_gdf)}")

        gdf_point = poi_gdf[poi_gdf['GEO_TYPE'] == 'Point']
        gdf_polygon = poi_gdf[poi_gdf['GEO_TYPE'] == 'Polygon']

        save(gdf_point, 'pois_point')
        save(gdf_polygon, 'pois_polygon')


def download_osm_data():
    # download graph object
    graph_obj = ox.graph_from_place(address, network_type=network_type)
    graph_obj = ox.project_graph(graph_obj, to_crs=crs)

    # download lines
    download_lines(graph_obj)
    print(Fore.GREEN + "Lines are downloaded")

    # download pois
    download_pois()
    print(Fore.GREEN + "Pois are downloaded")

    return graph_obj


# dummy data generator
def add_dummy_fields(points: gpd.GeoDataFrame, add_time=True, add_person_id=True):
    """
    Adds dummy fields into GeoDataFrame
    :param points:
    :param add_time:
    :param add_person_id:
    :return:
    """
    points['Age'] = [dummy_person.age(min_age, max_age) for _ in range(len(points))]
    points['Quality'] = [random.randint(0, 5) for _ in range(len(points))]
    points['Gender'] = [random.choice([Gender.MALE, Gender.FEMALE]).name for _ in range(len(points))]

    # points['First Name'] = [dummy_person.first_name() for _ in range(len(points))]
    # points['Last Name'] = [dummy_person.last_name() for _ in range(len(points))]

    if add_time:
        points['Timestamp'] = [random_date() for _ in range(len(points))]

    if add_person_id:
        points['PersonID'] = [uuid.uuid4() for _ in range(len(points))]

    return points


def add_dummy_fields_fn(x, add_timestamp=True):
    """
    Adds dummy fields into GeoDataFrame

    :return:
    """
    _gender = random.choice([Gender.MALE, Gender.FEMALE])
    x['Age'] = dummy_person.age(min_age, max_age)
    x['Quality'] = random.randint(0, 5)
    x['Gender'] = _gender.name
    x['PersonID'] = uuid.uuid4()

    # x['First Name'] = dummy_person.first_name(gender=_gender)
    # x['Last Name'] = dummy_person.last_name(gender=_gender)

    if add_timestamp:
        print("Will added timestamp")
        x['Timestamp'] = random_date()

    return x


def _generate_random_points_shapely():
    xmin, ymin, xmax, ymax = bbox
    points = []
    count = static_settings.sample_count

    while count > 0:
        x = random.uniform(xmin, xmax)
        y = random.uniform(ymin, ymax)
        point = Point(x, y)
        points.append(point)
        count += -1

    points = gpd.GeoDataFrame(points)
    points.rename(columns={0: 'geometry'}, inplace=True)
    points.set_geometry('geometry', inplace=True)
    points = points.set_crs(crs=crs)

    return points


def generate_points_along_line():
    """
    Generate points along lines and sum up.
    :return:
    """

    points = []

    # filter
    # lines = lines[lines.length > maximum_distance]
    lines = read_lines()

    print(f"Count of lines: {len(lines)}")
    for _, l in lines.iterrows():

        distances = np.random.randint(0, dynamic_settings.maximum_distance,
                                      np.random.randint(1, dynamic_settings.max_step))
        distances.sort()

        _gender = random.choice([Gender.MALE, Gender.FEMALE])
        fname = dummy_person.first_name(gender=_gender)
        lname = dummy_person.last_name(gender=_gender)
        age = dummy_person.age(person_settings.min_age, person_settings.max_age)
        pid = uuid.uuid4()
        q = random.randint(0, 5)

        for d in distances:
            p = {
                'geometry': l.geometry.interpolate(d),
                'Timestamp': start_date + timedelta(minutes=float(d // dynamic_settings.avg_speed)),
                # 'First Name': fname,
                # 'Last Name': lname,
                'Gender': _gender.name,
                'PersonID': pid,
                'Quality': q,
                'Age': age
            }

            points.append(p)

        if len(points) > dynamic_settings.max_count:
            break

    # points
    points_gdf = gpd.GeoDataFrame(points, crs=crs)
    points_gdf.drop_duplicates('geometry', inplace=True)
    points_gdf.reset_index(inplace=True)
    points_gdf.rename(columns={'index': 'ROWID'}, inplace=True)
    points_gdf.set_geometry('geometry', inplace=True)
    points_gdf['DTYPE'] = 'DYNAMIC'

    print(f"Generated points : {len(points)}")
    points_gdf['PersonID'] = points_gdf['PersonID'].astype(str)
    save(points_gdf, 'points')

    return points_gdf


def generate_random_points_in_area(add_dummy=True) -> gpd.GeoDataFrame:
    """
    Downloads OSM Data and generate random points snapped to roads as pandas DataFrame
    :return:
    """
    print("Generating points with shapely")
    random_points = _generate_random_points_shapely()

    random_points['DTYPE'] = 'STATIC'

    if add_dummy:
        random_points = add_dummy_fields(random_points, add_time=True)

    random_points['PersonID'] = random_points['PersonID'].astype(str)
    save(random_points, 'points')

    return random_points


def generate_recursive_points():
    """
    Sampled count of points will be duplicated with different attributes
    :return:
    """
    points = read_points()
    repeated_times = recursive_settings.repeated_times

    while repeated_times > 0:
        points_sampled = points.sample(recursive_settings.recursive_sample)
        points_sampled['DTYPE'] = 'RECURSIVE'

        # different attributes
        points_sampled['Timestamp'] = [pd.Timestamp(i) for i in points_sampled['Timestamp']]
        points_sampled['Timestamp'] = points_sampled['Timestamp'] + timedelta(minutes=recursive_settings.wait_min)

        repeated_times += - 1
        print(f"Appended points with recursive")
        points.append(points_sampled)

    save(points, 'points')
    return points


def generate_points():
    print("Started to generating..")
    static_random_points = generate_random_points_in_area()
    print(Fore.GREEN + "Static points are generated ! : \n"
                       f"{static_random_points.head(10)}")

    points_on_line = generate_points_along_line()
    print(Fore.GREEN + "Points on the line (DYNAMIC) are generated ! : \n"
                       f"{points_on_line.head(10)}")

    rec_points = generate_recursive_points()
    print("Recursive points are added : \n"
          f"{rec_points.head(10)}")


if __name__ == '__main__':
    try:
        assert db.gis.lines.count_documents({}) > 0
    except AssertionError:
        graph = download_osm_data()

    generate_points()
