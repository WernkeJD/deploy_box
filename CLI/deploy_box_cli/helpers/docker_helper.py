import subprocess
import sys
import os
import docker
from .decorators import singleton


@singleton
class DockerHelper:
    def __init__(self):
        self.client = None

    def check_docker(self):
        """Check if Docker is installed."""
        try:
            subprocess.run(
                ["docker", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            print("Docker is installed!")
            return True
        except subprocess.CalledProcessError:
            print("Docker is not installed.")
            return False

    def start_docker_engine(self):
        """Start Docker engine based on OS."""
        if sys.platform.startswith("linux"):
            subprocess.run(["sudo", "systemctl", "start", "docker"], check=True)
            print("Docker engine started on Linux.")
        elif sys.platform.startswith("win"):
            subprocess.run(["sc", "start", "Docker"], check=True)
            print("Docker engine started on Windows.")
        else:
            print("Docker engine start not supported on this platform.")

    def install_docker(self):
        """Install Docker based on OS."""
        if sys.platform.startswith("linux"):
            subprocess.run(
                ["sudo", "apt-get", "install", "-y", "docker.io"], check=True
            )
            print("Docker installed on Linux!")
        elif sys.platform.startswith("win"):
            docker_installer_url = (
                "https://desktop.docker.com/win/stable/Docker%20Desktop%20Installer.exe"
            )
            docker_installer_path = os.path.join(
                os.getenv("TEMP"), "DockerDesktopInstaller.exe"
            )

            subprocess.run(
                ["curl", "-L", docker_installer_url, "-o", docker_installer_path],
                check=True,
            )
            subprocess.run([docker_installer_path], check=True)
            print("Docker installed on Windows!")
        else:
            print("Docker installation not supported on this platform.")

    def authenticate(self, auth_config):
        """Authenticate with Docker Hub."""
        self.client = docker.from_env()
        self.client.login(**auth_config)

    def build_image(self, image_name: str, source_directory: str):
        """Build a Docker image."""
        image, logs = self.client.images.build(path=source_directory, tag=image_name)

        for log in logs:
            print(log)

    def push_image(self, image_name: str):
        """Push a Docker image to a registry."""
        self.client.images.push(image_name)
