"""
Miner module for the SampleChain blockchain.

This module contains the Miner class which handles proof-of-work mining,
finding valid nonces for blocks, and managing mining operations.
"""

import time
import multiprocessing as mp
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from .block import Block
from .blockchain import Blockchain


class MiningError(Exception):
    """Raised when mining operations fail."""

    pass


class Miner:
    """
    Handles proof-of-work mining for blocks.

    The miner finds valid nonces for blocks by testing different values
    until the block hash meets the difficulty requirement. Supports both
    single-threaded and multi-threaded mining.

    Attributes:
        max_nonce: Maximum nonce value to try before giving up
        progress_callback: Optional callback function for mining progress
    """

    def __init__(
        self,
        max_nonce: int = 1000000,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> None:
        """
        Initialize a new miner.

        Args:
            max_nonce: Maximum nonce to try before giving up
            progress_callback: Function called with (nonce, hash) during mining
        """
        self.max_nonce = max_nonce
        self.progress_callback = progress_callback
        self._mining_stats = {"blocks_mined": 0, "total_hashes": 0, "total_time": 0.0}

    def mine_block(self, block: Block) -> bool:
        """
        Mine a block by finding a valid nonce.

        This method modifies the block's nonce value until the block hash
        meets the difficulty requirement.

        Args:
            block: The block to mine

        Returns:
            True if mining was successful, False if max_nonce was reached

        Raises:
            MiningError: If mining fails due to invalid block
        """
        if block.difficulty < 1:
            raise MiningError("Block difficulty must be at least 1")

        start_time = time.time()
        target_prefix = "0" * block.difficulty

        for nonce in range(self.max_nonce):
            block.nonce = nonce
            current_hash = block.calculate_hash()

            # Call progress callback if provided
            if self.progress_callback and nonce % 1000 == 0:
                self.progress_callback(nonce, current_hash)

            if current_hash.startswith(target_prefix):
                # Mining successful
                end_time = time.time()
                mining_time = end_time - start_time

                # Update statistics
                self._mining_stats["blocks_mined"] += 1
                self._mining_stats["total_hashes"] += nonce + 1
                self._mining_stats["total_time"] += mining_time

                return True

        # Max nonce reached without finding valid hash
        return False

    def mine_block_parallel(
        self, block: Block, num_workers: Optional[int] = None
    ) -> bool:
        """
        Mine a block using multiple threads for better performance.

        Divides the nonce search space among multiple worker threads.

        Args:
            block: The block to mine
            num_workers: Number of worker threads (defaults to CPU count)

        Returns:
            True if mining was successful, False if max_nonce was reached
        """
        if num_workers is None:
            num_workers = mp.cpu_count()

        start_time = time.time()
        chunk_size = self.max_nonce // num_workers

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit mining tasks for different nonce ranges
            futures = []
            for i in range(num_workers):
                start_nonce = i * chunk_size
                end_nonce = (
                    start_nonce + chunk_size if i < num_workers - 1 else self.max_nonce
                )

                future = executor.submit(
                    self._mine_range,
                    block.copy() if hasattr(block, "copy") else self._copy_block(block),
                    start_nonce,
                    end_nonce,
                )
                futures.append(future)

            # Wait for first successful result
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    # Mining successful - update original block
                    nonce, mining_hash = result
                    block.nonce = nonce

                    # Cancel remaining tasks
                    for f in futures:
                        f.cancel()

                    # Update statistics
                    end_time = time.time()
                    mining_time = end_time - start_time
                    self._mining_stats["blocks_mined"] += 1
                    self._mining_stats["total_hashes"] += nonce + 1
                    self._mining_stats["total_time"] += mining_time

                    return True

        return False

    def _mine_range(
        self, block: Block, start_nonce: int, end_nonce: int
    ) -> Optional[tuple]:
        """
        Mine a block within a specific nonce range.

        Args:
            block: Block to mine (should be a copy)
            start_nonce: Starting nonce value
            end_nonce: Ending nonce value

        Returns:
            Tuple of (nonce, hash) if successful, None otherwise
        """
        target_prefix = "0" * block.difficulty

        for nonce in range(start_nonce, end_nonce):
            block.nonce = nonce
            current_hash = block.calculate_hash()

            if current_hash.startswith(target_prefix):
                return (nonce, current_hash)

        return None

    def _copy_block(self, block: Block) -> Block:
        """Create a copy of a block for parallel mining."""
        return Block(
            index=block.index,
            transactions=block.transactions.copy(),
            timestamp=block.timestamp,
            previous_hash=block.previous_hash,
            nonce=block.nonce,
            difficulty=block.difficulty,
        )

    def estimate_mining_time(
        self, difficulty: int, hash_rate: Optional[int] = None
    ) -> float:
        """
        Estimate time required to mine a block with given difficulty.

        Args:
            difficulty: Mining difficulty (number of leading zeros)
            hash_rate: Hashes per second (estimated from previous mining if None)

        Returns:
            Estimated mining time in seconds
        """
        if hash_rate is None:
            # Estimate based on previous mining statistics
            if self._mining_stats["total_time"] > 0:
                hash_rate = (
                    self._mining_stats["total_hashes"]
                    / self._mining_stats["total_time"]
                )
            else:
                # Default estimate
                hash_rate = 1000  # Hashes per second

        # Expected number of hashes needed
        expected_hashes = 16**difficulty

        return expected_hashes / hash_rate

    def mine_blockchain(
        self,
        blockchain: Blockchain,
        miner_address: int,
        num_blocks: int = 1,
        block_size: int = 10,
        use_parallel: bool = True,
    ) -> int:
        """
        Mine multiple blocks on a blockchain.

        Args:
            blockchain: The blockchain to mine on
            miner_address: Address to receive mining rewards
            num_blocks: Number of blocks to mine
            block_size: Maximum transactions per block
            use_parallel: Whether to use parallel mining

        Returns:
            Number of blocks successfully mined
        """
        blocks_mined = 0

        for _ in range(num_blocks):
            # Mine pending transactions
            new_block = blockchain.mine_pending_transactions(miner_address, block_size)

            if new_block is None:
                # No transactions to mine
                break

            # Mine the block
            mining_method = (
                self.mine_block_parallel if use_parallel else self.mine_block
            )

            if mining_method(new_block):
                # Add mined block to blockchain
                blockchain.add_block(new_block)
                blocks_mined += 1
            else:
                # Mining failed (max nonce reached)
                break

        return blocks_mined

    def get_mining_stats(self) -> dict:
        """
        Get mining statistics.

        Returns:
            Dictionary with mining performance statistics
        """
        stats = self._mining_stats.copy()

        if stats["total_time"] > 0:
            stats["average_hash_rate"] = stats["total_hashes"] / stats["total_time"]
            stats["average_mining_time"] = stats["total_time"] / max(
                stats["blocks_mined"], 1
            )
        else:
            stats["average_hash_rate"] = 0
            stats["average_mining_time"] = 0

        return stats

    def reset_stats(self) -> None:
        """Reset mining statistics."""
        self._mining_stats = {"blocks_mined": 0, "total_hashes": 0, "total_time": 0.0}

    @staticmethod
    def calculate_difficulty_adjustment(blocks: list, target_time: int = 600) -> int:
        """
        Calculate difficulty adjustment based on block times.

        Analyzes the last few blocks to determine if difficulty should be
        adjusted to maintain target block time.

        Args:
            blocks: List of recent blocks
            target_time: Target time between blocks in seconds

        Returns:
            New difficulty level
        """
        if len(blocks) < 2:
            return blocks[0].difficulty if blocks else 4

        # Calculate average time between blocks
        time_diffs = []
        for i in range(1, len(blocks)):
            time_diff = blocks[i].timestamp - blocks[i - 1].timestamp
            time_diffs.append(time_diff)

        average_time = sum(time_diffs) / len(time_diffs)
        current_difficulty = blocks[-1].difficulty

        # Adjust difficulty based on average time
        if average_time < target_time * 0.5:
            # Blocks being mined too fast - increase difficulty
            return min(current_difficulty + 1, 8)
        elif average_time > target_time * 2:
            # Blocks being mined too slow - decrease difficulty
            return max(current_difficulty - 1, 1)
        else:
            # Time is acceptable - keep current difficulty
            return current_difficulty

    def __str__(self) -> str:
        """String representation of the miner."""
        stats = self.get_mining_stats()
        return (
            f"Miner(blocks_mined={stats['blocks_mined']}, "
            f"avg_hash_rate={stats['average_hash_rate']:.1f} H/s)"
        )

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return f"Miner(max_nonce={self.max_nonce})"
