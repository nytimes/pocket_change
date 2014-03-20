from setuptools import setup, find_packages

setup(name='pocket_change',
      version='0.0.0',
      packages=find_packages(),
      install_requires=['sneeze',
                        'Flask',
                        'Flask-RESTful',
                        'Flask-SQLAlchemy',
                        'passlib'])