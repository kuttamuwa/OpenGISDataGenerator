import ast
import random
import warnings
from datetime import datetime
from datetime import timedelta

import geopandas as gpd
import osmnx as ox
import pandas as pd
from shapely.geometry import Point, LineString, Polygon

from config import settings
from db.connector import db, if_exists
from dummygen.data_generator import DummyDataManipulator
from errors.configerr import OSMNXMustbeTrue

loc_settings = settings.LOCATION_SETTINGS
poi_settings = settings.POI_SETTINGS
osm_settings = settings.OSM_SETTINGS

static_settings = settings.STATIC_POINTS
dynamic_settings = settings.DYNAMIC_POINTS
recursive_settings = settings.RECURSIVE_POINTS

date_settings = settings.DATE_SETTINGS

ox.config(use_cache=True, log_console=True,
          # default_crs=DUMMY_SETTINGS.crs
          )


class DataStore:
    """
    POIleri çekeceğiz -> osmnx
    Lineları çekeceğiz -> osmnx

    POI'lere buffer at
    POI'ler ile müşterilere intersection, contains, within yapalım

    """
    graph = None

    crs = loc_settings.crs
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

    @classmethod
    def download_graph(cls, network_type='all_private'):
        """
       Downloads OSM Data and generate random points as pandas DataFrame
       :return:
        """
        try:
            if cls.graph is None and cls.use_osmnx is True:
                print("Loading graph..")
                if cls.address:
                    G = ox.graph_from_place(cls.address, network_type=network_type)
                else:
                    raise ValueError('bbox veya adres parametresi doldurulmalıdır')

                print("Graph is created. Now projecting..")
                G = ox.project_graph(G, to_crs=cls.crs)
                cls.graph = G
                print("Graph is loaded.")
            else:
                print("Graph is already loaded or not going to use !")
        except ConnectionError:
            raise ConnectionError("Internet bağlantınızı kontrol ediniz !")

    @classmethod
    def init_routing(cls):
        cls.graph = ox.speed.add_edge_speeds(cls.graph)
        cls.graph = ox.speed.add_edge_travel_times(cls.graph)

    def __init__(self):
        self.points = None
        self.lines = None
        self.pois = None

        # load data
        self.load()

    def load(self):
        self.download_graph()
        self._load_lines()
        self._load_points()
        self._load_poi()

    def download_lines(self, save=True, set=True):
        """
        Get lines from osmnx
        :return:
        """
        if self.lines is None:
            if self.graph is None:
                raise OSMNXMustbeTrue("OSMNX set cannot be False if there is no data ! ")

            print("Lines are downloading..")
            lines = ox.graph_to_gdfs(self.graph, nodes=False)
            lines.drop(columns=[i for i in lines.columns if i not in ('geometry', 'osmid', 'length', 'name')],
                       inplace=True)
            lines.drop_duplicates('geometry', inplace=True)

            if set:
                self.lines = lines

            if save:
                self._save_lines()

            return lines

    def generate_points(self):
        print("Generating")
        if static_settings.run == 1:
            self.static_points()

        if recursive_settings.run == 1:
            self.recursive_points()

        # different places
        if dynamic_settings.run == 1:
            self.dynamic_points()

        print("Generated points !")

    def recursive_points(self):
        print("Recursive points are generating..")
        repeated_times = recursive_settings.repeated_times
        sample_count = recursive_settings.recursive_sample

        # while repeated_times > 0:
        self.generate_recursive_points(sample_count=sample_count, repeated_times=repeated_times)
        print(f"Recursive Points are generated, \n "
              f"Length of all points : {len(self.points)}")
        # repeated_times += -1
        # print(f"Recursive last : {repeated_times}")

        self._save_points()
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

    def generate_random_points_osmnx(self):
        Gp = ox.project_graph(self.graph, to_crs=self.crs)
        random_points = ox.utils_geo.sample_points(ox.get_undirected(Gp), self.count)
        random_points = gpd.GeoDataFrame(random_points)
        random_points.rename(columns={0: 'geometry'}, inplace=True)
        random_points.set_geometry('geometry', inplace=True)

        return random_points

    def generate_random_points_in_area(self, save=True, set=True, add_dummy=True) -> gpd.GeoDataFrame:
        """
        Downloads OSM Data and generate random points snapped to roads as pandas DataFrame
        :return:
        """

        if self.use_osmnx is True:
            print("Generating points with osmnx")
            random_points = self.generate_random_points_osmnx()
        else:
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

    def download_poi(self):
        """
        Downloads POI
        :return:
        """
        print("Downloading POI")
        print(f"poi tags : {self.poi_tags}")
        poi_gdf = ox.geometries_from_point(self.poi_center, tags=self.poi_tags, dist=self.poi_buffer_distance)

        # projection
        poi_gdf.to_crs(crs=self.crs, inplace=True)

        if poi_gdf.empty:
            warnings.warn("There is no downloaded POI around your center ! "
                          "Please set another poi_center ! ")

        else:
            print(f"Downloaded poi : {poi_gdf.head(5)} \n"
                  f"Length : {len(poi_gdf)}")

            if self.pois is not None:
                print("POIs are adding..")
                self.pois = self.pois.append(poi_gdf)
                remained_columns = self.pois.columns
            else:
                self.pois = poi_gdf
                remained_columns = poi_gdf.columns

            # filtering
            remained_columns = [i for i in remained_columns if i not in ('geometry', 'name')]
            self.pois.drop(columns=remained_columns, inplace=True)

            # drop duplicates
            self.pois.drop_duplicates('geometry', inplace=True)

            self._save_pois()

    def _load_lines(self):
        print("Lines are loading..")
        try:
            self.lines = self.read_line_mongodb('lines', )
        except ValueError:
            warnings.warn(f"Lines are downloading..")
            self.download_lines(save=True, set=True)

    def _load_points(self):
        print("Points are loading..")
        if self.reload_data:
            print("Reloading.. ")
            self.delete_mongodb('points')
            self.generate_points()
        else:
            print("No reload !")
            try:
                self.points = self.read_point_mongodb('points')
                print("Generated points will be appended !")
                self.generate_points()

            except ValueError:
                warnings.warn(f"Points are generating..")
                self.generate_points()

    def _load_poi(self):
        """
        POI
        :return:
        """
        print("POIs are loading..")
        try:
            if self.pois is None:
                self.pois = self.read_point_mongodb('pois', ('name', 'geometry'))
                self.download_poi()
        except ValueError:
            warnings.warn(f"Couldn't read POIS table")
            self.download_poi()

    def _save_points(self, replace=False):
        self.points['ROWID'] = [i for i in range(len(self.points))]
        if replace:
            self.delete_mongodb('points')
            self.point_write_mongodb(self.points, 'points')
        else:
            self.point_write_mongodb(self.points, 'points')
        print("Points are saved")

    @classmethod
    def get_point_counts(cls):
        return db.gis.point.count_documents({})

    def _save_lines(self):
        self.line_write_mongodb(self.lines, 'lines')
        print("Lines are saved.")

    def _save_pois(self):
        self.pois_write_mongodb(self.pois, 'pois')
        print("POIs are saved")

    # Mongodb
    # writing
    @staticmethod
    def point_write_mongodb(gdf, table_name):
        geodict = gdf.to_dict(orient='records')
        for i in geodict:
            v = i['geometry']
            i['geometry'] = [v.x, v.y]
            i['PersonID'] = str(i['PersonID'])

        # date to str
        if 'Timestamp' in gdf.columns:
            gdf.Timestamp = gdf.Timestamp.astype(str)

        if if_exists == 'replace':
            db.gis.get_collection(table_name).drop()

        db.gis.get_collection(table_name).insert_many(geodict)

    def pois_write_mongodb(self, gdf, table_name):
        gdf['polygon'] = gdf.geometry.apply(lambda x: True if isinstance(x, Polygon) else False)
        gdf_point = gdf[gdf['polygon'] == False]
        gdf_polygon = gdf[gdf['polygon']]

        self.point_write_mongodb(gdf_point, table_name)
        self.polygon_write_mongodb(gdf_polygon, f'{table_name}_polygon')

    @staticmethod
    def polygon_write_mongodb(gdf, table_name):
        pass
        # todo:
        # geodict = gdf.to_dict(orient='records')
        # for i in geodict:
        #     i['geometry'] = None
        #
        # if if_exists == 'replace':
        #     db.gis.get_collection(table_name).drop()
        #
        # db.gis.get_collection(table_name).insert_many(geodict)

    @staticmethod
    def line_write_mongodb(gdf, table_name):
        geodict = gdf.to_dict(orient='records')
        for i in geodict:
            i['geometry'] = i['geometry'] = gdf.geometry.__geo_interface__['features']

        if if_exists == 'replace':
            db.gis.get_collection(table_name).drop()

        db.gis.get_collection(table_name).insert_many(geodict)

    # reading
    @staticmethod
    def read_point_mongodb(table_name, column_list=('geometry', 'DTYPE', 'Age',
                                                    'Quality', 'Gender', 'First Name', 'Last Name',
                                                    'Timestamp', 'PersonID', 'ROWID')):
        results = []
        for v in db.gis.get_collection(table_name).find():
            data = {k: v[k] for k in column_list}
            results.append(data)

        gdf = gpd.GeoDataFrame(results)
        if gdf.empty:
            raise ValueError

        gdf.rename(columns={"coordinates": "geometry"}, inplace=True)
        geometries = [Point(i) for i in gdf['geometry']]
        gdf['geometry'] = geometries
        gdf.set_geometry('geometry', inplace=True)

        return gdf

    @staticmethod
    def read_line_mongodb(table_name, column_list=('osmid', 'name', 'length', 'geometry')):
        results = []
        for v in db.gis.get_collection(table_name).find():
            data = {k: v[k] for k in column_list}
            results.append(data)

        gdf = gpd.GeoDataFrame(results)
        if gdf.empty:
            raise ValueError

        gdf.rename(columns={"coordinates": "geometry"}, inplace=True)
        geometries = [LineString(i) for i in gdf['geometry']]
        gdf['geometry'] = geometries
        gdf.set_geometry('geometry', inplace=True)

        return gdf

    # delete
    @staticmethod
    def delete_mongodb(table_name):
        db.gis.get_collection(table_name).drop()

