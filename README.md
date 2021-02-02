# Ghidra App Bundle

[![Ghidra](/doc/Ghidra.png)](https://ghidra-sre.org)

[![Github CI](https://github.com/TorgoTorgo/Ghidra-App-Bundle/workflows/CI/badge.svg?branch=master)](https://github.com/TorgoTorgo/Ghidra-App-Bundle/actions?query=workflow%3ACI+branch%3Amaster)
[![GitLab CI](https://gitlab.com/Torgo/ghidra-app-bundle/badges/master/pipeline.svg)](https://gitlab.com/Torgo/ghidra-app-bundle/-/commits/master)

This repo contains a script to create an app bundle for the
Ghidra SRE framework. This makes Ghidra look and play nicer
on the macOS platform.

Click one of the CI pipeline buttons above to download the prebuilt bundles.

## Building

Building is simple, the quickest way to get started is to run `./update.py --dmg`. This will download the latest Ghidra by scraping the https://ghidra-sre.org site.

```bash
pip3 install -r requirements.txt
./update.py --dmg
open Ghidra*.dmg
```

To install a specific version you can specify a URL or a local path.

```bash
pip3 install -r requirements.txt
./update.py --version "9.2.2" --url "https://ghidra-sre.org/ghidra_9.2.2_PUBLIC_20201229.zip"
open Ghidra*.dmg
```

### Apple Silicon

You can use the JDK bundling feature to include an Apple Silicon compatible
JDK. In the example below we use the [JDK from Zulu](https://www.azul.com/downloads/zulu-community/?os=macos&architecture=arm-64-bit&package=jdk).

```bash
pip3 install -r requirements.txt
curl -o zulu_jdk.zip 'https://cdn.azul.com/zulu/bin/zulu16.0.65-ea-jdk16.0.0-ea.24-macos_aarch64.zip'
./update.py --tar --jdk zulu_jdk.zip
```
