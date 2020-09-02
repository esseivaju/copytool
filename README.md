[github repo](https://github.com/esseivaju/copytool)
# copytool
Copy dir to another, checking checksum of each file. This script has two mode of working:
* --copy : This will copy a src directory to a destination directory and verify the integrity of each file by computing a checksum on the source file and the newly copied file. If the checksum mismatch, an entry is generated in the log file. In additon a csv summary of all copied files and their hash is also generated. Note that if the checksum between the original and new files mismatch, the new file is kept.
* --check : works with an output directory copied with --copy. Check will look at each file hash saved in the cheksum file, recompute the hash of the file and make sure both match. Any missmatch is logged in the log file created at the rot of specified directry

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
usage: bns_copytool [-h] (--copy src dst | --check dir) [--full-copy]
                    [--workers WORKERS]
                    [--cksum {sha384,sha1,blake2s,md5,sha3_256,sha224,blake2b,sha512,sha3_384,sha256,sha3_224,sha3_512}]

optional arguments:
  -h, --help            show this help message and exit
  --copy src dst        Copy mode. Copy the directory src to dst. The checksum
                        is checked before and after copying each file to make
                        sure it was successfully copied. Save checksum files
                        in dst to be used with --check later. Produces a
                        logfile in the current directory
  --check dir           Check mode. Verify that each file in the specified
                        directory (and subdirectories) still match it's
                        checksum. Each directory should have a checksum.sha3
                        file with the checksum of each file. Produces a
                        logfile in the current directory
  --full-copy           By default the script doesn't copy files if the
                        destination already exists and was modified after src.
                        Set this argument to copy every file regardless
  --workers WORKERS     Number of workers (threads) to use. Default to the
                        number of cpu cores
  --cksum {sha384,sha1,blake2s,md5,sha3_256,sha224,blake2b,sha512,sha3_384,sha256,sha3_224,sha3_512}
                        Select the checksum algorithm to use
```
