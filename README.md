# Ghidra App Bundle

This repo contains a script to create an app bundle for the
Ghidra SRE framework. This makes Ghidra look and play nicer
on the macOS platform.

## Building

Building is simple, the quickest way to get started is to just point
update.py to the Ghidra zip you want to bundle.

```bash
pip3 install -r requirements.txt
./update.py --dmg --version "9.0.4" --url https://ghidra-sre.org/ghidra_9.0.4_PUBLIC_20190516.zip
open Ghidra*.dmg
```
