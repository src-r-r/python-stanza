import click
from pathlib import Path
from stanza.lib.core import convert_command


@click.command()
@click.option(
    "-R",
    "--dev-requirements",
    multiple=True,
    type=click.Path(),
    help="file paths to requirements.txt that include development requirements; many can be specified",
)
@click.option(
    "-r",
    "--requirements",
    multiple=True,
    type=click.Path(),
    help="file paths to requirements.txt that include normal requirements; many can be specified",
)
@click.option(
    "-n",
    "--name",
    default=Path(".").resolve().name,
    help="name of the project (will normally be detected automatically)",
)
@click.option(
    "-V",
    "--version",
    default="0.1.0",
    help="version of the project (will normally be detected automatically)",
)
@click.option(
    "-v",
    "--verbose",
    help="Make the program talk a lot.",
    is_flag=True,
)
@click.argument(
    "path",
    required=False,
    # help="override the base directory. Default is the current path.",
    default=Path(".").resolve(),
)
def main(dev_requirements, requirements, name, version, path):
    """Convert requirements.txt to pyproject.toml"""
    convert_command(requirements, dev_requirements, path, name, version)
