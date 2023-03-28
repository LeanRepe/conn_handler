from setuptools import find_packages, setup

setup(name='mtcollector', 
      packages=find_packages(include=['mtcollector']), 
      version='0.0.3',
      description='Multithread output collector', 
      author='L. Repetto', 
      author_email='leanrepetto@gmail.com', 
      install_requires=['netmiko']
      )