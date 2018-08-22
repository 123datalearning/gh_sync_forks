#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess

import requests


def parse_args():
    parser = argparse.ArgumentParser(description='Sync forks of a GitHub organization')

    parser.add_argument('organization', help='a GitHub organization name from which forks will be synced')
    parser.add_argument('access_token', help='a GitHub access token to work around default rate limit')
    parser.add_argument('target_directory', help='a local directory in which repositories will be cloned')

    parser.add_argument("-c", "--clean", help="clean Git repository", action="store_true")
    parser.add_argument("-r", "--reset", help="reset Git repository", action="store_true")

    arguments = parser.parse_args()

    if os.path.isfile(arguments.target_directory):
        os.remove(arguments.target_directory)

    if not os.path.isdir(arguments.target_directory):
        os.mkdir(arguments.target_directory)

    return arguments


class GitHubForkSync:
    def __init__(self, organization, access_token, target_directory, clean, reset):
        self.organization = organization
        self.access_token = access_token
        self.target_directory = target_directory
        self.clean = clean
        self.reset = reset

    def sync_forks_from_page(self, page):
        template = 'https://api.github.com/orgs/{organization}/repos?type=forks&access_token={access_token}&page={page}'
        url = template.format(organization=self.organization, access_token=self.access_token, page=page)

        self.sync_forks_from_url(url)

    def sync_forks_from_url(self, url):
        response = requests.get(url)
        forks = json.loads(response.text)

        for fork in forks:
            self.sync_fork(fork)

        next_url = response.links.get('next', {}).get('url', '')

        if next_url:
            self.sync_forks_from_url(next_url)

    def sync_fork(self, fork):
        name = fork['name']

        template = 'https://api.github.com/repos/{organization}/{name}?access_token={access_token}'
        url = template.format(organization=self.organization, name=name, access_token=self.access_token)
        response = requests.get(url)
        repository = json.loads(response.text)

        print(repository['clone_url'])

        path = self.resolve_repository_directory(name)

        if os.path.isfile(path):
            os.remove(path)

        if os.path.isdir(path):
            try:
                self.git_update_fork(repository)
            except subprocess.CalledProcessError:
                shutil.rmtree(path)
                self.git_create_fork(repository)
                self.git_update_fork(repository)
        else:
            self.git_create_fork(repository)
            self.git_update_fork(repository)

    def git_create_fork(self, repository):
        self.git_clone_repository(repository)
        self.git_add_upstream(repository)

    def git_clone_repository(self, repository):
        command = 'git clone {ssh_url}'.format(ssh_url=repository['ssh_url'])

        return self.execute_without_repository_name(command)

    def git_add_upstream(self, repository):
        original_owner = repository['parent']['owner']['login']
        original_repository = repository['parent']['name']

        template = 'https://github.com/{original_owner}/{original_repository}.git'
        url = template.format(original_owner=original_owner, original_repository=original_repository)

        name = repository['parent']['name']

        command = 'git remote add upstream {upstream_url}'.format(upstream_url=url)

        return self.execute_with_repository_name(command, name)

    def git_update_fork(self, repository):
        self.git_fetch_upstream(repository)
        if self.clean:
            self.git_clean(repository)
        if self.reset:
            self.git_reset(repository)
        self.git_checkout(repository)
        self.git_merge_upstream(repository)
        self.git_push(repository)

    def git_fetch_upstream(self, repository):
        name = repository['parent']['name']

        command = 'git fetch upstream'

        return self.execute_with_repository_name(command, name)

    def git_checkout(self, repository):
        name = repository['parent']['name']
        default_branch = repository['parent']['default_branch']

        command = 'git checkout {default_branch}'.format(default_branch=default_branch)

        return self.execute_with_repository_name(command, name)

    def git_clean(self, repository):
        name = repository['parent']['name']

        command = 'git clean -xfd'

        return self.execute_with_repository_name(command, name)

    def git_reset(self, repository):
        name = repository['parent']['name']

        command = 'git reset --hard HEAD'

        return self.execute_with_repository_name(command, name)

    def git_merge_upstream(self, repository):
        name = repository['parent']['name']
        default_branch = repository['parent']['default_branch']

        command = 'git merge upstream/{default_branch} --strategy-option theirs --no-edit'.format(default_branch=default_branch)

        return self.execute_with_repository_name(command, name)

    def git_push(self, repository):
        name = repository['parent']['name']

        command = 'git push --all && git push --tags'

        return self.execute_with_repository_name(command, name)

    def execute_without_repository_name(self, command):
        return self.execute(command, self.target_directory)

    def execute_with_repository_name(self, command, name):
        return self.execute(command, self.resolve_repository_directory(name))

    @staticmethod
    def execute(command, cwd):
        return subprocess.run(command, cwd=cwd, shell=True, check=True)

    def resolve_repository_directory(self, name):
        return os.path.join(self.target_directory, name)


if __name__ == '__main__':
    args = parse_args()

    gh_fork_sync = GitHubForkSync(args.organization,
                                  args.access_token,
                                  args.target_directory,
                                  args.clean,
                                  args.reset)

    gh_fork_sync.sync_forks_from_page(1)
