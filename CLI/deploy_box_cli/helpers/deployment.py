import os
import subprocess
from helpers.auth import AuthHelper
from helpers.menu import MenuHelper


class DeploymentHelper:
    def __init__(self, auth: AuthHelper):
        self.auth = auth

    def get_available_stacks(self):
        """Get a list of stacks for the user"""
        response = self.auth.request_api("GET", "get_available_stacks")

        if response.status_code != 200:
            print(f"Error: {response.json()['error']}")
            return

        data = response.json()
        options = [
            f"{stack['variant']} {stack['type']} : {stack['version']}" for stack in data
        ]
        options.append("Cancel")

        selected_idx, _ = MenuHelper.menu(options, "Select a stack to deploy:")

        return data[selected_idx]["id"], data[selected_idx]["type"]

    def download_source_code(self):
        """Download and extract source code for the selected stack."""
        stack_id, stack_type = self.get_available_stacks()

        current_working_dir = os.getcwd()
        file_name = os.path.join(current_working_dir, f"{stack_type}.tar")
        extracted_file_name = os.path.join(current_working_dir, stack_type)

        response = self.auth.request_api(
            "GET", f"download_stack/{stack_id}", stream=True
        )
        if response.status_code == 200:
            print("Downloading file...")
            with open(file_name, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            if not os.path.exists(extracted_file_name):
                os.makedirs(extracted_file_name)

            try:
                subprocess.run(
                    ["tar", "-xvf", file_name, "-C", extracted_file_name], check=True
                )
                print("Extraction complete!")
            except subprocess.CalledProcessError as e:
                print(f"Error extracting tar file: {e}")

    def get_available_deployments(self):
        """Get a list of deployments for the user"""
        response = self.auth.request_api("GET", "get_available_deployments")

        if response.status_code != 200:
            # print(f"Error: {response.text}")
            return

        data = response.json()

        options = [f"{deployment['name']}" for deployment in data]
        options.append("Upload new deployment")
        options.append("Cancel")

        selected_idx, _ = MenuHelper.menu(options, "Select a deployment to deploy:")

        if selected_idx >= len(data):
            selected_idx = selected_idx - len(options)

        return data[selected_idx]["id"] if selected_idx >= 0 else selected_idx

    def upload_source_code(self):
        deployment_id = self.get_available_deployments()

        # Cancel the operation
        if deployment_id == -1:
            print("Operation cancelled.")

        # Upload new deployment
        elif deployment_id == -2:
            print("Uploading new deployment...")
            deployment_name = input("Enter deployment name: ")
            deployment_stack_id, _ = self.get_available_stacks()

            if not deployment_name:
                print("Error: Deployment name is required.")
                return

            data = {"name": deployment_name, "stack_id": deployment_stack_id}

            # Open the file in binary mode and stream it
            compressed_file = self.compress_source_code()
            files = {"file": open("./MERN.tar", "rb")}

            self.auth.request_api(
                "POST", "upload_deployment", data=data, files=files, stream=True
            )

        # Upload to existing deployment
        else:
            data = {"deployment-id": deployment_id}

            # Open the file in binary mode and stream it
            files = {"file": open("./MERN.tar", "rb")}

            self.auth.request_api(
                "PATCH", "patch_deployment", data=data, files=files, stream=True
            )

    def compress_source_code(self):
        """Compress the source code into a tar file."""
        current_working_dir = os.getcwd()
        stack_type = os.path.basename(current_working_dir)
        file_name = os.path.join(current_working_dir, f"{stack_type}.tar")
        exclude_files = [
            ".git",
            ".vscode",
            "__pycache__",
            "node_modules",
            "venv",
            "env",
        ]

        try:
            exclude_args = []
            for ignore in exclude_files:
                exclude_args.extend(["--exclude", ignore])

            subprocess.run(
                ["tar", "-cvf", file_name] + exclude_args + ["."],
                check=True,
                cwd=current_working_dir,
            )
            print("Compression complete!")
        except subprocess.CalledProcessError as e:
            print(f"Error compressing files: {e}")
