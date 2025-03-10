from setuptools import setup, find_packages

setup(
    name="deploy_box_cli",
    version="0.1.1",
    description="CLI for managing Deploy Box operations",
    author="Jacob Wernke",
    author_email="Wernke.jacob@gmail.com",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pkce",
        "keyring",
        "readchar",
        # Add other dependencies your project uses
    ],
    entry_points={
        'console_scripts': [
            'deploy-box-cli = deploy_box_cli.cli:main',  # Command to run your CLI
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
