from os.path import expanduser
from threading import Thread
from git import Repo, exc

# if on windows, get the username
if '\\' in expanduser("~"):
    user_name = expanduser("~").split('\\')[-1]
else:
    user_name = expanduser("~").split('/')[-1]

CORRECT_BRANCH = f'{user_name}/xml-main'


class GitTools(Thread):
    def __init__(self, script_name):
        Thread.__init__(self)
        self.script_name = script_name

    def run(self):
        self.push_changes()

    @staticmethod
    def check_branch(repo):
        try:
            if repo.active_branch.name != CORRECT_BRANCH:
                repo.git.checkout(CORRECT_BRANCH)
        except exc.GitCommandError:
            # Create the branch if it doesn't exist
            repo.git.checkout('HEAD', b=CORRECT_BRANCH)
            print(f'Created new branch: {CORRECT_BRANCH}')

    def push_changes(self):
        try:
            repo = Repo('./script_data')
            self.check_branch(repo)
            repo.git.add('.')
            repo.git.commit('-m', f'Updated {self.script_name}')
            # Tentative de poussée, configuration de l'upstream si nécessaire
            try:
                repo.git.push()
            except exc.GitCommandError:
                # Définir l'upstream si la branche n'a pas de branche distante
                repo.git.push('--set-upstream', 'origin', repo.active_branch.name)
                print(f'Set upstream for {repo.active_branch.name} to origin/{repo.active_branch.name}')
        except Exception as err:
            print(f'Error when pushing to gitlab: {err}')
        else:
            print(f'Pushed changes to {CORRECT_BRANCH} branch.')

    @staticmethod
    def reload():
        repo = Repo('./script_data')
        GitTools.check_branch(repo)
        try:
            repo.git.pull()
        except Exception as err:
            print(f'Error when pulling from gitlab: {err}')
        else:
            print(f'Pulled changes from {CORRECT_BRANCH} branch.')
