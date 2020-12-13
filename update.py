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

parser = argparse.ArgumentParser()
parser.add_argument('-u', '--url', help='Ghidra zip URL')
parser.add_argument(
    '-p', '--path', help='Path to Ghidra zip or install', type=Path)
parser.add_argument('-d', '--dmg', action='store_true',
                    help='Construct a DMG file for distribution')
parser.add_argument('-t', '--tar', action='store_true',
                    help='Construct a tar file for distribution')
parser.add_argument('-v', '--version', dest='version',
                    help='Set the version for the dmg. Eg: "9.1 BETA"')
parser.add_argument(
    '-j', '--jdk', help='Path to a JDK directory to bundle', type=Path)

args = parser.parse_args()
with tempfile.TemporaryDirectory() as tmp_dir:
    shutil.copytree('Ghidra.app', os.path.join(tmp_dir, 'Ghidra.app'))
    os.symlink('/Applications', os.path.join(tmp_dir, 'Applications'))

    out_app = Path(tmp_dir, 'Ghidra.app')
    contents_path = out_app.joinpath('Contents')
    dest_path = contents_path.joinpath('Resources')

    if args.version:
        # Set the version in the plist if possible
        print(f"[+] Setting bundle version to {args.version.split()[0]}")
        with open(contents_path.joinpath('Info.plist'), 'rb') as plist_file:
            info = plistlib.loads(plist_file.read())
        info['CFBundleVersion'] = args.version.split()[0]
        with open(contents_path.joinpath('Info.plist'), 'wb') as plist_file:
            plistlib.dump(info, plist_file)

    if args.url:
        print("[+] Downloading {}".format(args.url))
        download = requests.get(args.url)

        if download.status_code == 200:
            ghidra_content = download.content
        else:
            print('[!] Failed to download!')
            sys.exit(1)
    elif args.path:
        print("[-] Will use Ghidra from {}".format(args.path))
    else:
        print("[!] Neither path nor url were specified!")
        sys.exit(1)

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
                subprocess.run(
                    f'unzip -d "{jdk_path}" "{zip_path}"', shell=True)
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
