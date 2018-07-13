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
    parser = argparse.ArgumentParser(description='Sync forks of a GitHub organization')

    parser.add_argument('org', help='a GitHub organization name from which forks will be synced')
    parser.add_argument('--token', help='a GitHub access token to work around default rate limit')

    args = parser.parse_args()

    return args


def gh_sync_fork(args, fork):
    name = fork['name']

    template = 'https://api.github.com/repos/{org}/{name}?access_token={access_token}'
    url = template.format(org=args.org, name=name, access_token=args.token)
    response = requests.get(url)
    repository = json.loads(response.text)

    path = resolve_repository_directory(name)

    if os.path.isfile(path):
        os.remove(path)

    if os.path.isdir(path):
        try:
            git_update_fork(repository)
        except subprocess.CalledProcessError:
            shutil.rmtree(path)
            git_create_fork(repository)
            git_update_fork(repository)

    else:
        git_create_fork(repository)
        git_update_fork(repository)


def git_create_fork(repository):
    git_clone_repository(repository)
    git_add_upstream(repository)


def git_clone_repository(repository):
    command = 'git clone {ssh_url}'.format(ssh_url=repository['ssh_url'])

    return subprocess.run(command, cwd=tempfile.gettempdir(), shell=True, check=True)


def git_add_upstream(repository):
    original_owner = repository['parent']['owner']['login']
    original_repository = repository['parent']['name']

    template = 'https://github.com/{original_owner}/{original_repository}.git'
    url = template.format(original_owner=original_owner, original_repository=original_repository)

    name = repository['parent']['name']

    command = 'git remote add upstream {upstream_url}'.format(upstream_url=url)

    return subprocess.run(command, cwd=resolve_repository_directory(name), shell=True, check=True)


def git_update_fork(repository):
    git_fetch_upstream(repository)
    git_checkout(repository)
    git_merge_upstream(repository)
    git_push(repository)


def git_fetch_upstream(repository):
    name = repository['parent']['name']

    command = 'git fetch upstream'

    return subprocess.run(command, cwd=resolve_repository_directory(name), shell=True, check=True)


def git_checkout(repository):
    name = repository['parent']['name']
    default_branch = repository['parent']['default_branch']

    command = 'git checkout {default_branch}'.format(default_branch=default_branch)

    return subprocess.run(command, cwd=resolve_repository_directory(name), shell=True, check=True)


def git_merge_upstream(repository):
    name = repository['parent']['name']
    default_branch = repository['parent']['default_branch']

    command = 'git merge upstream/{default_branch}'.format(default_branch=default_branch)

    return subprocess.run(command, cwd=resolve_repository_directory(name), shell=True, check=True)


def git_push(repository):
    name = repository['parent']['name']

    command = 'git push --all && git push --tags'

    return subprocess.run(command, cwd=resolve_repository_directory(name), shell=True, check=True)


def resolve_repository_directory(name):
    return os.path.join(tempfile.gettempdir(), name)


if __name__ == '__main__':
    gh_sync_forks()
