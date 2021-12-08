import re
from typing import Iterable, Optional, AnyStr
from pathlib import Path
from configparser import ConfigParser
import requirements
from poetry.core.packages import Requirement, Dependency
from poetry.core.toml import TOMLFile
from poetry.poetry import ProjectPackage, Poetry
from poetry.console.commands.init import InitCommand
from poetry.layouts import Layout

import logging
log = logging.getLogger(__name__)

RE_REPL_SETUP = re.compile(r"^setup\(", re.MULTILINE).sub

class Converter:

    SETUP_REPLACEMENT = "_setup_kwargs = dict("

    def __init__(self, base_dir=Path(".").resolve()):
        self.project : ProjectPackage = None
        self.base_dir = base_dir
        self.dependencies = []
        self.dev_dependencies = []
        self._setup_data = {}
    
    def parse_setup_py(self, setup_path : Path):
        setup_code = setup_path.read_text()
        setup_code = RE_REPL_SETUP(setup_code, self.SETUP_REPLACEMENT)
        exec(setup_code)
        self._setup_data = _setup_kwargs
        self.project = ProjectPackage(setup["name"], setup["version"])

    def add_dependencies(self, req_file : Path, is_dev=False):
        for req in requirements.parse(str(req_file)):
            dep = Dependency(req.name, req.extras, optional=optional)
            if is_dev:
                self.dev_dependencies.append(dep)
            else:
                self.dependencies.append(dep)
    
    def set_project_by_defaults(self, name=None, version="0.1.0"):
        default_name = self.base_dir.name
        name = name or default_name
        self.project = ProjectPackage(name, version)

    @property
    def layout_author(self):
        if not self._setup_data:
            return None
        return f"{self._setup_data['author']} <{self._setup_data['author_email']}>"
    
    def dump_to_pyproject_toml(self):
        if not self.project:
            raise RuntimeError("No project specified.")
        
        layout_kwargs = {
            "dependencies": self.dependencies,
            "dev_dependencies": self.dev_dependencies,
        }
        
        if self._setup_data:
            layout_kwargs.update({
                "version": self._setup_data["version"],
                "description": self._setup_data["description"],
                "author": self.layout_author,
                "license": self._setup_data["license"],
            })
        layout = Layout(project, **layout_kwargs)
        
        layout.create(self.base_dir)

def convert_command(dependencies : Iterable[Path], dev_dependencies : Iterable[Path], base_dir=Path(".").resolve(), name : Optional[AnyStr]=None, version="0.1.0"):
    converter = Converter(base_dir)
    default_name = name or base_dir.name

    for depfile in dependencies:
        log.info("Adding dependencies from %s", depfile.resolve())
        converter.add_dependencies(depfile)
    for depfile in dev_dependencies:
        log.info("Adding [dev] dependencies from %s", depfile.resolve())
        converter.add_dependencies(depfile)
    try:
        converter.parse_setup_py(setup_path)
    except OSError as err:
        log.warn("No `setup.py` in path %s", base_dir)
    if not converter.project:
        log.warn("Setting project name as '%s' and version '%s'", name, version)
        log.warn("If this is not what you want, specify the --name and --version flags.")
        converter.set_project_by_defaults(name=name, version=version)
    
    log.info("Generating pyproject.toml file in %s", base_dir)
    converter.dump_to_pyproject_toml()