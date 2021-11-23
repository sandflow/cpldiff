import pathlib
from setuptools import setup, find_packages

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='cpldiff', 
    version='1.0.0b1',
    description='Compares the timeline of two IMF Compositions',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/sandflow/cpldiff',
    author='Sandflow Consulting LLC',
    author_email='info@sandflow.com',
    keywords="cpl imf composition diff",

    package_dir={'cpldiff': 'src/main/python/cpldiff'}, 

    packages=find_packages(where='src/main/python'),

    python_requires='>=3.7, <4',

    project_urls={
        'Bug Reports': 'https://github.com/sandflow/cpldiff/issues',
        'Source': 'https://github.com/sandflow/cpldiff',
    },

    entry_points={
        "console_scripts": [
            "tt = cpldiff.cli:main"
        ]
    },
)
