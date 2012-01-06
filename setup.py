from setuptools import setup, find_packages
import sys, os

version = '0.30'

setup(name='Twister',
      version=version,
      description="Twitter Streaming Server",
      long_description="""\
Twitter Streaming Server""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='python twitter',
      author='Jun Kimura',
      author_email='jksmphone@gmail.com',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
