#!/usr/bin/env python3

import argparse

import os
import tempfile
import subprocess
import shutil

import json
import requests


def gh_sync_forks():
    args = parse_args()

    forks_url = 'https://api.github.com/orgs/{org}/repos?type=forks&access_token={access_token}'.format(org=args.org, access_token=args.token)
    forks_response = requests.get(forks_url)
    forks = json.loads(forks_response.text)

    for fork in forks:
        gh_sync_fork(args, fork)


def parse_args():
    parser = argparse.ArgumentParser(description='Sync forks of a GitHub organization')

    parser.add_argument('org', help='a GitHub organization name from which forks will be synced')
    parser.add_argument('--token', help='a GitHub access token')

    args = parser.parse_args()

    return args


def gh_sync_fork(args, fork):
    fork_name = fork['name']

    repository_url = 'https://api.github.com/repos/{org}/{name}?access_token={access_token}'.format(org=args.org, name=fork_name, access_token=args.token)
    repository_response = requests.get(repository_url)
    repository = json.loads(repository_response.text)

    path = os.path.join(tempfile.gettempdir(), fork_name)

    if os.path.isdir(path):
        try:
            git_update_fork(repository)
        except:
            shutil.rmtree(path)
            git_create_fork(repository)
    else:
        git_create_fork(repository)


def git_create_fork(repository):
    git_clone_repository(repository)
    git_add_upstream(repository)

    git_update_fork(repository)


def git_clone_repository(repository):
    command = 'git clone {ssh_url}'.format(ssh_url=repository['ssh_url'])

    return subprocess.run(command, cwd=tempfile.gettempdir(), shell=True, check=True)


def git_update_fork(repository):
    git_fetch_upstream(repository)
    git_checkout_master(repository)
    git_merge_upstream(repository)


def git_add_upstream(repository):
    original_owner = repository['parent']['owner']['login']
    original_repository = repository['parent']['name']
    upstream_url = 'https://github.com/{original_owner}/{original_repository}.git'.format(original_owner=original_owner, original_repository=original_repository)

    name = repository['parent']['name']

    command = 'git remote add upstream {upstream_url}'.format(upstream_url=upstream_url)

    return subprocess.run(command, cwd=os.path.join(tempfile.gettempdir(), name), shell=True, check=True)


def git_fetch_upstream(repository):
    name = repository['parent']['name']

    command = 'git fetch upstream'

    return subprocess.run(command, cwd=os.path.join(tempfile.gettempdir(), name), shell=True, check=True)


def git_checkout_master(repository):
    default_branch = repository['parent']['default_branch']

    name = repository['parent']['name']

    command = 'git checkout {default_branch}'.format(default_branch=default_branch)

    return subprocess.run(command, cwd=os.path.join(tempfile.gettempdir(), name), shell=True, check=True)


def git_merge_upstream(repository):
    name = repository['parent']['name']

    command = 'git merge upstream/master'

    return subprocess.run(command, cwd=os.path.join(tempfile.gettempdir(), name), shell=True, check=True)


if __name__ == '__main__':
    gh_sync_forks()
