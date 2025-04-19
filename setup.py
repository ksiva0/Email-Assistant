# content of setup.py for making it a installable package

from setuptools import setup, find_packages

setup(
    name='email_processor',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
        'python-dotenv',
        'flask',
        'slack_sdk',
    ],
    entry_points={
        'console_scripts': [
            'run_app=src.main:main',
        ],
    },
)
