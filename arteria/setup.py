from setuptools import setup, find_packages
from arteria import __version__
import os

def read_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='arteria',
    version=__version__,
    description="Helper classes for the arteria project",
    long_description=read_file('README'),
    keywords='bioinformatics',
    author='SNP&SEQ Technology Platform, Uppsala University',
    packages=find_packages(),
    include_package_data=True
)
