import setuptools
from distutils.core import setup


setup(
    name='Django ReDo',
    version='0.2',
    packages=setuptools.find_packages(),
    url='https://github.com/duverse/django-redo',
    license='General Public License v3.0',
    description='Easy to use django-redis asynchronous task manager.',
    long_description=open('README.md').read(),
    requires=[
        'redis',
        'django'
    ],
    long_description_content_type="text/markdown",
    classifiers=[
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
    ]
)
