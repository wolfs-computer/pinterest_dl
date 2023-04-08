#!/usr/bin/env python3

from setuptools import setup

try: # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError: # for pip <= 9.0.3
    from pip.req import parse_requirements


def load_requirements(requirement_list):
    requirements = parse_requirements(requirement_list, session="test")
    return [str(requirement.requirement) for requirement in requirements]


if __name__ == "__main__":

    setup(
        name="pinterest_dl",
        version="1.0",
        description="Programm for downloading pins from Pinterest",
        author="RKR",
        author_email="goowolf.proc@gmail.com",
        packages=["pinterest_dl"],
        install_requires=load_requirements("requirements.txt"),
        entry_points={
            'console_scripts': [
                'pinterest-dl=pinterest_dl:run'
            ]
        },
    )
