from setuptools import setup, find_packages
import os

# 读取README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取版本
with open("abs_quant/__init__.py", "r", encoding="utf-8") as fh:
    for line in fh:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"\'')
            break

setup(
    name="abs_quant",
    version=version,
    author="Your Name",
    author_email="your.email@example.com",
    description="Absolute Quantification Pipeline for Microbial Metagenomics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/abs_quant",
    packages=find_packages(),
    package_data={
        'abs_quant': ['data/*.csv'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Intended Audience :: Science/Research",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "colorama>=0.4.4",
        "biopython>=1.79",
    ],
    entry_points={
        "console_scripts": [
            "abs_quant=abs_quant.cli:main",
        ],
    },
)
