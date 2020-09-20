# Ghidra App Bundle

[![Ghidra](/doc/Ghidra.png)](https://ghidra-sre.org)

[![Github CI](https://github.com/TorgoTorgo/Ghidra-App-Bundle/workflows/CI/badge.svg?branch=master)](https://github.com/TorgoTorgo/Ghidra-App-Bundle/actions?query=workflow%3ACI+branch%3Amaster)
[![GitLab CI](https://gitlab.com/Torgo/ghidra-app-bundle/badges/master/pipeline.svg)](https://gitlab.com/Torgo/ghidra-app-bundle/-/commits/master)

This repo contains a script to create an app bundle for the
Ghidra SRE framework. This makes Ghidra look and play nicer
on the macOS platform.

Click one of the CI pipeline buttons above to download the prebuilt bundles.

## Building

Building is simple, the quickest way to get started is to just point
update.py to the Ghidra zip you want to bundle.

```bash
pip3 install -r requirements.txt
./update.py --dmg --version "9.0.4" --url https://ghidra-sre.org/ghidra_9.0.4_PUBLIC_20190516.zip
open Ghidra*.dmg
```
