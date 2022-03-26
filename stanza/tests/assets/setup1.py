import os
from setuptools import setup


# with open(os.getenv('REQUIREMENTS_IN', 'requirements.in')) as f:
#     requirements = [
#         req.rsplit('#egg=', 1)[1] if req.startswith('-e') else req
#         for req in f.read().splitlines()]


setup(
    name='stanza',
    version='0.1',
    packages=['cuthbert'],
    # install_requires=requirements,
)
