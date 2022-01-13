from typing import AnyStr
from pathlib import Path
import pkg_resources
import re
import logging
from poetry.repositories import pypi_repository
log = logging.getLogger(__name__)

RX_VERSION = re.compile(r'.+(^python_version).+(?P<operator>[\=\>\<]+)\s*(?P<version>.+)$').match

def get_version(line : AnyStr):
    vers = RX_VERSION(line)
    if not vers:
        return tuple()
    return (vers.group("operator"), vers.group("version").strip("'").strip())

def get_requirements(req_path : Path):
    """ Parse a requirements file and return a list of Requirement objects.

    Ignore any comments or blank lines and include any "-r" requirement
    entries.
    """
    with req_path.open() as f:
        for line in f:
            l = line.strip()
            if not l:
                continue
            if l.startswith("#"):
                continue
            if l.startswith("-e"):
                # This is "this project"
                continue
            if l.startswith("-r"):
                try:
                    included = l.replace("-r", "").strip()
                    log.info("reading included file %s", included)
                    if included.startswith("/"):
                        # this is an absolute path
                        for i in get_requirements(included):
                            yield i
                    else:
                        # This is a relative path
                        for i in get_requirements(req_path.parent / included):
                            yield i
                except ValueError as err:
                    raise Exception("Parsing line '%s' : %s", l, err)
            else:
                req = pkg_resources.Requirement.parse(l)
                req.extras = [s.strip() for s in line.split(";")]
                yield req