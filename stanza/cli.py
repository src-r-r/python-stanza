import click
from pathlib import Path
from stanza.lib.core import convert_command


@click.command()
@click.option("-R", "--dev-requirements", multiple=True, type=click.Path())
@click.option("-r", "--requirements", multiple=True, type=click.Path())
@click.option("-n", "--name", default=Path(".").resolve().name)
@click.option("-v", "--version", default="0.1.0")
@click.argument("path", required=False)
def main(dev_requirements, requirements, name, version, path):
    """Convert requirements.txt to pypoetry.toml"""
    convert_command(requirements, dev_requirements, path, name, version)
