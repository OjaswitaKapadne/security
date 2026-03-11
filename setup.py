'''
The setup.py is an essential part of packaging & distributing python objects & projects. 
It is used by setup tools(or disutils om older python version) to define the configuration 
of your projects, such as metadatas, dependencies & more...
'''

from setuptools import find_packages, setup
from typing import List

def get_requirements() -> List[str]:
    """
    This function will return list of requirements
    """

    requirement_lst: List[str] = []

    try:
        with open('requirements.txt', 'r') as file:
            ## Read files from the file
            lines = file.readlines()

            for line in lines:
                requirement = line.strip()
                ## Ignore empty lines & -e .

                if requirement and requirement!= '-e .':
                    requirement_lst.append(requirement)


    except FileNotFoundError:
        print("requirements.txt file not found!")

    return requirement_lst


setup(
    name = "NetworkSecurity",
    version="0.0.1",
    author="OjaswitaKapadne",
    author_email="ojaswitakapadne1010@gmail.com",
    packages=find_packages(),
    install_requires=get_requirements()
)

