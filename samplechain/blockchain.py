"""
Blockchain module for the SampleChain blockchain.

This module contains the Blockchain class which manages the chain of blocks,
validates transactions, maintains balances, and provides the main blockchain
functionality.
"""

import json
from typing import List, Dict, Optional
from collections import defaultdict

from .block import Block
from .transaction import Transaction


class BlockchainError(Exception):
    """Base exception for blockchain operations."""

    pass


class InvalidTransactionError(BlockchainError):
    """Raised when a transaction is invalid."""

    pass


class InvalidBlockError(BlockchainError):
    """Raised when a block is invalid."""

    pass


class Blockchain:
    """
    Manages the blockchain and maintains account balances.

    The blockchain maintains a list of valid blocks, tracks account balances,
    validates new transactions and blocks, and provides methods for querying
    the blockchain state.

    Attributes:
        chain: List of blocks in the blockchain
        pending_transactions: List of transactions waiting to be mined
        balances: Dictionary mapping addresses to their current balances
        difficulty: Current mining difficulty
        mining_reward: Reward given to miners for mining a block
    """

    def __init__(
        self,
        initial_balances: Optional[Dict[int, int]] = None,
        difficulty: int = 4,
        mining_reward: int = 10,
    ) -> None:
        """
        Initialize a new blockchain.

        Args:
            initial_balances: Starting balances for addresses
            difficulty: Mining difficulty (number of leading zeros)
            mining_reward: Reward for mining a block
        """
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.balances: Dict[int, int] = defaultdict(int)
        self.difficulty = difficulty
        self.mining_reward = mining_reward

        # Set initial balances
        if initial_balances:
            self.balances.update(initial_balances)

        # Create genesis block with no difficulty requirement
        genesis_block = Block.create_genesis_block()
        genesis_block.difficulty = 0  # Genesis block doesn't need proof-of-work
        self.chain.append(genesis_block)

    def get_latest_block(self) -> Block:
        """
        Get the most recent block in the chain.

        Returns:
            The latest block
        """
        return self.chain[-1]

    def get_balance(self, address: int) -> int:
        """
        Get the current balance for an address.

        Args:
            address: The address to check

        Returns:
            Current balance for the address
        """
        return self.balances[address]

    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Add a new transaction to the pending transactions pool.

        Args:
            transaction: The transaction to add

        Returns:
            True if transaction was added successfully

        Raises:
            InvalidTransactionError: If transaction is invalid
        """
        if not self.is_transaction_valid(transaction):
            raise InvalidTransactionError(
                f"Transaction {transaction} is invalid: insufficient balance"
            )

        self.pending_transactions.append(transaction)
        return True

    def is_transaction_valid(
        self, transaction: Transaction, temp_balances: Optional[Dict[int, int]] = None
    ) -> bool:
        """
        Check if a transaction is valid given current or temporary balances.

        Args:
            transaction: The transaction to validate
            temp_balances: Temporary balances to use (defaults to current balances)

        Returns:
            True if transaction is valid
        """
        balances = temp_balances if temp_balances is not None else self.balances
        sender_balance = balances.get(transaction.from_address, 0)
        total_cost = transaction.value + transaction.fee

        return sender_balance >= total_cost

    def validate_transactions_for_block(
        self, transactions: List[Transaction], block_size: int
    ) -> List[Transaction]:
        """
        Validate and select transactions for inclusion in a block.

        Validates transactions against current blockchain balances, tracking
        temporary balance changes within the block to prevent double-spending.

        Args:
            transactions: List of candidate transactions
            block_size: Maximum number of transactions per block

        Returns:
            List of valid transactions to include in block
        """
        valid_transactions = []
        # Track balance changes within this block
        temp_balances = self.balances.copy()

        for transaction in transactions[:]:  # Work on a copy
            if len(valid_transactions) >= block_size:
                break

            # Validate against temporary balances (updated within this block)
            if self.is_transaction_valid(transaction, temp_balances):
                valid_transactions.append(transaction)
                # Update temporary balances
                temp_balances[transaction.from_address] -= (
                    transaction.value + transaction.fee
                )
                temp_balances[transaction.to_address] += transaction.value

        return valid_transactions

    def mine_pending_transactions(
        self, miner_address: int, block_size: int = 10
    ) -> Optional[Block]:
        """
        Mine pending transactions into a new block.

        Args:
            miner_address: Address to receive mining reward
            block_size: Maximum number of transactions per block

        Returns:
            The newly mined block, or None if no valid transactions
        """
        if not self.pending_transactions:
            return None

        # Validate and select transactions
        valid_transactions = self.validate_transactions_for_block(
            self.pending_transactions, block_size
        )

        if not valid_transactions:
            return None

        # Add mining reward transaction
        if self.mining_reward > 0:
            reward_transaction = Transaction(
                from_address=-1,  # Special address for mining rewards
                to_address=miner_address,
                value=self.mining_reward,
                fee=0,
            )
            valid_transactions.insert(0, reward_transaction)

        # Create new block
        new_block = Block(
            index=len(self.chain),
            transactions=valid_transactions,
            previous_hash=self.get_latest_block().calculate_hash(),
            difficulty=self.difficulty,
        )

        return new_block

    def add_block(self, block: Block, skip_mining: bool = False) -> bool:
        """
        Add a new block to the blockchain.

        Args:
            block: The block to add
            skip_mining: Skip proof-of-work validation (for testing)

        Returns:
            True if block was added successfully

        Raises:
            InvalidBlockError: If block is invalid
        """
        if not self.is_block_valid(block, skip_mining):
            raise InvalidBlockError(f"Block {block.index} is invalid")

        # Apply transactions to balances
        for transaction in block.transactions:
            if transaction.from_address != -1:  # Not a mining reward
                self.balances[transaction.from_address] -= (
                    transaction.value + transaction.fee
                )
            self.balances[transaction.to_address] += transaction.value

        # Add block to chain
        self.chain.append(block)

        # Remove processed transactions from pending
        for transaction in block.transactions:
            if transaction in self.pending_transactions:
                self.pending_transactions.remove(transaction)

        return True

    def is_block_valid(self, block: Block, skip_mining: bool = False) -> bool:
        """
        Validate a block against the current blockchain state.

        Args:
            block: The block to validate
            skip_mining: Skip proof-of-work validation

        Returns:
            True if block is valid
        """
        # Check block index
        if block.index != len(self.chain):
            return False

        # Check previous hash
        if block.previous_hash != self.get_latest_block().calculate_hash():
            return False

        # Check proof-of-work (unless skipped)
        if not skip_mining and not block.is_hash_valid():
            return False

        # Validate all transactions in the block
        temp_balances = self.balances.copy()
        for transaction in block.transactions:
            if transaction.from_address != -1:  # Not a mining reward
                if not self.is_transaction_valid(transaction, temp_balances):
                    return False
                temp_balances[transaction.from_address] -= (
                    transaction.value + transaction.fee
                )
            temp_balances[transaction.to_address] += transaction.value

        return True

    def is_chain_valid(self, validate_mining: bool = False) -> bool:
        """
        Validate the entire blockchain.

        Args:
            validate_mining: Whether to validate proof-of-work (default False for testing compatibility)

        Returns:
            True if the entire chain is valid
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Check if current block is valid (optionally validate mining)
            if validate_mining and not current_block.is_hash_valid():
                return False

            # Check if current block points to previous block
            if current_block.previous_hash != previous_block.calculate_hash():
                return False

        return True

    def get_transaction_history(self, address: int) -> List[Transaction]:
        """
        Get all transactions involving a specific address.

        Args:
            address: The address to search for

        Returns:
            List of transactions involving the address
        """
        transactions = []
        for block in self.chain:
            for transaction in block.transactions:
                if (
                    transaction.from_address == address
                    or transaction.to_address == address
                ):
                    transactions.append(transaction)
        return transactions

    def get_chain_stats(self) -> Dict[str, any]:
        """
        Get statistics about the blockchain.

        Returns:
            Dictionary with blockchain statistics
        """
        total_transactions = sum(len(block.transactions) for block in self.chain)
        total_value = sum(
            sum(tx.value for tx in block.transactions) for block in self.chain
        )

        return {
            "total_blocks": len(self.chain),
            "total_transactions": total_transactions,
            "total_value_transferred": total_value,
            "pending_transactions": len(self.pending_transactions),
            "difficulty": self.difficulty,
            "mining_reward": self.mining_reward,
            "total_addresses": len(
                [addr for addr, balance in self.balances.items() if balance > 0]
            ),
        }

    def save_to_file(self, filename: str) -> None:
        """
        Save the blockchain to a file.

        Args:
            filename: Path to save the blockchain
        """
        data = {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            "balances": dict(self.balances),
            "difficulty": self.difficulty,
            "mining_reward": self.mining_reward,
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filename: str) -> "Blockchain":
        """
        Load a blockchain from a file.

        Args:
            filename: Path to load the blockchain from

        Returns:
            Loaded Blockchain instance
        """
        with open(filename, "r") as f:
            data = json.load(f)

        # Create new blockchain (will create genesis block)
        blockchain = cls(
            difficulty=data["difficulty"], mining_reward=data["mining_reward"]
        )

        # Clear the auto-created genesis block
        blockchain.chain = []

        # Load blocks
        for block_data in data["chain"]:
            block = Block.from_dict(block_data)
            blockchain.chain.append(block)

        # Load pending transactions
        blockchain.pending_transactions = [
            Transaction.from_dict(tx_data) for tx_data in data["pending_transactions"]
        ]

        # Load balances (convert string keys back to integers)
        blockchain.balances = defaultdict(int)
        for addr_str, balance in data["balances"].items():
            blockchain.balances[int(addr_str)] = balance

        return blockchain

    def __str__(self) -> str:
        """String representation of the blockchain."""
        return (
            f"Blockchain({len(self.chain)} blocks, "
            f"{len(self.pending_transactions)} pending transactions)"
        )

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return (
            f"Blockchain(blocks={len(self.chain)}, "
            f"pending={len(self.pending_transactions)}, "
            f"difficulty={self.difficulty})"
        )
