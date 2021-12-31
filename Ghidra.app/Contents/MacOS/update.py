#!/usr/bin/env python3

import argparse
import glob
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import io
import requests
from pathlib import Path

import plistlib

our_dir = Path(__file__).resolve().parent
download_dir = Path.home().joinpath("Downloads", "Ghidra-App-Bundle-Downloads")
download_dir.mkdir(exist_ok=True)
print(f"[+] Downloads will be cached to {download_dir}")

def download_file(url: str, filename: str = None) -> Path:
    if not filename:
        filename = url.split("/")[-1]
    dest = download_dir.joinpath(filename)
    if not dest.exists():
        print(f"[+] {dest} does not exist. Downloading from {url}")
        with open(dest, "wb") as f:
            with requests.get(url, stream=True) as r:
                shutil.copyfileobj(r.raw, f)
    return dest

def get_github_releases(project: str):
    r = requests.get(f'https://api.github.com/repos/{project}/releases')
    releases = r.json()
    releases = sorted(releases, key=lambda x: x["created_at"], reverse=True)
    return releases

def get_ghidra_releases():
    return get_github_releases('nationalsecurityagency/ghidra')

def list_ghidra_versions():
    releases = get_ghidra_releases()
    for release in releases:
        vers = release["name"].split(" ")[1]
        print(f"\t{vers}")

def clone_repository(git_url: str, destination: Path) -> Path:
    if not destination.exists():
        subprocess.check_call(f"git clone {git_url} {destination}", shell=True)
    assert destination.exists()
    return destination

def build_ghidra_extension(ghidra_home: Path, extension_path: Path, java_home: Path = None) -> Path:
    # Here we'll build the extension for our Ghidra version, and return a path
    # to the distribution zip file
    build_command = [
        "gradle"
    ]
    build_environment = {
        "GHIDRA_INSTALL_DIR": str(ghidra_home),
        "PATH": f"{java_home.joinpath('bin')}:{os.environ['PATH']}",
    }
    if java_home:
        build_environment["JAVA_HOME"] = str(java_home)
    subprocess.check_call(build_command, env=build_environment, cwd=extension_path, shell=True)
    distribution_zip = next(extension_path.joinpath("dist").glob('*.zip'))
    return distribution_zip


parser = argparse.ArgumentParser()
parser.add_argument('-u', '--url', help='Ghidra zip URL. Defaults to latest from Github')
parser.add_argument(
    '-p', '--path', help='Path to Ghidra zip or install', type=Path)
parser.add_argument('-d', '--dmg', action='store_true',
                    help='Construct a DMG file for distribution')
parser.add_argument('-t', '--tar', action='store_true',
                    help='Construct a tar file for distribution')
parser.add_argument('-v', '--version', dest='version', required=False,
                    help='Set the version for the dmg. Eg: "9.1 BETA"')
parser.add_argument('--app', type=Path, required=False, help='Do an in place upgrade of an app bundle')
parser.add_argument('--extension', type=Path, default=[], nargs='*', help='Path to a Ghidra extension zip to install')
parser.add_argument('--list-versions', action='store_true', help='Print available Ghidra versions')

jdk_group = parser.add_mutually_exclusive_group()
jdk_group.add_argument(
    '-j', '--jdk', help='Path to a JDK directory to bundle', type=Path)
jdk_group.add_argument("--graal", action='store_true', help="Bundle the Graal VM and Ghidraal for Python3 support")

args = parser.parse_args()

if args.list_versions:
    print("[+] Available Ghidra versions from Github:")
    list_ghidra_versions()
    exit(0)

if not args.app:
    # Maybe we are being run from within the bundle
    us = Path(__file__)
    for d in us.parents:
        if d.name == 'Contents':
            if d.parent.suffix == '.app':
                args.app = d.parent
                print(f"[+] We're in a bundle, defaulting app directory to {args.app}")
                break

