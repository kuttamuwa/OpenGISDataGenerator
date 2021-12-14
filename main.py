"""
Dummy Location Generator

Dependency: OSM (osmnx)

Purpose: Collects

@Author: Umut Ucok, 2021

"""
import os.path

import click

from dummygen.data_generator import DummyDataManipulator
from dummygen.data_puller import DataStore


@click.command()
@click.option('-c', '--config', help='Please inspect README.md and .toml file',
              prompt='Input your config file or we will use default', type=click.Path(),
              default="")
def app(config):
    click.echo(click.format_filename(config))
    with open('settings.toml', 'w') as writer:
        writer.truncate()
        if config != "":
            # file check
            if not os.path.exists(config):
                raise FileNotFoundError("We cannot access to config !")

            click.echo("We are using custom config !")
            writer.writelines(click.open_file(config).readlines())
        else:
            click.echo("We are using default config !")
            writer.writelines(click.open_file('defaultsettings.toml').readlines())

        writer.close()

    # app
    dummy = DummyDataManipulator()
    puller = DataStore()

    print("Finished")
    return dummy, puller


if __name__ == '__main__':
    dummy, puller = app()
