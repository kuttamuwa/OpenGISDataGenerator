"""
Dummy Location Generator

Dependency: OSM (osmnx)

Purpose: Collects

@Author: Umut Ucok, 2021

"""
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

from utils import random_date

from config import settings

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

count = static_settings.sample_count
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

import ast
import random
import warnings
from datetime import datetime
from datetime import timedelta

import geopandas as gpd
import osmnx as ox
import pandas as pd
import shapely.geometry
from pymongo import GEOSPHERE
from shapely.geometry import Point, LineString, Polygon

from config import settings
from db.connector import db, if_exists
from errors.configerr import OSMNXMustbeTrue

ox.config(use_cache=True, log_console=True,
          # default_crs=DUMMY_SETTINGS.crs
          )

# OBJECTS
graph = None
points: gpd.GeoDataFrame = None
lines: gpd.GeoDataFrame = None
pois_points: gpd.GeoDataFrame = None
pois_polygons: gpd.GeoDataFrame = None


# FUNCTIONS
# data generator
def add_dummy_fields(add_time=True, add_person_id=True):
    """
    Adds dummy fields into GeoDataFrame
    :param add_time:
    :param add_person_id:
    :return:
    """
    points['Age'] = [dummy_person.age(min_age, max_age) for _ in range(len(points))]
    points['Quality'] = [random.randint(0, 5) for _ in range(len(points))]
    points['Gender'] = [random.choice([Gender.MALE, Gender.FEMALE]).name for _ in range(len(points))]

    points['First Name'] = [dummy_person.first_name() for _ in range(len(points))]
    points['Last Name'] = [dummy_person.last_name() for _ in range(len(points))]

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

    x['First Name'] = dummy_person.first_name(gender=_gender)
    x['Last Name'] = dummy_person.last_name(gender=_gender)

    if add_timestamp:
        print("Will added timestamp")
        x['Timestamp'] = random_date()

    return x


