import os
import subprocess
from deploy_box_cli.helpers.auth import AuthHelper
from deploy_box_cli.helpers.menu import MenuHelper


class DeploymentHelper:
    def __init__(self, auth: AuthHelper):
        self.auth = auth

    def get_available_stacks(self):
        """Get a list of stacks for the user"""
        response = self.auth.request_api("GET", "stacks")

        if response.status_code != 200:
            print(f"Error: {response.json()['error']}")
            return

        return response.json().get("data", [])

    def download_source_code(self):
        """Download and extract source code for the selected stack."""
        stacks = self.get_available_stacks()

        data_options = [f"{stack['type']}" for stack in stacks]

        selected_idx, _ = MenuHelper.menu(
            data_options=data_options, prompt="Select a stack to download:"
        )

        stack_type = stacks[selected_idx]["type"]
        stack_id = stacks[selected_idx]["id"]

        current_working_dir = os.getcwd()
        file_name = os.path.join(current_working_dir, f"{stack_type}.tar")
        extracted_file_name = os.path.join(current_working_dir, stack_type)

        response = self.auth.request_api(
            "GET", f"stacks/{stack_id}/download", stream=True
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

        return response.json()

    def upload_source_code(self):
        compressed_file = self.compress_source_code()

        return
        available_deployments = self.get_available_deployments()

        data_options = [f"{deployment['name']}" for deployment in available_deployments]
        extra_options = ["Upload new deployment"]

        selected_idx, _ = MenuHelper.menu(
            data_options=data_options,
            extra_options=extra_options,
            prompt="Select a deployment to deploy:",
        )

        # Cancel the operation
        if selected_idx == -1:
            print("Operation cancelled.")

        # Upload new deployment
        elif selected_idx == -2:
            print("Uploading new deployment...")
            deployment_name = input("Enter deployment name: ")

            # TODO: Validate deployment name for special characters
            if not deployment_name:
                print("Error: Deployment name is required.")
                return

            available_stacks = self.get_available_stacks()

            data_options = [
                f"{stack['variant']} {stack['type']} : {stack['version']}"
                for stack in available_stacks
            ]
            selected_idx, _ = MenuHelper.menu(
                data_options=data_options,
                extra_options=[],
                prompt="Select a stack to deploy:",
            )

            if selected_idx == -1:
                print("Operation cancelled.")
                return

            deployment_stack_id = available_stacks[selected_idx]["id"]

            deployment_data = {"name": deployment_name, "stack_id": deployment_stack_id}

            # Open the file in binary mode and stream it
            compressed_file = self.compress_source_code()
            files = {"file": open("./MERN.tar", "rb")}

            self.auth.request_api(
                "POST",
                "upload_deployment",
                data=deployment_data,
                files=files,
                stream=True,
            )

        # Upload to existing deployment
        else:
            deployment_id = available_deployments[selected_idx]["id"]
            deployment_data = {"deployment-id": deployment_id}

            # Open the file in binary mode and stream it
            files = {"file": open("./MERN.tar", "rb")}

            self.auth.request_api(
                "PATCH",
                "patch_deployment",
                data=deployment_data,
                files=files,
                stream=True,
            )

    def compress_source_code(self):
        """Compress the source code into a tar file."""
        current_working_dir = os.getcwd()

        # TODO: Make sure the user can compress their source code from the cli

        # Check if the directory contains a frontend directory
        if not os.path.exists(os.path.join(current_working_dir, "frontend")):
            print("Error: No frontend directory found.")
            return

        # Check if the directory contains a backend directory
        if not os.path.exists(os.path.join(current_working_dir, "backend")):
            print("Error: No backend directory found.")
            return

        # Check if the directory contains a database directory
        if not os.path.exists(os.path.join(current_working_dir, "database")):
            print("Error: No database directory found.")
            return

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

            return file_name
        except subprocess.CalledProcessError as e:
            print(f"Error compressing files: {e}")
