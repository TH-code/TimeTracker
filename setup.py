from setuptools import setup, find_packages
import os

setup(
    name='timetracker',
    version='0.1',
    author="THijs",
    author_email="t.jonkman@gmail.com",
    description="",
    packages=find_packages(),
    package_dir={'': os.sep.join(['src', 'timetracker'])},
    include_package_data=True,
    install_requires=[
      'bobo',
      'distribute',
    ],
)
