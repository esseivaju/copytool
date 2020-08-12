# copytool
Copy dir to another, checking checksum of each file

## Setup

bns_copytool requires python 3.7 and should be installed in a virtual environment.

```bash
conda create -ncopytool python=3.7
conda activate copytool
cd path/to/copytool
pip install .
copytool --help
```

After the script has been installed for the first time, subsequent use only require to activate  the environment:
```bash
conda activate copytool
bns_copytool --help
```

## Usage

```
bns_copytool --help
usage: bns_copytool [-h] (--copy src dst | --check dir) [--workers WORKERS]

optional arguments:
  -h, --help         show this help message and exit
  --copy src dst     Copy mode. Copy the directory src to dst. The checksum is
                     checked before and after copying each file to make sure
                     it was successfully copied. Save checksum files in dst to
                     be used with --check later. Produces a logfile in the
                     current directory
  --check dir        Check mode. Verify that each file in the specified
                     directory (and subdirectories) still matches its checksum.
                     Each directory should have a checksum.sha3 file with the
                     checksum of each file. Produces a logfile in the current
                     directory
  --workers WORKERS  Number of workers to use. Default to the number of cpu
                     cores
```
