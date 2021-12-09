# Stanza

Convert a pip-based project to to pypoetry.toml

This used to be what dephell used to do so well, but the project is since archived.
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

  Convert requirements.txt to pypoetry.toml

Options:
  -R, --dev-requirements PATH
  -r, --requirements PATH
  -n, --name TEXT
  -v, --version TEXT
  --help                       Show this message and exit.
```