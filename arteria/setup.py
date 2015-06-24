from setuptools import setup
from arteria import __version__
from arteria import __requirements__
import os

print "You're installing version %s" %  __version__
print "Your package's requirements are %s" %  __requirements__ 

def read_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='arteria',
    version=__version__,
    description="Main python library for arteria",
    long_description=read_file('README'),
    keywords='bioinformatics',
    author='SNP&SEQ Technology Platform, Uppsala University',
    packages=['arteria'],
    include_package_data=True,
    install_requires=__requirements__,
)
