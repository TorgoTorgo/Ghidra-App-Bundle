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

parser = argparse.ArgumentParser()
parser.add_argument('-u', '--url', help='Ghidra zip URL')
parser.add_argument('-p', '--path', help='Path to Ghidra zip')
parser.add_argument('-d', '--dmg', action='store_true',
                    help='Construct a DMG file for distribution')
parser.add_argument('-t', '--tar', action='store_true',
                    help='Construct a tar file for distribution')
parser.add_argument('-v', '--version', dest='version',
                    help='Set the version for the dmg. Eg: "9.1 BETA"')

args = parser.parse_args()
with tempfile.TemporaryDirectory() as tmp_dir:
    shutil.copytree('Ghidra.app', os.path.join(tmp_dir, 'Ghidra.app'))
    os.symlink('/Applications', os.path.join(tmp_dir, 'Applications'))
    dest_path = os.path.join(tmp_dir, 'Ghidra.app', 'Contents', 'Resources')
    if args.url:
        print("[+] Downloading {}".format(args.url))
        download = requests.get(args.url)

        if download.status_code == 200:
            ghidra_content = download.content
        else:
            print('[!] Failed to download!')
            sys.exit(1)
    elif args.path:
        print("[+] Opening {}".format(args.path))
        with open(args.path, 'rb') as f:
            ghidra_content = f.read()
    else:
        print("[!] Neither path nor url were specified!")
        sys.exit(1)

    print("[+] Extracting...")
    with tempfile.TemporaryDirectory() as zip_dir:
        zip_path = os.path.join(zip_dir, 'Ghidra.zip')
        with open(zip_path, 'wb') as f:
            f.write(ghidra_content)
        subprocess.run(f'unzip -d "{dest_path}" "{zip_path}"', shell=True)
    print("[+] Extracted to {}".format(dest_path))

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
