#!/usr/bin/env python3

import argparse
import glob
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import requests
from pathlib import Path

import plistlib

try:
    from bs4 import BeautifulSoup
    have_bs4 = True
except ImportError:
    have_bs4 = False

parser = argparse.ArgumentParser()
parser.add_argument('-u', '--url', help='Ghidra zip URL')
parser.add_argument(
    '-p', '--path', help='Path to Ghidra zip or install', type=Path)
parser.add_argument('-d', '--dmg', action='store_true',
                    help='Construct a DMG file for distribution')
parser.add_argument('-t', '--tar', action='store_true',
                    help='Construct a tar file for distribution')
parser.add_argument('-v', '--version', dest='version', required=False,
                    help='Set the version for the dmg. Eg: "9.1 BETA"')
parser.add_argument('--app', type=Path, required=False, help='Do an in place upgrade of an app bundle')
parser.add_argument(
    '-j', '--jdk', help='Path to a JDK directory to bundle', type=Path)
parser.add_argument('--extension', type=Path, nargs='*', help='Path to a Ghidra extension zip to install')

args = parser.parse_args()


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
    dest_path = contents_path.joinpath('Resources')
    ghidra_content = None
    ghidra_zip_name = None

    if have_bs4 and not args.url and not args.path:
        print("No URL or path provided, getting latest from ghidra-sre.org")
        r = requests.get('https://ghidra-sre.org/')
        s = BeautifulSoup(r.content, 'html.parser')
        for link in s.find_all('a'):
            if link.get('href', default='').endswith('.zip'):
                args.url = 'https://ghidra-sre.org/{}'.format(link['href'])

    if args.path:
        print("[-] Will use Ghidra from {}".format(args.path))
        ghidra_zip_name = Path(args.path).name
    elif args.url:
        print("[+] Downloading {}".format(args.url))
        download = requests.get(args.url)
        ghidra_zip_name = Path(args.url).name

        if download.status_code == 200:
            ghidra_content = download.content
        else:
            print('[!] Failed to download!')
            sys.exit(1)
    else:
        print("[!] Neither path nor url were specified!")
        sys.exit(1)

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
       with tempfile.TemporaryDirectory() as zip_dir:
           zip_path = os.path.join(zip_dir, 'Ghidra.zip')
           with open(zip_path, 'wb') as f:
               f.write(ghidra_content)
           subprocess.run(f'unzip -d "{dest_path}" "{zip_path}"', shell=True)
       print("[+] Extracted to {}".format(dest_path))

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
                subprocess.run(f'unzip -d "{dest_path}" "{zip_path}"', shell=True)
            print("[+] Extracted to {}".format(dest_path))
        elif args.path.is_dir():
            print("[+] Copying...")
            shutil.copytree(args.path, dest_path / args.path.name)
            print("[+] Copied to {}".format(dest_path / args.path.name))

    # Install any extensions
    ghidra_install_dir = None
    try:
        ghidra_install_dir = next(dest_path.glob(f'ghidra_{version}*'))
    except IndexError as e:
        raise Exception(f"Ghidra was not installed into {dest_path}, is the Ghidra zip correctly structured?", e)
    # If we don't have an install dir matching this format, the launch
    # script won't work, so we might as well die here
    extension_dir = ghidra_install_dir.joinpath("Ghidra", "Extensions")
    if args.extension:
        for extension in args.extension:
            print("[+] Installing extension: {extension}")
            subprocess.run(f'unzip -d "{extension_dir}" "{extension}"', shell=True)

    if args.jdk:
        jdk_path = dest_path / "jdk"
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

    if args.dmg:
        print("[+] Building dmg")
        name = 'Ghidra'
        if args.version:
            name = f"{name} {args.version}"
        subprocess.run(
            f'genisoimage -V "{name}" -D -R -apple -no-pad -o "{name}.dmg" "{tmp_dir}"', shell=True)
        print(f"[+] Built {name}.dmg")
    elif args.tar:
        print("[+] Building tar")
        name = 'Ghidra'
        if args.version:
            name = f"{name} {args.version}"
        name = name.replace(' ', '_')
        subprocess.run(
            f'tar -cvzf "{name}.tar.gz" -C "{tmp_dir}" .', shell=True)
