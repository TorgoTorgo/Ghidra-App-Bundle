# Ghidra App Bundle

[![Ghidra](/doc/Ghidra.png)](https://ghidra-sre.org)

[![Github CI](https://github.com/TorgoTorgo/Ghidra-App-Bundle/workflows/CI/badge.svg?branch=master)](https://github.com/TorgoTorgo/Ghidra-App-Bundle/actions?query=workflow%3ACI+branch%3Amaster)
[![GitLab CI](https://gitlab.com/Torgo/ghidra-app-bundle/badges/master/pipeline.svg)](https://gitlab.com/Torgo/ghidra-app-bundle/-/commits/master)

This repo contains a script to create an app bundle for the
Ghidra SRE framework. This makes Ghidra look and play nicer
on the macOS platform.

Click one of the CI pipeline buttons above to download the prebuilt bundles.

## Building

Building is simple, the quickest way to get started is to run `./update.py --dmg`. This will download the latest Ghidra from Github.

```bash
pip3 install -r requirements.txt
./update.py --dmg
open Ghidra*.dmg
```

To install a specific version you can specify a version on the command line, or a URL/local path.

```bash
pip3 install -r requirements.txt
./update.py --list-versions
# A list of versions will be printed
./update.py --dmg --version "10.0.1"
```

To install a specific version from a custom URL:

```bash
pip3 install -r requirements.txt
./update.py --dmg --version "9.2.2" --url "https://ghidra-sre.org/ghidra_9.2.2_PUBLIC_20201229.zip"
open Ghidra*.dmg
```

### Experimental Python3 (and more!) with Graal and Ghidraal

Building a bundle with:

```sh
./update.py --graal
```

builds Ghidra and bundles the [GraalVM](https://www.graalvm.org), a
drop in replacement for OpenJDK that provides experimental polyglot support for
Python3, R, NodeJS, etc. It also installs the [Ghidraal extension](https://github.com/jpleasu/ghidraal)
which installs scripting support for a number of GraalVM supported languages.

Once the bundle has been built, open the code browser tool and then open File, Configure Extensions,
and open the Experimental section. From there check the box for Ghidraal, close the extensions window
and click File, Save Tool to save your changes.

Once the Ghidraal extension is enabled you'll find a "Ghidraal" category in the script browser with
examples of Python3, NodeJS, and other scripts. You may have some issues with python2 scripts, but the
2to3 tool can solve many of these.

Note that at the time of writing, [Graal's Python3 support is not sufficient for most packages](https://github.com/oracle/graalpython/issues/228) and some language features, such as asyncio, are not supported. It might still be useful to have things such as type hints and fstrings however.