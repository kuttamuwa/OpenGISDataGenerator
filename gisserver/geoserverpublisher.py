from geo.Geoserver import Geoserver

from config import settings
from server.gisserver import BaseGISServer

testgisconfig = settings.testgeoserverconfig
livegisconfig = settings.livegisconfig


class GeoServerPublisher(BaseGISServer):
    def __init__(self):
        super(GeoServerPublisher, self).__init__()

    def create_live_publisher(self):
        self.publisher = Geoserver(
            service_url=livegisconfig.url,
            username=livegisconfig.username,
            password=livegisconfig.password
        )

    def create_test_publisher(self):
        self.publisher = GeoServer(
            service_url=testgisconfig.url,
            username=testgisconfig.username,
            password=testgisconfig.password
        )

    def read_config(self):
        super().read_config()