def generate_points_along_line():
    """
    Generate points along lines and sum up.
    :return:
    """

    generated_points_online = []

    # filter
    # lines = lines[lines.length > maximum_distance]

    print(f"Count of lines: {len(lines)}")
    for _, l in lines.iterrows():
        start_date_fn = random_date()

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
                'Timestamp': start_date_fn + timedelta(minutes=float(d // dynamic_settings.avg_speed)),
                'First Name': fname,
                'Last Name': lname,
                'Gender': _gender.name,
                'PersonID': pid,
                'Quality': q,
                'Age': age
            }

            generated_points_online.append(p)

        if len(generated_points_online) > dynamic_settings.max_count:
            break

    # points
    points_gdf = gpd.GeoDataFrame(generated_points_online, crs=crs)
    points_gdf.drop_duplicates('geometry', inplace=True)
    points_gdf.reset_index(inplace=True)
    points_gdf.rename(columns={'index': 'ROWID'}, inplace=True)
    points_gdf.set_geometry('geometry', inplace=True)
    points_gdf['DTYPE'] = 'DYNAMIC'

    print(f"Generated points : {len(generated_points_online)}")

    return points_gdf


# data puller
def download_graph():
    """
   Downloads OSM Data and generate random points as pandas DataFrame
   :return:
    """
    try:
        if graph is None and use_osmnx is True:
            print("Loading graph..")
            if address:
                G = ox.graph_from_place(address, network_type=network_type)
            else:
                raise ValueError('bbox veya adres parametresi doldurulmalıdır')

            print("Graph is created. Now projecting..")
            graph = ox.project_graph(G, to_crs=crs)
            print("Graph is loaded.")
        else:
            print("Graph is already loaded or not going to use !")
    except ConnectionError:
        raise ConnectionError("Internet bağlantınızı kontrol ediniz !")


def download_lines():
    """
    Get lines from osmnx
    :return:
    """
    if lines is None:
        if graph is None:
            raise OSMNXMustbeTrue("OSMNX set cannot be False if there is no data ! ")

        print("Lines are downloading..")
        lines = ox.graph_to_gdfs(graph, nodes=False)
        lines.drop(columns=[i for i in lines.columns if i not in ('geometry', 'osmid', 'length', 'name')],
                   inplace=True)
        lines.drop_duplicates('geometry', inplace=True)

        return lines


def recursive_points():
    print("Recursive points are generating..")
    repeated_times = recursive_settings.repeated_times
    sample_count = recursive_settings.recursive_sample

    # while repeated_times > 0:
    generate_recursive_points(sample_count=sample_count, repeated_times=repeated_times)
    print(f"Recursive Points are generated, \n "
          f"Length of all points : {len(points)}")
    # repeated_times += -1
    # print(f"Recursive last : {repeated_times}")

    _save_points()
    print("Recursive points are generated and saved ")


def static_points(self):
    self.generate_random_points_in_area(save=True)  # static points
    print(f"Static points are generated and saved. Length : {len(self.points)}")


def dynamic_points(self):
    points = DummyDataManipulator.generate_points_along_line(self.lines)
    print(f"Random points along the line are generated, length : {len(points)} ")

    if self.points is None:
        self.points = points
    else:
        self.points = self.points.append(points)

    self.points.drop_duplicates(inplace=True)
    self._save_points()
    print("Points along line saved !")


def generate_recursive_points(self, sample_count=1000, repeated_times=5):
    """
    Sampled count of points will be duplicated with different attributes
    :return:
    """

    points = self.points.sample(sample_count)
    points['DTYPE'] = 'RECURSIVE'

    while repeated_times > 0:
        # different attributes
        points['Timestamp'] = [pd.Timestamp(i) for i in points['Timestamp']]
        points['Timestamp'] = points['Timestamp'] + timedelta(minutes=recursive_settings.wait_min)

        if self.points is None:
            self.points = points
        else:
            self.points = self.points.append(points)

        repeated_times += - 1
        print(f"Appended points with recursive")


def generate_random_points_shapely(self):
    xmin, ymin, xmax, ymax = self.bbox
    points = []
    count = self.count

    while count > 0:
        x = random.uniform(xmin, xmax)
        y = random.uniform(ymin, ymax)
        point = Point(x, y)
        points.append(point)
        count += -1

    points = gpd.GeoDataFrame(points)
    points.rename(columns={0: 'geometry'}, inplace=True)
    points.set_geometry('geometry', inplace=True)
    points = points.set_crs(crs=self.crs)

    return points


def generate_random_points_in_area(self, save=True, set=True, add_dummy=True) -> gpd.GeoDataFrame:
    """
    Downloads OSM Data and generate random points snapped to roads as pandas DataFrame
    :return:
    """

    # if self.use_osmnx is True:
    #     print("Generating points with osmnx")
    #     random_points = self.generate_random_points_osmnx()
    # else:
    print("Generating points with shapely")
    random_points = self.generate_random_points_shapely()

    random_points['DTYPE'] = 'STATIC'

    if add_dummy:
        random_points = DummyDataManipulator.add_dummy_fields(random_points, add_time=True)

    if set:
        if self.points is not None:
            self.points = self.points.append(random_points)
        else:
            self.points = random_points

    if save:
        self._save_points()

    return random_points


def download_poi():
    """
    Downloads POI
    :return:
    """
    print("Downloading POI")
    print(f"poi tags : {poi_tags}")
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

        if pois is not None:
            print("POIs are adding..")
            pois = pois.append(poi_gdf)
            remained_columns = pois.columns
        else:
            pois = poi_gdf
            remained_columns = poi_gdf.columns

        # filtering
        remained_columns = [i for i in remained_columns if i not in ('geometry', 'name', 'GEO_TYPE')]
        pois.drop(columns=remained_columns, inplace=True)

        # drop duplicates
        pois.drop_duplicates('geometry', inplace=True)

        _save_pois()


def _load_lines():
    print("Lines are loading..")
    try:
        lines = read_line_mongodb('lines', )
    except ValueError:
        warnings.warn(f"Lines are downloading..")
        lines = download_lines()
        _save_lines()


def _load_points():
    print("Points are loading..")
    if reload_data:
        print("Reloading.. ")
        delete_mongodb('points')
        generate_points()
    else:
        print("No reload !")
        try:
            points = read_point_mongodb('points')
            print("Generated points will be appended !")
            generate_points()

        except ValueError:
            warnings.warn(f"Points are generating..")
            generate_points()


def _load_poi():
    """
    POI
    :return:
    """
    print("POIs are loading..")
    try:
        if pois is None:
            self.pois = self.read_point_mongodb('pois', ('name', 'geometry'))
            self.download_poi()
    except ValueError:
        warnings.warn(f"Couldn't read POIS table")
        self.download_poi()


def _save_points(self, replace=False):
    if replace:
        self.delete_mongodb('points')
        self.point_write_mongodb(self.points, 'points')
    else:
        self.point_write_mongodb(self.points, 'points')
    print("Points are saved")


def get_point_counts(cls):
    return db.gis.point.count_documents({})


def _save_lines(self):
    self.line_write_mongodb(self.lines, 'lines')
    print("Lines are saved.")


def _save_pois(self):
    self.pois_write_mongodb(self.pois, 'pois')
    print("POIs are saved")


# Mongodb
def point_write_mongodb(gdf: gpd.GeoDataFrame, table_name):
    gdf = gdf.to_crs(epsg=4326)
    gdf['geometry'] = gdf['geometry'].apply(lambda x: shapely.geometry.mapping(x))

    if 'PersonID' in gdf.columns:
        gdf['PersonID'] = gdf['PersonID'].astype(str)

    geodict = gdf.to_dict(orient='records')

    collection = db.gis.get_collection(table_name)
    if if_exists == 'replace':
        collection.drop()

    collection.create_index([("geometry", GEOSPHERE)])
    collection.insert_many(geodict)


def pois_write_mongodb(self, gdf, table_name):
    gdf_point = gdf[gdf['GEO_TYPE'] == 'Point']
    gdf_polygon = gdf[gdf['GEO_TYPE'] == 'Polygon']

    self.point_write_mongodb(gdf_point, table_name)
    self.polygon_write_mongodb(gdf_polygon, f'{table_name}_polygon')


def polygon_write_mongodb(gdf: gpd.GeoDataFrame, table_name):
    gdf.to_crs(epsg=4326, inplace=True)
    gdf['geometry'] = gdf['geometry'].apply(lambda x: shapely.geometry.mapping(x))
    geodict = gdf.to_dict(orient='records')
    collection = db.gis.get_collection(table_name)

    if if_exists == 'replace':
        collection.drop()
    collection.create_index([("geometry", GEOSPHERE)])

    collection.insert_many(geodict)


def line_write_mongodb(gdf: gpd.GeoDataFrame, table_name):
    gdf.to_crs(epsg=4326, inplace=True)
    gdf['geometry'] = gdf['geometry'].apply(lambda x: shapely.geometry.mapping(x))

    geodict = gdf.to_dict(orient='records')

    collection = db.gis.get_collection(table_name)
    collection.create_index([("geometry", GEOSPHERE)])

    if if_exists == 'replace':
        collection.drop()

    collection.insert_many(geodict)


def read_point_mongodb(table_name, column_list=('geometry', 'DTYPE', 'Age',
                                                'Quality', 'Gender', 'First Name', 'Last Name',
                                                'Timestamp', 'PersonID')):
    results = []
    for v in db.gis.get_collection(table_name).find():
        data = {k: v[k] for k in column_list}
        results.append(data)

    gdf = gpd.GeoDataFrame(results)
    if gdf.empty:
        raise ValueError

    gdf['geometry'] = gdf['geometry'].apply(lambda x: Point(x['coordinates']))
    gdf.set_geometry('geometry', inplace=True)
    gdf.set_crs(epsg=4326, inplace=True)

    return gdf


def read_line_mongodb(table_name, column_list=('osmid', 'name', 'length', 'geometry')):
    results = []
    for v in db.gis.get_collection(table_name).find():
        data = {k: v[k] for k in column_list}
        results.append(data)

    gdf = gpd.GeoDataFrame(results)
    if gdf.empty:
        raise ValueError

    gdf['geometry'] = gdf['geometry'].apply(lambda x: LineString(x['coordinates']))
    gdf.set_geometry('geometry', inplace=True)
    gdf.set_crs(epsg=4326, inplace=True)

    return gdf


def delete_mongodb(table_name):
    db.gis.get_collection(table_name).drop()


if __name__ == '__main__':
    # app
    dummy = DummyDataManipulator()
    puller = DataStore()

    print("Finished")
