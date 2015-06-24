from setuptools import setup, find_packages
from runfolder import __version__
from runfolder import __requirements__
import os

print "You're installing version %s" %  __version__
print "Your package's requirements are %s" %  __requirements__ 

def read_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='runfolder',
    version=__version__,
    description="Micro-service for managing runfolders",
    long_description=read_file('README'),
    keywords='bioinformatics',
    author='SNP&SEQ Technology Platform, Uppsala University',
    packages=find_packages(),
    include_package_data=True,
    install_requires=__requirements__,
    entry_points={
        'console_scripts': [ 'runfolder-ws = runfolder.runfolder_ws:start' ]
    }
)
