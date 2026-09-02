# WordPress Build & Deploy

This actions provide easier way to deploy WordPress repository to FTP server. 
The goal is to skip the unnecessary files and only deploy the plugins and themes that are maintained by the repository.


## Usage

```yaml
name: Deploy WordPress to FTP
on:
  push:
    branches:
      - main    

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to FTP
        uses: Flexaro/wp-deploy-scripts/ftp-deploy@v1
        with:
          ftp_host: ${{ secrets.FTP_HOST }}
          ftp_user: ${{ secrets.FTP_USER }}
          ftp_password: ${{ secrets.FTP_PASSWORD }}
          ftp_port: ${{ secrets.FTP_PORT }}
          wp_themes: "theme1,theme2"
          wp_plugins: "plugin1,plugin2"
```

## Build Scripts

This action support automated plugin build scripts. That would be useful if you are using a build tool like Webpack, vite, or any other build tool that requires a build step before deployment. 

To use this feature, you need to add a `build.sh` script in the root of your plugin/theme's directory. Eg:

```text
wp-content/
  plugins/
    my-plugin/
      build.sh
      src/
      dist/
      my-plugin.php
      ...
  themes/
    my-theme/
      build.sh
      functions.php
      style.css
      ...
```

Sample `build.sh` script:

```bash
#!/usr/bin/env bash
set -e

# ==========================================
# Configuration Variables
# ==========================================
BUILD_DIR="my-plugin"
ZIP_NAME="my-plugin.zip"

# Files and directories to exclude from the copy
EXCLUDES=(
    "node_modules"
    ".git"
    ".vscode"
    "$BUILD_DIR"
    "$ZIP_NAME"
    "build.sh"
    "build.ps1"
    "package.json"
    "package-lock.json"
    "README.md"
)

# ==========================================
# Argument Parsing
# ==========================================
INSTALL=false
NO_DELETE_DIR=false
for arg in "$@"; do
    case $arg in
        -i|--install)
            INSTALL=true
            shift
            ;;
        --no-delete-dir)
            NO_DELETE_DIR=true
            shift
            ;;
    esac
done

# ==========================================
# Build Process
# ==========================================

# Delete existing build artifacts if they exist
echo "Cleaning old build files..."
rm -rf "$BUILD_DIR" "$ZIP_NAME"

# Create fresh build directory
mkdir -p "$BUILD_DIR"

# Run npm install and build if flag is provided
if [ "$INSTALL" = true ]; then
    echo "Running npm install and build..."
    npm install
    npm run build
fi

# Copy theme files excluding specified patterns
echo "Copying theme files to build directory..."
RSYNC_ARGS=("-av" "./" "$BUILD_DIR/")
for item in "${EXCLUDES[@]}"; do
    RSYNC_ARGS+=(--exclude="$item")
done

rsync "${RSYNC_ARGS[@]}"

# Create zip archive
echo "Creating zip archive..."
zip -r "$ZIP_NAME" "$BUILD_DIR"

if [ "$NO_DELETE_DIR" = false ]; then
    echo "Cleaning up build directory..."
    rm -rf "$BUILD_DIR"
fi

echo "Build completed: $ZIP_NAME"
```

You can also create a `build.ps1` script for Windows users. The script should have the same functionality as the `build.sh` script but written in PowerShell. You will need to have 7zip installed on your system and update the `$sevenZipPath` variable in the script to point to the correct path of the 7zip executable. Some servers does not support zip files created by the built-in Windows zip utility, so using 7zip is recommended.


```powershell
# Set variables
$buildDir = "my-plugin"
$zipName = "my-plugin.zip"

# 7zip path
$sevenZipPath = "C:\Program Files\7-Zip\7z.exe"


# Delete build directory "my-plugin" if exists
if (Test-Path -Path "./$buildDir") {
    Remove-Item -Recurse -Force "./$buildDir"
}
if (Test-Path -Path "./$zipName") {
    Remove-Item -Force "./$zipName"
}

# Create build directory
New-Item -ItemType Directory -Path "./$buildDir"

# If parameter has -install flag, run npm install
param([switch]$install)
if ($install) {
    Write-Host "Running npm install..."
    npm install
    npm run build
}

# Copy theme files to build directory excluding node_modules and .git
Write-Host "Copying theme files to build directory..."
robocopy .\ .\my-plugin /E /XD node_modules .git .vscode my-plugin /XF build.ps1 package.json package-lock.json README.md 

# Create zip archive of the build directory
Write-Host "Creating zip archive..."
& $sevenZipPath a -tzip "./$zipName" ".\$buildDir"

# --no-delete-dir flag to skip deleting the build directory
param([switch]$noDeleteDir)
if (-not $noDeleteDir) {
    Remove-Item -Recurse -Force "./$buildDir"
}

Write-Host "Build completed: $zipName"
```