"""
Block module for the SampleChain blockchain.

This module contains the Block class which represents a blockchain block
containing transactions, proof-of-work, and linking to previous blocks.
"""

import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .transaction import Transaction


@dataclass
class Block:
    """
    Represents a block in the blockchain.

    A block contains a list of transactions, a reference to the previous block,
    and proof-of-work data (nonce) that makes the block valid.

    Attributes:
        index: The position of this block in the chain
        transactions: List of transactions included in this block
        timestamp: Unix timestamp when the block was created
        previous_hash: Hash of the previous block in the chain
        nonce: Proof-of-work nonce value
        difficulty: Mining difficulty (number of leading zeros required)
    """

    index: int
    transactions: List[Transaction]
    timestamp: int = field(default_factory=lambda: int(time.time()))
    previous_hash: str = "0" * 64  # SHA256 produces 64-character hex strings
    nonce: int = 0
    difficulty: int = 4  # Number of leading zeros required in hash

    def __post_init__(self) -> None:
        """Validate block parameters after initialization."""
        if self.index < 0:
            raise ValueError("Block index must be non-negative")

        if self.difficulty < 1:
            raise ValueError("Difficulty must be at least 1")

        if len(self.previous_hash) != 64:
            raise ValueError("Previous hash must be 64 characters (SHA256)")

        # Validate all transactions
        for transaction in self.transactions:
            if not isinstance(transaction, Transaction):
                raise TypeError("All transactions must be Transaction objects")

    def calculate_hash(self) -> str:
        """
        Calculate the SHA256 hash of this block.

        The hash includes the block index, timestamp, previous hash, nonce,
        and all transactions in the block.

        Returns:
            The hexadecimal hash string of the block
        """
        # Create a deterministic string representation of transactions
        transactions_str = json.dumps(
            [tx.to_dict() for tx in self.transactions],
            sort_keys=True,
            separators=(",", ":"),
        )

        block_string = (
            f"{self.index}:"
            f"{self.timestamp}:"
            f"{self.previous_hash}:"
            f"{self.nonce}:"
            f"{transactions_str}"
        )

        return hashlib.sha256(block_string.encode()).hexdigest()

    def is_hash_valid(self, block_hash: Optional[str] = None) -> bool:
        """
        Check if the block's hash meets the difficulty requirement.

        Args:
            block_hash: Hash to validate (if None, calculates current hash)

        Returns:
            True if hash has the required number of leading zeros
        """
        if block_hash is None:
            block_hash = self.calculate_hash()

        required_prefix = "0" * self.difficulty
        return block_hash.startswith(required_prefix)

    def get_merkle_root(self) -> str:
        """
        Calculate the Merkle root of all transactions in this block.

        Returns:
            SHA256 hash representing the Merkle root
        """
        if not self.transactions:
            return "0" * 64

        # Start with transaction hashes
        hashes = [tx.calculate_hash() for tx in self.transactions]

        # Build Merkle tree bottom-up
        while len(hashes) > 1:
            next_level = []

            # Process pairs of hashes
            for i in range(0, len(hashes), 2):
                left = hashes[i]
                right = hashes[i + 1] if i + 1 < len(hashes) else left

                combined = left + right
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())

            hashes = next_level

        return hashes[0]

    def get_transaction_total(self) -> int:
        """
        Calculate the total value of all transactions in this block.

        Returns:
            Sum of all transaction values
        """
        return sum(tx.value for tx in self.transactions)

    def get_total_fees(self) -> int:
        """
        Calculate the total fees of all transactions in this block.

        Returns:
            Sum of all transaction fees
        """
        return sum(tx.fee for tx in self.transactions)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert block to dictionary representation.

        Returns:
            Dictionary containing all block data
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "hash": self.calculate_hash(),
            "merkle_root": self.get_merkle_root(),
            "transaction_count": len(self.transactions),
            "transactions": [tx.to_dict() for tx in self.transactions],
            "total_value": self.get_transaction_total(),
            "total_fees": self.get_total_fees(),
        }

    def to_json(self) -> str:
        """
        Convert block to JSON string.

        Returns:
            JSON string representation of the block
        """
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        """
        Create block from dictionary.

        Args:
            data: Dictionary containing block data

        Returns:
            New Block instance
        """
        transactions = [
            Transaction.from_dict(tx_data) for tx_data in data["transactions"]
        ]

        return cls(
            index=data["index"],
            transactions=transactions,
            timestamp=data["timestamp"],
            previous_hash=data["previous_hash"],
            nonce=data["nonce"],
            difficulty=data.get("difficulty", 4),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Block":
        """
        Create block from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            New Block instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def create_genesis_block(cls) -> "Block":
        """
        Create the genesis (first) block of the blockchain.

        Returns:
            Genesis block with index 0 and no transactions
        """
        return cls(
            index=0, transactions=[], previous_hash="0" * 64, timestamp=int(time.time())
        )

    def __str__(self) -> str:
        """String representation of the block."""
        return (
            f"Block {self.index} "
            f"({len(self.transactions)} transactions, "
            f"hash: {self.calculate_hash()[:12]}...)"
        )

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return (
            f"Block(index={self.index}, "
            f"transactions={len(self.transactions)}, "
            f"previous_hash={self.previous_hash[:12]}..., "
            f"nonce={self.nonce})"
        )