# if __name__ == '__main__':
# from config import settings
# from sqlalchemy import create_engine
# from pymongo import MongoClient
# import geopandas as gpd
#
# dbconf = settings.DB
# points_table_name = dbconf.points_table_name
# lines_table_name = dbconf.lines_table_name
# if_exists = dbconf.if_exists
# conn_string = f"postgresql+psycopg2://{dbconf.username}:{dbconf.password}@{dbconf.host}:{dbconf.port}/{dbconf.db}"
# db = create_engine(conn_string)
# pydb = MongoClient()
#
# gdf_point = gpd.read_postgis('select * from points', con=db, geom_col='geometry')
# gdf_lines = gpd.read_postgis('select * from lines', con=db, geom_col='geometry')
# gdf_pois = gpd.read_postgis('select * from pois', con=db, geom_col='geometry')
#
# gdf_point.Timestamp = gdf_point.Timestamp.astype(str)
#
# gdf_point.rename(columns={"geometry": "coordinates"}, inplace=True)
# gdf_lines.rename(columns={"geometry": "coordinates"}, inplace=True)
# gdf_pois.rename(columns={"geometry": "coordinates"}, inplace=True)

# write them once
# point_write(gdf_point, 'point')
# point_write(gdf_lines, 'lines')
# point_write(gdf_pois, 'pois')


# write old data
# point_write_mongodb(gdf_point, 'point')

# read them
# gdf_point_in = read_point_mongodb('point', gdf_point.columns)
# gdf_lines_in = read_point_mongodb('point', gdf_lines.columns)
# gdf_pois_in = read_point_mongodb('point', gdf_pois.columns)
