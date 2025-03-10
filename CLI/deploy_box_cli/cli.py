import cmd
import os
print(os.getcwd())  # This will print the current working directory

from helpers.auth import AuthHelper
from helpers.docker import DockerHelper
from helpers.deployment import DeploymentHelper

class DeployCLI(cmd.Cmd):
    prompt = 'Deploy_Box >> '
    intro = 'Welcome to Deploy Box. Type "help" for available commands'

    def __init__(self):
        super().__init__()
        self.auth = AuthHelper()
        self.docker = DockerHelper()
        self.deployment = DeploymentHelper(auth=self.auth)

        print(self.auth.access_token)

        # self.deployment.upload_source_code()

    def do_login(self, _):
        """Login to the CLI"""
        self.auth.login()

    def do_logout(self, _):
        """Logout from the CLI"""
        self.auth.logout()

    def do_check_docker(self, _):
        """Check and start Docker if needed"""
        if not self.docker.check_docker():
            install = input("Docker not found. Install now? (Y/N): ").strip().lower()
            if install == 'y':
                self.docker.install_docker()

    def do_download_SC(self, _):
        """Download source code"""
        self.deployment.download_source_code()

    def do_upload(self, _):
        """Upload source code to cloud"""
        self.deployment.upload_source_code()

    def do_exit(self, _):
        """Exit the CLI"""
        print("Exiting...")
        return True

def main():
    DeployCLI().cmdloop()

if __name__ == '__main__':
    main()