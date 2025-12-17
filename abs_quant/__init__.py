"""Absolute Quantification Pipeline for Microbial Metagenomics"""

__version__ = "1.0.0"
__author__ = "NI Can"
__email__ = "nican0910@connect.hku.hk"

from .cli import main
from .build import build_database
from .process import process_sample
from .utils import setup_logger, ColorFormatter
