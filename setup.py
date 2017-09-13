from setuptools import setup

setup(name='sivepy',
      version='0.1',
      description='Download SIVEP-Malária data',
      url='http://github.com/lecardozo/sivepy',
      author='Lucas Cardozo',
      author_email='lucasecardozo@gmail.com',
      license='MIT',
      packages=['sivepy'],
      install_requires=[
          'bs4',
          'click',
          'htmlparser',
          'pandas',
          'requests',
          'unidecode'
      ],
      zip_safe=False)
