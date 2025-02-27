import cmd
import subprocess
import sys
import os
import requests

class deployCLI(cmd.Cmd):
    prompt = 'Deploy_Box >> '
    intro = 'Welcome to Deploy Box. Type "help" for available commands'

    def __init__(self):
        super().__init__()
        self.check_user('')
        self.do_check_docker('')  # Automatically check for Docker when the CLI starts
        self.download_image('')
        self.run_image('')

    def check_user(self, line):
        username = "hapi"
        print(f'user identified hello: {username}')
        pass


############################################################start of docker stuff#################################################################################
    def do_check_docker(self, line):
        """Check if Docker is installed"""
        print("Checking if Docker is installed...")
        try:
            subprocess.run(['docker', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Docker is installed!")
            self.check_docker_engine()
        except subprocess.CalledProcessError:
            print("Docker is not installed.")
            self.ask_to_install_docker()

    def check_docker_engine(self):
        """Check if Docker engine is running"""
        print("Checking if Docker engine is running...")
        try:
            subprocess.run(['docker', 'info'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Docker engine is running.")
            self.do_next_step('')
        except subprocess.CalledProcessError:
            print("Docker engine is not running.")
            self.start_docker_engine()

    def start_docker_engine(self):
        """Start Docker engine if not running"""
        if sys.platform.startswith('linux'):
            self.start_docker_engine_linux()
        elif sys.platform.startswith('win'):
            self.start_docker_engine_windows()
        else:
            print("Docker engine start not supported on this platform.")
            self.do_exit('')

    def start_docker_engine_linux(self):
        """Start Docker engine on Linux"""
        print("Starting Docker engine on Linux...")
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'docker'], check=True)
            print("Docker engine started on Linux.")
        except subprocess.CalledProcessError as e:
            print(f"Error starting Docker engine on Linux: {e}")
        self.do_next_step('')

    def start_docker_engine_windows(self):
        """Start Docker engine on Windows without opening Docker Desktop"""
        print("Starting Docker engine on Windows...")
        try:
            subprocess.run(['sc', 'start', 'Docker'], check=True)  # Starts the Docker service
            print("Docker engine started on Windows without opening Docker Desktop.")
        except subprocess.CalledProcessError as e:
            print(f"Error starting Docker engine on Windows: {e}")
        
        self.do_next_step('')

    def ask_to_install_docker(self):
        """Ask the user if they want to install Docker"""
        user_input = input("Do you want to install Docker? (Y/N): ").strip().lower()
        if user_input == 'y':
            self.install_docker()
        elif user_input == 'n':
            print("Docker installation skipped.")
            self.do_exit('')
        else:
            print("Invalid input, please enter Y or N.")
            self.ask_to_install_docker()

    def install_docker(self):
        """Install Docker if it's not found"""
        print("Installing Docker...")
        if sys.platform.startswith('linux'):
            self.install_docker_linux()
        elif sys.platform.startswith('win'):
            self.install_docker_windows()
        else:
            print("Installation not supported on this platform.")
        self.do_next_step('')

    def install_docker_linux(self):
        """Install Docker on Linux"""
        print("Installing Docker on Linux...")
        try:
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'docker.io'], check=True)
            print("Docker installation complete on Linux!")
        except subprocess.CalledProcessError as e:
            print(f"Error installing Docker on Linux: {e}")
        self.do_next_step('')

    def install_docker_windows(self):
        """Install Docker on Windows"""
        print("Installing Docker on Windows...")
        # Download the Docker Desktop installer for Windows
        docker_installer_url = 'https://desktop.docker.com/win/stable/Docker%20Desktop%20Installer.exe'
        docker_installer_path = os.path.join(os.getenv('TEMP'), 'DockerDesktopInstaller.exe')
        
        try:
            # Download the installer
            subprocess.run(['curl', '-L', docker_installer_url, '-o', docker_installer_path], check=True)
            print("Docker installer downloaded. Running the installer...")
            
            # Run the installer
            subprocess.run([docker_installer_path], check=True)
            print("Docker installation complete on Windows!")
        except subprocess.CalledProcessError as e:
            print(f"Error installing Docker on Windows: {e}")
        
        self.do_next_step('')

#######################################end of docker sutff##################################################################################################################

####################################start of image exicution################################################################################################################
    def download_image(self, line):
        url = "http://34.68.6.54:7890/api/pull-artifact/1740617456-mern-frontend"
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        file_name = os.path.join(downloads_folder, "mern_frontend.tar")

        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(file_name, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            try:
                subprocess.run(['docker', 'load', '-i', file_name], check=True)
            except subprocess.CalledProcessError as e:
                print(f'error extracting tar file: {e}')

            print("Download Complete Here is your File Name: ", file_name)
        
        else: 
            print("Failed to download file: ", response.status_code)

    def run_image(self, line):
        print("would you like to run your image?")
        user_i = input("enter Y/N")

        if user_i == "Y" or user_i == "y":
            try:
                print("your container is running on port 8080")
                subprocess.run(['docker', 'run', '-p', '8080:8080','us-central1-docker.pkg.dev/deploy-box/deploy-box-repository/1740617456-mern-frontend:latest'], check=True)
            except subprocess.CalledProcessError as e:
                print(f'Error running image: {e}')

        else:
            print("fine don't then")
            self.do_next_step('')

########################################end of image stuff###################################################################################################################

        

    def do_next_step(self, line):
        """Move on to the next installation step"""
        print("Moving on to the next step...")
        # Add further steps here

    def do_exit(self, line):
        """Exit the CLI"""
        print("Exiting...")
        return True

    def postcmd(self, stop, line):
        """Adds an extra line for readability"""
        print()
        return stop


if __name__ == '__main__':
    deployCLI().cmdloop()