with tempfile.TemporaryDirectory() as tmp_dir:
    shutil.copytree('Ghidra.app', os.path.join(tmp_dir, 'Ghidra.app'))
    os.symlink('/Applications', os.path.join(tmp_dir, 'Applications'))

    if args.app:
        out_app = args.app
    else:
        out_app = Path(tmp_dir, 'Ghidra.app')
    contents_path = out_app.joinpath('Contents')
    resources_path = contents_path.joinpath('Resources')
    ghidra_content = None
    ghidra_zip_name = None

    if not args.url and not args.path and not args.version:
        print("[!] No URL or path provided, getting latest from github")
        releases = get_ghidra_releases()
        release = releases[0] # The latest release
        args.version = release["name"].split(" ")[1]
        args.url = release["assets"][0]["browser_download_url"]
        print(f"[+] Fetching {args.version} from {args.url}")
        ghidra_download_path = download_file(args.url, filename=ghidra_zip_name)
        ghidra_zip_name = ghidra_download_path.name
    elif args.version and not args.url and not args.path:
        # If we have a version and not a path or URL, we'll get that specific release
        releases = get_ghidra_releases()
        for release in releases:
            if args.version in release["name"]:
                # Found it
                args.url = release["assets"][0]["browser_download_url"]
                print(f"[+] Found version {args.version} on Github @ {args.url}")
        if not args.url:
            print(f"[!] Failed to find version {args.version} on Github. Found:")
            list_ghidra_versions()
            exit(1)
    if args.path or args.url:
        pass
    else:
        print("[!] Neither path nor url were specified!")
        sys.exit(1)


    if args.path:
        print("[-] Will use Ghidra from {}".format(args.path))
        ghidra_zip_name = Path(args.path).name
    elif args.url:
        ghidra_download_path = download_file(args.url, filename=ghidra_zip_name)
        ghidra_content = ghidra_download_path.read_bytes()
        ghidra_zip_name = ghidra_download_path.name

    # calculate the name from a path
    if ghidra_zip_name:
        version = ghidra_zip_name.split('ghidra_')[1].split('_')[0]
    if args.version:
        version = args.version


    if version:
        # Set the version in the plist if possible
        print(f"[+] Setting bundle version to {version.split()[0]}")
        with open(contents_path.joinpath('Info.plist'), 'rb') as plist_file:
            info = plistlib.loads(plist_file.read())
        info['CFBundleVersion'] = version.split()[0]
        with open(contents_path.joinpath('Info.plist'), 'wb') as plist_file:
            plistlib.dump(info, plist_file)

    if args.url:
        print("[+] Extracting...")
        subprocess.run(f'unzip -d "{resources_path}" "{ghidra_download_path}"', shell=True)
        print("[+] Extracted to {}".format(resources_path))

    if args.path:
        if args.path.is_file():
            print("[+] Opening {}".format(args.path))
            with open(args.path, 'rb') as f:
                ghidra_content = f.read()
            print("[+] Extracting...")
            with tempfile.TemporaryDirectory() as zip_dir:
                zip_path = os.path.join(zip_dir, 'Ghidra.zip')
                with open(zip_path, 'wb') as f:
                    f.write(ghidra_content)
                subprocess.run(f'unzip -d "{resources_path}" "{zip_path}"', shell=True)
            print("[+] Extracted to {}".format(resources_path))
        elif args.path.is_dir():
            print("[+] Copying...")
            shutil.copytree(args.path, resources_path / args.path.name)
            print("[+] Copied to {}".format(resources_path / args.path.name))

    # Install any extensions
    ghidra_install_dir = None
    try:
        ghidra_install_dir = next(resources_path.glob(f'ghidra_{version}*'))
    except IndexError as e:
        raise Exception(f"Ghidra was not installed into {resources_path}, is the Ghidra zip correctly structured?", e)
    jdk_path = resources_path / "jdk"
    if args.jdk:
        if args.jdk.is_file():
            print("[+] Opening {}".format(args.jdk))
            with open(args.jdk, 'rb') as f:
                jdk_content = f.read()
            print("[+] Extracting...")
            with tempfile.TemporaryDirectory() as zip_dir:
                zip_path = os.path.join(zip_dir, 'JDK.zip')
                with open(zip_path, 'wb') as f:
                    f.write(jdk_content)
                with tempfile.TemporaryDirectory() as jdk_tmp_dir:
                    subprocess.run(
                        f'unzip -d "{jdk_tmp_dir}" "{zip_path}"', shell=True)
                    shutil.copytree(next(Path(jdk_tmp_dir).glob('*')), jdk_path)
            print("[+] Extracted to {}".format(jdk_path))
        if args.jdk.is_dir():
            print("[+] Copying...")
            shutil.copytree(args.jdk, jdk_path)
            print("[+] Copied to {}".format(jdk_path))
    if args.graal:
        graal_dest_path = resources_path / "graal"
        # Install the Graal VM as our JDK
        # First lets go grab the Graal VM from Github
        graal_releases = get_github_releases('graalvm/graalvm-ce-builds')

        # The release names look like:
        # GraalVM Community Edition 21.3.0
        graal_release = graal_releases[0]
        latest_graal_vm = graal_release["name"].split(" ")[-1]
        # Let's hunt for the Darwin asset
        graal_release_url = None
        graal_filename = None
        for asset in graal_release["assets"]:
            asset_name = asset["name"]
            if asset_name.endswith('tar.gz') and 'graalvm-ce-java11' in asset_name and 'darwin' in asset_name:
                graal_release_url = asset['browser_download_url']
                graal_filename = asset_name

        # We must have both the URL and the filename to continue
        assert graal_release_url and graal_filename
        print(f"[+] Graal {latest_graal_vm} @ {graal_release_url}")
        graal_tar_path = download_file(graal_release_url, graal_filename)
        # We derive the graal directory name from the name of the downloaded tar
        graal_cached = download_dir.joinpath(graal_filename.replace('darwin-amd64-', '').split('.tar.gz')[0])
        if not graal_cached.exists():
            subprocess.run(
                f'tar -C {download_dir} -xvf {graal_tar_path}', shell=True, check=True)
        print("[+] Installing graal VM components")
        subprocess.check_call(f"{graal_cached}/Contents/Home/bin/gu install llvm-toolchain native-image nodejs python ruby R wasm", shell=True)
        # Now that we've primed our cached version of graal with the various language components
        # we can install it into our Ghidra bundle

        # We must not already have a JDK path, if we do we'll end up with a 'Home' directory
        # inside the JDK path, which will break the launcher script.
        print("[+] Copying Graal to Ghidra bundle")
        assert not graal_dest_path.exists()
        assert not jdk_path.exists()
        graal_dest_path.mkdir()
        # Now copy the primed cache into our bundle. Note the archive parameter, we need to preserve
        # symlinks or graal will get sad
        subprocess.check_call(f"rsync --archive --recursive {graal_cached} {graal_dest_path}", shell=True)
        graal_home = next(graal_dest_path.glob('*')).joinpath("Contents", "Home")
        # The path looks like
        # graalvm-ce-java11-21.3.0/Contents/Home/...
        assert not jdk_path.exists()
        jdk_path.symlink_to(graal_home.relative_to(resources_path))
        # Now we'll check that our copied graal works for good measure
        subprocess.check_call(f'{graal_home}/bin/gu list', shell=True)

        # Now we have Graal installed, lets ensure we get the Ghidraal extension
        print("[+] Building Ghidraal extension")
        ghidraal_repo_path = download_dir.joinpath("ghidraal")
        clone_repository("https://github.com/jpleasu/ghidraal.git", ghidraal_repo_path)
        # Ghidraal seems to have a broken gradle.build file, so we'll patch it
        ghidraal_repo_path.joinpath("build.gradle").unlink()
        shutil.copy(our_dir.parent.joinpath("Resources", "build.gradle"), ghidraal_repo_path.joinpath("build.gradle"))
        ghidraal_extension = build_ghidra_extension(ghidra_install_dir, ghidraal_repo_path, java_home=jdk_path)
        # Pretend the user specified this on the command line
        print("[+] Adding Ghidraal to the selected extensions for installation")
        args.extension.append(ghidraal_extension)

    # If we don't have an install dir matching this format, the launch
    # script won't work, so we might as well die here
    extension_dir = ghidra_install_dir.joinpath("Ghidra", "Extensions")
    if args.extension:
        for extension in args.extension:
            print("[+] Installing extension: {extension}")
            subprocess.run(f'unzip -d "{extension_dir}" "{extension}"', shell=True)


    if args.dmg or not args.tar:
        print("[+] Building dmg")
        name = 'Ghidra'
        if args.version:
            name = f"{name} {args.version}"
        dmg_dest = Path(f"{name}.dmg")
        if dmg_dest.exists():
            dmg_dest.unlink()

        try:
            # Lets assume we're on macOS first
            subprocess.run(
                f'hdiutil create -volname "{name}" -fs HFS+  -srcfolder "{tmp_dir}" "{name}.dmg"', shell=True, check=True)
        except subprocess.CalledProcessError:
            # Now try the linux equivalent
            subprocess.run(
                f'genisoimage -V "{name}" -D -R -apple -no-pad -o "{name}.dmg" "{tmp_dir}"', shell=True, check=True)
        print(f"[+] Built {name}.dmg")
    elif args.tar:
        print("[+] Building tar")
        name = 'Ghidra'
        if args.version:
            name = f"{name} {args.version}"
        name = name.replace(' ', '_')
        subprocess.run(
            f'tar -cvzf "{name}.tar.gz" -C "{tmp_dir}" .', shell=True)
    else:
        print("[!] No output format specified. Please specify either --dmg or --tar")
