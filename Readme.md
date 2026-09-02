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
    "package.json"
    "package-lock.json"
    "README.md"
)

# ==========================================
# Argument Parsing
# ==========================================
INSTALL=false
for arg in "$@"; do
    case $arg in
        -i|--install)
            INSTALL=true
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

echo "Build completed: $ZIP_NAME"
```