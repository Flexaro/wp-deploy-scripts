"""
Flexaro Build & Deploy Script for WordPress Websites
@version 1.0.0

"""

import subprocess
import os
import time

themes_input = os.getenv("WP_THEMES", "")
plugins_input = os.getenv("WP_PLUGINS", "")

themes = [t.strip() for t in themes_input.split(",") if t.strip()]
plugins = [p.strip() for p in plugins_input.split(",") if p.strip()]




FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASSWORD")
FTP_PORT = int(os.getenv("FTP_PORT")) if os.getenv("FTP_PORT") else 21
base_path = os.getenv("GITHUB_WORKSPACE", ".")


##########################################################
# Utility Functions
##########################################################
def check_env_variables():
    required_vars = ["FTP_HOST", "FTP_USER", "FTP_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)


def is_windows():
    return os.name == "nt"

def is_build_script_exists(path):
    if is_windows():
        return os.path.exists(f"{path}\\build.ps1")
    else:
        return os.path.exists(f"{path}/build.sh")
    
    
    
##########################################################
# Step 1: Build the themes
##########################################################
build_files = []

def build_themes_or_plugins(theme_name, type="theme"):
    print(f"Building {type}: {theme_name}")
    print(f"Current working directory: {base_path}")
    path = f"{base_path}/wp-content/{'themes' if type == 'theme' else 'plugins'}/{theme_name}"
    path_remote = f"/wp-content/{'themes' if type == 'theme' else 'plugins'}/{theme_name}"

    
    subprocess_cmds = []
    if is_windows():
        path = path.replace("/", "\\")

    if is_build_script_exists(path):
        if is_windows():
            subprocess_cmds = ["powershell", "-ExecutionPolicy", "Bypass", "-File", f"build.ps1"]
        else:
            subprocess_cmds = ["bash", f"build.sh"]

        try:
            result = subprocess.run(subprocess_cmds, 
                                    cwd=path,
                                    check=True,
                                    text=True,
                                    capture_output=True
                                   )
            print(f"Successfully built {type}: {theme_name}")
            print(result.stdout)
            output_dir = os.path.join(path, theme_name)
            if not os.path.exists(output_dir):
                raise Exception(f"Output directory {output_dir} does not exist after build.")
            
            build_files.append((theme_name, path, output_dir, path_remote))

        except subprocess.CalledProcessError as e:
            print(f"Error building {type} {theme_name}: {e}")
            exit(1)
    else:
        build_files.append((theme_name, path, path, path_remote))
        print(f"No build script found for {type}: {theme_name}. Skipping build.")





##########################################################
# Step 2: Upload to Server via FTP
##########################################################
import ftplib
from pathlib import Path

ftplib.FTP_PORT = FTP_PORT

def create_subdirectories(ftp, remote_dir):
    dirs = remote_dir.split('/')
    current_path = ''
    for dir in dirs:
        if dir:  # Skip empty strings
            current_path += f'/{dir}'
            try:
                ftp.mkd(current_path)
                print(f"Created directory: {current_path}")
            except ftplib.error_perm as e:
                if not str(e).startswith('550'):
                    print(f"Error creating directory {current_path}: {e}")
                    exit(1)


def upload_dir_to_ftp(local_dir, remote_dir):
    u_timestamp = time.time_ns()
    backup_dir = f"{remote_dir}-bk-{u_timestamp}"
    try:
        with ftplib.FTP(FTP_HOST) as ftp:
            ftp.login(FTP_USER, FTP_PASS)
            print(f"Connected to FTP server: {FTP_HOST}")


            # Rename remote directory if it exists to -backup
            try:
                ftp.cwd(remote_dir)
                try:
                    ftp.rename(remote_dir, backup_dir)
                    print(f"Renamed existing remote directory to: {backup_dir}")
                except ftplib.error_perm as e:
                    print(f"Failed to rename remote directory: {e}")
            except ftplib.error_perm:
                print(f"No existing remote directory to rename: {remote_dir}")

            try:
                for root, dirs, files in os.walk(local_dir):
                    for file in files:
                        local_file_path = os.path.join(root, file)
                        relative_path = Path(local_file_path).relative_to(local_dir)
                        remote_file_path = os.path.join(remote_dir, relative_path).replace("\\", "/")
    
                        # Ensure the remote directory exists
                        remote_dir_path = os.path.dirname(remote_file_path)
                        create_subdirectories(ftp, remote_dir_path)

                        with open(local_file_path, 'rb') as f:
                            ftp.storbinary(f'STOR {remote_file_path}', f)
                            print(f"Uploaded: {remote_file_path}")
            except Exception as e:
                print(f"Error during FTP upload: {e}")
                exit(1)

            # Delete the backup directory after successful upload
            try:
                ftp.cwd('/')
                ftp.rmd(backup_dir)
                print(f"Deleted backup directory: {backup_dir}")
            except ftplib.error_perm as e:
                print(f"Failed to delete backup directory: {e}")
            
    except Exception as e:
        print(f"FTP upload failed: {e}")
        exit(1)


if __name__ == "__main__":

    check_env_variables()

    # Step 1: Build the themes and plugins    
    for theme in themes:
        build_themes_or_plugins(theme, type="theme")

    for plugin in plugins:
        build_themes_or_plugins(plugin, type="plugin")

    # Step 2: Upload the built themes and plugins to the server
    for theme_name, local_path, output_dir, remote_path in build_files:
        print(f"Uploading {theme_name} from {output_dir} to {remote_path}")
        upload_dir_to_ftp(output_dir, remote_path)

    print("Deployment completed successfully.")