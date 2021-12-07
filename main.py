"""
Dummy Location Generator

Dependency: OSM (osmnx)

Purpose: Collects

@Author: Umut Ucok, 2021

"""
from dummygen.data_generator import DummyDataManipulator
from dummygen.data_puller import DataStore
import argparse


# agp = argparse.ArgumentParser()
# agp.add_argument('config', help='settings.toml dosyasını yükle')

if __name__ == '__main__':
    dummy = DummyDataManipulator()
    puller = DataStore()
