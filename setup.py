from setuptools import setup, find_packages

setup(
    name="content",
    version="0.1",
    packages=find_packages(include=["content*"]),
    package_dir={"": "."},  # Ищем пакеты в корне
)
