from setuptools import setup, find_packages
import os

setup(
    name='timelog',
    version='0.1',
    author="THijs",
    author_email="t.jonkman@gmail.com",
    description="",
    packages=find_packages(),
    package_dir={'': os.sep.join(['src', 'timelog'])},
    include_package_data=True,
    install_requires=[
      'bobo',
      'distribute',
    ],
)
