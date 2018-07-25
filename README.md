# GitHub Sync Forks

A Python 3 script to sync forks of a GitHub organization.

## Usage

    usage: gh_sync_forks.py [-h] organization access_token target_directory
    
    Sync forks of a GitHub organization
    
    positional arguments:
      organization      a GitHub organization name from which forks will be synced
      access_token      a GitHub access token to work around default rate limit
      target_directory  a local directory in which repositories will be cloned
    
    optional arguments:
      -h, --help        show this help message and exit

## Developers

Conda environment has been created as shown below.

    conda create --no-default-packages -p .conda python=3.7
    source activate .conda
    conda install requests

## Credits

Written by Christophe Bismuth, licensed under the [The MIT License (MIT)](LICENSE.md).
