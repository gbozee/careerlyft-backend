import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="l_shortner",
    version="0.2",
    packages=['api'],
    include_package_data=True,
    license="MIT License",  # example license
    description="A reusable link shortner microservice",
    long_description=README,
    url="https://www.example.com/",
    author="Biola Oyeniyi",
    author_email="gbozee@gmail.com",
    install_requires=[],
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: X.Y",  # replace "X.Y" as appropriate
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",  # example license
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        # Replace these appropriately if you are stuck on Python 2.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
