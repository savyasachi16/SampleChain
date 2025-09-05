"""
SampleChain: A modern blockchain implementation in Python.

A simple but robust blockchain implementation with transaction validation,
proof-of-work mining, and comprehensive testing.
"""

__version__ = "2.0.0"
__author__ = "SampleChain Developer"

from .blockchain import Blockchain
from .block import Block
from .transaction import Transaction
from .miner import Miner

__all__ = ["Blockchain", "Block", "Transaction", "Miner"]
