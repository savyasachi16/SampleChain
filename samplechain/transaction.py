"""
Transaction module for the SampleChain blockchain.

This module contains the Transaction class which represents a blockchain
transaction with validation, serialization, and integrity checking.
"""

import hashlib
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Transaction:
    """
    Represents a blockchain transaction.

    A transaction transfers value from one address to another. Each transaction
    includes the sender (from_address), recipient (to_address), and the amount
    being transferred.

    Attributes:
        from_address: The address sending the value (integer address)
        to_address: The address receiving the value (integer address)
        value: The amount being transferred (must be positive)
        fee: Transaction fee for miners (defaults to 0)
        timestamp: Unix timestamp when transaction was created
    """

    from_address: int
    to_address: int
    value: int
    fee: int = 0
    timestamp: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate transaction parameters after initialization."""
        if self.value <= 0:
            raise ValueError("Transaction value must be positive")

        if self.fee < 0:
            raise ValueError("Transaction fee cannot be negative")

        # Allow -1 as special address for mining rewards
        if self.from_address < -1 or self.to_address < 0:
            raise ValueError(
                "Addresses must be non-negative integers (except -1 for mining)"
            )

        if self.from_address == self.to_address and self.from_address != -1:
            raise ValueError("Cannot send transaction to the same address")

    def calculate_hash(self) -> str:
        """
        Calculate the SHA256 hash of this transaction.

        Returns:
            The hexadecimal hash string of the transaction data
        """
        transaction_string = (
            f"{self.from_address},{self.to_address},"
            f"{self.value},{self.fee},{self.timestamp}"
        )
        return hashlib.sha256(transaction_string.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert transaction to dictionary representation.

        Returns:
            Dictionary containing all transaction data
        """
        return {
            "from_address": self.from_address,
            "to_address": self.to_address,
            "value": self.value,
            "fee": self.fee,
            "timestamp": self.timestamp,
            "hash": self.calculate_hash(),
        }

    def to_json(self) -> str:
        """
        Convert transaction to JSON string.

        Returns:
            JSON string representation of the transaction
        """
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        """
        Create transaction from dictionary.

        Args:
            data: Dictionary containing transaction data

        Returns:
            New Transaction instance
        """
        return cls(
            from_address=data["from_address"],
            to_address=data["to_address"],
            value=data["value"],
            fee=data.get("fee", 0),
            timestamp=data.get("timestamp"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Transaction":
        """
        Create transaction from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            New Transaction instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __str__(self) -> str:
        """String representation of the transaction."""
        return f"Transaction({self.from_address} -> {self.to_address}: {self.value})"

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return (
            f"Transaction(from_address={self.from_address}, "
            f"to_address={self.to_address}, value={self.value}, "
            f"fee={self.fee}, timestamp={self.timestamp})"
        )
