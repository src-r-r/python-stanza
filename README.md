# Stanza

Convert a pip-based project to to pyproject.toml

This used to be what dephell used to do so well, but the project is since archived.

Features of stanza:

- Parses a list of requirements.txt file (similar to `poetry add`)
- Detects `setup.py` file and includes project info
- Separate **dev** dependencies from **non-dev** dependencies.
- Importing multiple requirements.
- Include sub-requirements (e.g. `-r ./requirements/base.txt`).
# Installation

If you don't use `pipsi`, you're missing out.
Here are [installation instructions](https://github.com/mitsuhiko/pipsi#readme).

Simply run:

    $ pipsi install .

Or use your favorite installation method (feel free to add it as a PR!)
# Usage

To use it:

    $ stanza --help

```
Usage: stanza [OPTIONS] [PATH]

  Convert requirements.txt to pyproject.toml

Options:
  -R, --dev-requirements PATH  file paths to requirements.txt that include
                               development requirements; many can be specified
  -r, --requirements PATH      file paths to requirements.txt that include
                               normal requirements; many can be specified
  -n, --name TEXT              name of the project (will normally be detected
                               automatically)
  -v, --version TEXT           version of the project (will normally be
                               detected automatically)
  --help                       Show this message and exit.
```
