import pandas as pd


class BaseGISServer:
    debug = False
    datastore = None
    workspace = None

    def __init__(self):
        self.publisher = None
        self.set_publisher()

    def create_live_publisher(self):
        pass

    def create_test_publisher(self):
        pass

    def set_publisher(self):
        if self.debug:
            self.create_test_publisher()
        else:
            self.create_live_publisher()

    # def read_config(self):
    #     pass

    def publish(self, df: pd.DataFrame, title: str,
                tags: list, folder: str):
        pass
