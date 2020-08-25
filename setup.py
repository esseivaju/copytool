from setuptools import setup, find_packages

setup(
    name="Copytool",
    author="Julien Esseiva",
    description="Tool to copy file using multiple threads and check file integrity after the copy",
    version="0.1",
    packages=find_packages(),
    scripts=["bin/bns_copytool"],
    install_requires=[
        "progress>=1.5"
    ]
)
