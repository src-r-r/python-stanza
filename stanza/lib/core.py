import re
import os
from typing import Iterable, Optional, AnyStr
from pathlib import Path
from configparser import ConfigParser
import requirements
from poetry.repositories.pypi_repository import PyPiRepository
from poetry.core.packages import Requirement, Dependency
from poetry.core.toml import TOMLFile
from poetry.poetry import ProjectPackage, Poetry
from poetry.console.commands.init import InitCommand
from poetry.layouts import Layout
from poetry.core.semver.version_range import VersionRange
import importlib.machinery
import importlib.util
from copy import deepcopy
from stanza.lib.parser import get_requirements

import logging
import logging.config

log = logging.getLogger(__name__)

RE_REPL_SETUP = re.compile(r"^setup\(", re.MULTILINE).sub

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def logdict(stanza_level=logging.WARNING):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": LOG_FORMAT,
            }
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {
                "handlers": ["stdout"],
                "level": stanza_level,
                "propagate": True,
            }
        },
    }


def fetch_latest_version_for(dep: Dependency, repo=PyPiRepository(), force_search=True):
    log.debug("Finding version for %s", dep.name)
    latest = None
    for pkg in repo.find_packages(dep):
        dep.constraint
        if pkg.name != dep.name:
            continue
        if not latest:
            latest = pkg
            continue
        if pkg.version > latest.version:
            latest = pkg
    log.debug("Setting %s's version to %s", dep.name, str(latest.version))
    dep.version = str(latest.version)
    return dep


def fetch_latest_version(
    dependencies: Iterable[Dependency], repo=PyPiRepository(), force_search=False
):
    for dep in dependencies:
        pkg = fetch_latest_version_for(dep, repo, force_search)
        if pkg:
            yield pkg


class Converter:

    SETUP_REPLACEMENT = "_setup_kwargs = dict("

    def __init__(self, base_dir=Path(".").resolve()):
        self.project: ProjectPackage = None
        self.base_dir = base_dir
        self.dependencies: Iterable[Dependency] = []
        self.dev_dependencies: Iterable[Dependency] = []
        self._setup_data = {}

    def _copy_and_get_setup_data(self, setup_path: Path):
        """While this could be done with eval, that's a bit dangerous.

        Instead, let's import the `setup.py`, replacing the `setup` function
        call with a dict assignment. This way we can import the setup keyword
        arguments as a dictionary and pass directly to poetry.

        Return the setup arguments.
        """
        sp = setup_path
        swap_path = sp.parent / f"swp-{sp.name}"
        swap_code = RE_REPL_SETUP(self.SETUP_REPLACEMENT, setup_path.read_text())
        swap_path.write_text(swap_code)
        # Thanks to https://csatlas.com/python-import-file-module/
        loader = importlib.machinery.SourceFileLoader("swap_setup", str(swap_path))
        spec = importlib.util.spec_from_loader("swap_setup", loader)
        swap_setup_module = importlib.util.module_from_spec(spec)
        loader.exec_module(swap_setup_module)
        swap_setup = deepcopy(swap_setup_module._setup_kwargs)
        del swap_setup_module
        del spec
        del loader
        # Delete the original file.
        os.remove(str(swap_path))
        return swap_setup

    def _get_project_module(
        self, base_dir: Path = None
    ) -> importlib.machinery.ModuleSpec:
        """Get the project as a module."""
        base_dir = base_dir or self.base_dir
        module_name = base_dir.name
        loader = importlib.machinery.SourceFileLoader(module_name, str(base_dir))
        spec = importlib.util.spec_from_loader(module_name, loader)
        return importlib.util.module_from_spec(spec)

    def parse_setup_py(self, setup_path: Path):
        self._setup_data = self._copy_and_get_setup_data(setup_path)
        setup = self._setup_data
        self.project = ProjectPackage(setup["name"], setup["version"])

    def add_dependencies(self, req_file: Path, is_dev=False):
        if not isinstance(req_file, Path):
            req_file = Path(req_file).resolve()
        for req in get_requirements(req_file):
            extras = ""
            if req.extras:
                extras = extras
            dep = Dependency(req.name, constraint=extras)
            dep = fetch_latest_version_for(dep)
            if is_dev:
                self.dev_dependencies.append(dep)
            else:
                self.dependencies.append(dep)

    def set_project_by_defaults(self, name=None, version="0.1.0"):
        default_name = self.base_dir.name
        name = name or default_name
        version = version or "0.1.0"
        assert name
        assert version
        self.project = ProjectPackage(name, version)

    @property
    def layout_author(self):
        """Convenience property to format the project author in proper format.

        Will be None of _setup_data is None
        """
        if not self._setup_data:
            return ""
        if not "author" in self._setup_data:
            return ""
        return f"{self._setup_data['author']} <{self._setup_data['author_email']}>"
    
    def _layout_dependency(self, dep : Dependency, is_dev=False):
        c = dep.constraint
        if c and isinstance(c, VersionRange) and c.is_any():
            return (dep.name, str(dep.version))
        return (dep.name, str(dep.constraint))

    @property
    def _layout_kwargs(self):

        layout_kwargs = {
            "dependencies": dict(
                [self._layout_dependency(d) for d in self.dependencies]
            ),
            "dev_dependencies": dict(
                [self._layout_dependency(d, True) for d in self.dev_dependencies]
            ),
        }
        if self._setup_data:
            layout_kwargs.update(
                {
                    "version": self._setup_data.get("version") or "",
                    "description": self._setup_data.get("description") or "",
                    "author": self.layout_author or "",
                    "license": self._setup_data.get("license") or '',
                }
            )
        return layout_kwargs

    def get_toml_content(self, base_dir=None):

        base_dir = base_dir or self.base_dir

        if not self.project:
            raise RuntimeError("No project specified.")

        layout = Layout(self.project.name, **self._layout_kwargs)

        return layout.generate_poetry_content()

    def write_toml(self, base_dir=None):

        base_dir = base_dir or self.base_dir
        content = self.get_toml_content(base_dir)
        (base_dir / "pyproject.toml").write_text(content)


def convert_command(
    dependencies: Iterable[Path],
    dev_dependencies: Iterable[Path],
    base_dir=Path(".").resolve(),
    name: Optional[AnyStr] = None,
    version="0.1.0",
    verbose=False,
):
    if verbose:
        logging.config.dictConfig(logdict(logging.DEBUG))
    else:
        logging.config.dictConfig(logdict(logging.WARNING))
    base_dir = base_dir or Path(".").resolve()
    if not isinstance(base_dir, Path):
        base_dir = Path(base_dir)
    converter = Converter(base_dir)
    default_name = name or base_dir.name
    setup_path = base_dir / "setup.py"

    for depfile in dependencies:
        if not isinstance(depfile, Path):
            depfile = Path(depfile)
        log.info("Adding dependencies from %s", depfile.resolve())
        converter.add_dependencies(depfile)
    for depfile in dev_dependencies:
        if not isinstance(depfile, Path):
            depfile = Path(depfile)
        log.info("Adding [dev] dependencies from %s", depfile.resolve())
        converter.add_dependencies(depfile)
    try:
        converter.parse_setup_py(setup_path)
    except OSError as err:
        log.warn("No `setup.py` in path %s", base_dir)
    if not converter.project:
        log.warn("Setting project name as '%s' and version '%s'", name, version)
        log.warn(
            "If this is not what you want, specify the --name and --version flags."
        )
        converter.set_project_by_defaults(name=name, version=version)

    log.info("Generating pyproject.toml file in %s", base_dir)
    converter.write_toml(base_dir)
