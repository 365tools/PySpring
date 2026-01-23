from setuptools import setup, find_packages

setup(
    name="pyspring",
    version="1.1.0b1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
