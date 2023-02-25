from setuptools import setup, find_packages

setup(
    name='filesocket_server',
    packages=['filesocket_server'] + ['filesocket_server.' + pkg for pkg in find_packages('filesocket_server')],
    version='0.1.0',
    description='Server for filesocket',
    author='Mikhail Ivanov',
    author_email='qolorer@gmail.com',
    url='https://github.com/Qolorerr/FileSocketServer',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'quart>=0.18.0',
        'quart-schema>=0.12.0',
        'sqlalchemy>=1.4.39',
        'sqlalchemy-serializer>=1.4.1',
        'cryptography>=39.0.0'
    ],
)
