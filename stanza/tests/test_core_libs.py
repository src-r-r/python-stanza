from typing import Iterable, AnyStr
from pathlib import Path
from poetry.core.packages import Dependency
from poetry.core.packages.project_package import ProjectPackage
from pkg_resources import Requirement
import re
import pytest
from stanza.lib.core import (
    Converter,
    convert_command,
    fetch_latest_version,
    fetch_latest_version_for,
)
from stanza.lib.parser import get_requirements
import logging

log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
SETUP_PATH = ASSETS / "setup.py"
REQ = ASSETS / "requirements"
REQ_BASE = REQ / "base.txt"
REQ_LOCAL = REQ / "local.txt"
REQ_PROD = REQ / "production.txt"
SWAP_SETUP = SETUP_PATH.parent / ("swp-" + str(SETUP_PATH.name))

def pkg_version(package) -> re.Pattern:
    return re.compile(r'%s = "[_\d\-\.\w]+"' % package)

def assertAnyVersionIn(package : AnyStr, string : AnyStr):
    if not pkg_version(package).findall(string):
        raise AttributeError("Could not find package %s of any version in '%s'", package, string)


def is_in_deplist(name: AnyStr, deplist: Iterable[Dependency]):
    return any([name == dep.name for dep in deplist])


def is_in_req_list(name: AnyStr, deplist: Iterable[Requirement]):
    return any([name == dep.name for dep in deplist])


def test_create_new_converter():
    converter = Converter()
    assert converter.project is None
    assert converter.base_dir is not None


def test_prase_setup_py():
    converter = Converter(ASSETS)
    converter.parse_setup_py(SETUP_PATH)
    assert converter.project is not None
    assert not SWAP_SETUP.exists()


def test_parse_requirements():
    base_reqs = [i for i in get_requirements(REQ_BASE)]
    assert is_in_req_list("pytz", base_reqs)


def test_parse_requirements_with_inclusion():
    prod_reqs = [i for i in get_requirements(REQ_PROD)]
    assert is_in_req_list("pytz", prod_reqs)


def test_add_dependencies():
    converter = Converter(ASSETS)
    converter.add_dependencies(REQ_BASE)
    converter.add_dependencies(REQ_PROD)
    converter.add_dependencies(REQ_LOCAL, True)

    assert is_in_deplist("pytz", converter.dependencies)
    assert is_in_deplist("pytest-sugar", converter.dev_dependencies)
    assert is_in_req_list("psycopg2", converter.dependencies)


def test_dump_to_pyproject_toml():
    converter = Converter(ASSETS)
    converter.add_dependencies(REQ_BASE)
    converter.add_dependencies(REQ_PROD)
    converter.add_dependencies(REQ_LOCAL, True)
    converter.parse_setup_py(SETUP_PATH)

    content = converter.get_toml_content()
    assert 'name = "stanza"' in content


""" NOTE: this test is bound to need updating because packages keep changing.
"""


def test_fetch_latest_version():
    pkgname = "pytest"
    dep = Dependency("pytest", "*")
    log.debug("Created dependency %s", dep)
    new_deps = [d for d in fetch_latest_version([dep])]
    assert new_deps[0].version == "7.1.1"
    assert new_deps[0].name == "pytest"


def test_fetch_latest_version_with_extras():
    pkgname = "pytest"
    version = "2.0.0"
    dep = Dependency("pytest", version)
    log.debug("Created dependency %s", dep)
    new_deps = [d for d in fetch_latest_version([dep])]
    assert new_deps[0].version == "2.0.0"
    assert new_deps[0].name == "pytest"


def test_write_layout_to_file():
    pkgname = "pytest"
    dep = fetch_latest_version_for(Dependency("pytest", "*"))
    log.debug("Created dependency %s", dep)
    converter = Converter()
    converter.dependencies = [dep]
    converter.project = ProjectPackage("testproject", "1.0.0")
    toml_content = converter.get_toml_content()
    assertAnyVersionIn('pytest', toml_content)
