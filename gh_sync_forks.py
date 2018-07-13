#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import tempfile

import requests


def gh_sync_forks():
    args = parse_args()

    template = 'https://api.github.com/orgs/{org}/repos?type=forks&access_token={access_token}'
    url = template.format(org=args.org, access_token=args.token)
    response = requests.get(url)
    forks = json.loads(response.text)

    for fork in forks:
        gh_sync_fork(args, fork)


def parse_args():
    directory = tempfile.gettempdir()

    parser = argparse.ArgumentParser(description='Sync forks of a GitHub organization')

    parser.add_argument('org', help='a GitHub organization name from which forks will be synced')
    parser.add_argument('--token', help='a GitHub access token to work around default rate limit')
    parser.add_argument('--directory', help='a local directory in which repositories will be cloned (default: [{directory}])'.format(directory=directory), default=directory)

    args = parser.parse_args()

    if os.path.isfile(args.directory):
        os.remove(args.directory)

    if not os.path.isdir(args.directory):
        os.mkdir(args.directory)

    return args


def gh_sync_fork(args, fork):
    name = fork['name']

    template = 'https://api.github.com/repos/{org}/{name}?access_token={access_token}'
    url = template.format(org=args.org, name=name, access_token=args.token)
    response = requests.get(url)
    repository = json.loads(response.text)

    directory = args.directory

    path = resolve_repository_directory(directory, name)

    if os.path.isfile(path):
        os.remove(path)

    if os.path.isdir(path):
        try:
            git_update_fork(directory, repository)
        except subprocess.CalledProcessError:
            shutil.rmtree(path)
            git_create_fork(directory, repository)
            git_update_fork(directory, repository)

    else:
        git_create_fork(directory, repository)
        git_update_fork(directory, repository)


def git_create_fork(directory, repository):
    git_clone_repository(directory, repository)
    git_add_upstream(directory, repository)


def git_clone_repository(directory, repository):
    command = 'git clone {ssh_url}'.format(ssh_url=repository['ssh_url'])

    return subprocess.run(command, cwd=directory, shell=True, check=True)


def git_add_upstream(directory, repository):
    original_owner = repository['parent']['owner']['login']
    original_repository = repository['parent']['name']

    template = 'https://github.com/{original_owner}/{original_repository}.git'
    url = template.format(original_owner=original_owner, original_repository=original_repository)

    name = repository['parent']['name']

    command = 'git remote add upstream {upstream_url}'.format(upstream_url=url)

    return subprocess.run(command, cwd=resolve_repository_directory(directory, name), shell=True, check=True)


def git_update_fork(directory, repository):
    git_fetch_upstream(directory, repository)
    git_checkout(directory, repository)
    git_merge_upstream(directory, repository)
    git_push(directory, repository)


def git_fetch_upstream(directory, repository):
    name = repository['parent']['name']

    command = 'git fetch upstream'

    return subprocess.run(command, cwd=resolve_repository_directory(directory, name), shell=True, check=True)


def git_checkout(directory, repository):
    name = repository['parent']['name']
    default_branch = repository['parent']['default_branch']

    command = 'git checkout {default_branch}'.format(default_branch=default_branch)

    return subprocess.run(command, cwd=resolve_repository_directory(directory, name), shell=True, check=True)


def git_merge_upstream(directory, repository):
    name = repository['parent']['name']
    default_branch = repository['parent']['default_branch']

    command = 'git merge upstream/{default_branch}'.format(default_branch=default_branch)

    return subprocess.run(command, cwd=resolve_repository_directory(directory, name), shell=True, check=True)


def git_push(directory, repository):
    name = repository['parent']['name']

    command = 'git push --all && git push --tags'

    return subprocess.run(command, cwd=resolve_repository_directory(directory, name), shell=True, check=True)


def resolve_repository_directory(directory, name):
    return os.path.join(directory, name)


if __name__ == '__main__':
    gh_sync_forks()
