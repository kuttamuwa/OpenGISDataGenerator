"""
Dummy Location Generator

Dependency: OSM (osmnx)

Purpose: Collects

@Author: Umut Ucok, 2021

"""

from dummygen.data_generator import DummyDataManipulator
from dummygen.data_puller import DataStore


if __name__ == '__main__':
    # app
    dummy = DummyDataManipulator()
    puller = DataStore()

    print("Finished")
