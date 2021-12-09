import re
import os
from typing import Iterable, Optional, AnyStr
from pathlib import Path
from configparser import ConfigParser
import requirements
from poetry.core.packages import Requirement, Dependency
from poetry.core.toml import TOMLFile
from poetry.poetry import ProjectPackage, Poetry
from poetry.console.commands.init import InitCommand
from poetry.layouts import Layout
import importlib.machinery
import importlib.util
from copy import deepcopy
from stanza.lib.parser import get_requirements

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
    
    def _copy_and_get_setup_data(self, setup_path : Path):
        """ While this could be done with eval, that's a bit dangerous.

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
        spec = importlib.util.spec_from_loader( 'swap_setup', loader)
        swap_setup_module = importlib.util.module_from_spec( spec )
        loader.exec_module( swap_setup_module )
        swap_setup = deepcopy(swap_setup_module._setup_kwargs)
        del swap_setup_module
        del spec
        del loader
        # Delete the original file.
        os.remove(str(swap_path))
        return swap_setup

    
    def parse_setup_py(self, setup_path : Path):
        self._setup_data = self._copy_and_get_setup_data(setup_path)
        setup = self._setup_data
        self.project = ProjectPackage(setup["name"], setup["version"])

    def add_dependencies(self, req_file : Path, is_dev=False):
        for req in get_requirements(req_file):
            extras = ''
            if req.extras:
                extras = extras
            if extras:
                import ipdb; ipdb.set_trace()
            dep = Dependency(req.name, constraint=extras)
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
        """ Convenience property to format the project author in proper format.

        Will be None of _setup_data is None
        """
        if not self._setup_data:
            return None
        return f"{self._setup_data['author']} <{self._setup_data['author_email']}>"
    
    def dump_to_pyproject_toml(self, base_dir=None):

        base_dir = base_dir or self.base_dir

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

        content = layout.generate_poetry_content()

        import ipdb; ipdb.set_trace()
        
        layout.create(base_dir)

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