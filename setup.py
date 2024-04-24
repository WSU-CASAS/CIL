#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

with open('requirements_dev.txt') as req_file:
    requirements = req_file.read()

test_requirements = ['pytest>=3', ]

setup(
    author="Katherine Wuestney",
    author_email='katherineann983@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Package with tools to assist in the qualitative analysis of CASAS smart home data.",
    entry_points={
        'console_scripts': [
            'casas_measures=casas_measures.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='casas_measures',
    name='casas_measures',
    packages=find_packages(include=['casas_measures', 'casas_measures.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/katherine983/casas_measures',
    version='0.1.0',
    zip_safe=False,
)
