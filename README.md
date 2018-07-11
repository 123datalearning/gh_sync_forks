# GitHub Sync Forks

A simple Python 3 script to sync forks of a given organization.

## Usage

    usage: gh_sync_forks.py [-h] [--token TOKEN] org
    
    Sync forks of a GitHub organization
    
    positional arguments:
      org            a GitHub organization name from which forks will be synced
    
    optional arguments:
      -h, --help     show this help message and exit
      --token TOKEN  a GitHub access token to work around default rate limit

### Note

Remote forks will be cloned into system temporary directory.

## Credits

Written by Christophe Bismuth, licensed under the [The MIT License (MIT)](LICENSE.md).
