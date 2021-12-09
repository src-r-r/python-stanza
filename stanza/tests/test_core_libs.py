from typing import Iterable, AnyStr
from pathlib import Path
from poetry.core.packages import Dependency
from pkg_resources import Requirement

from stanza.lib.core import Converter, convert_command
from stanza.lib.parser import get_requirements

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
SETUP_PATH = ASSETS / "setup.py"
REQ = ASSETS / "requirements"
REQ_BASE = REQ / "base.txt"
REQ_LOCAL = REQ / "local.txt"
REQ_PROD = REQ / "production.txt"
SWAP_SETUP = SETUP_PATH.parent / ("swp-" + str(SETUP_PATH.name))

def is_in_deplist(name : AnyStr, deplist : Iterable[Dependency]):
    return any([
        name == dep.name for dep in deplist
    ])

def is_in_req_list(name : AnyStr, deplist : Iterable[Requirement]):
    return any([
        name == dep.name for dep in deplist
    ])

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