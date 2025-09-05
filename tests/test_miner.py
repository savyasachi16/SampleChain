"""
Tests for the Miner class.
"""

import pytest
from unittest.mock import patch
from samplechain.miner import Miner, MiningError
from samplechain.block import Block
from samplechain.transaction import Transaction
from samplechain.blockchain import Blockchain


class TestMiner:
    """Test cases for the Miner class."""
    
    def test_miner_initialization(self) -> None:
        """Test creating a new miner."""
        miner = Miner()
        
        assert miner.max_nonce == 1000000
        assert miner.progress_callback is None
        assert miner._mining_stats["blocks_mined"] == 0
        assert miner._mining_stats["total_hashes"] == 0
        assert miner._mining_stats["total_time"] == 0.0
    
    def test_miner_with_custom_parameters(self) -> None:
        """Test creating miner with custom parameters."""
        def dummy_callback(nonce: int, hash_str: str) -> None:
            pass
        
        miner = Miner(max_nonce=500000, progress_callback=dummy_callback)
        
        assert miner.max_nonce == 500000
        assert miner.progress_callback is dummy_callback
    
    def test_mine_block_easy_difficulty(self) -> None:
        """Test mining a block with easy difficulty."""
        miner = Miner(max_nonce=10000)
        
        # Create block with difficulty 1 (should be quick to mine)
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx], difficulty=1)
        
        result = miner.mine_block(block)
        
        assert result is True
        assert block.nonce > 0
        assert block.is_hash_valid()
        assert miner._mining_stats["blocks_mined"] == 1
        assert miner._mining_stats["total_hashes"] > 0
    
    def test_mine_block_impossible_difficulty(self) -> None:
        """Test mining fails with impossible difficulty in limited nonce range."""
        miner = Miner(max_nonce=100)  # Very low max nonce
        
        # Create block with high difficulty
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx], difficulty=8)
        
        result = miner.mine_block(block)
        
        assert result is False
        assert block.nonce == 99  # Should reach max_nonce - 1
        assert not block.is_hash_valid()  # Unlikely to find valid hash
    
    def test_mine_block_with_progress_callback(self) -> None:
        """Test mining with progress callback."""
        callback_calls = []
        
        def progress_callback(nonce: int, hash_str: str) -> None:
            callback_calls.append((nonce, hash_str))
        
        miner = Miner(max_nonce=5000, progress_callback=progress_callback)
        
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx], difficulty=1)
        
        miner.mine_block(block)
        
        # Should have some callback calls (every 1000 nonces)
        assert len(callback_calls) > 0
        for nonce, hash_str in callback_calls:
            assert nonce % 1000 == 0
            assert isinstance(hash_str, str)
            assert len(hash_str) == 64
    
    def test_mine_block_invalid_difficulty(self) -> None:
        """Test mining with invalid difficulty raises error."""
        miner = Miner()
        
        block = Block(index=1, transactions=[], difficulty=0)
        
        with pytest.raises(MiningError, match="Block difficulty must be at least 1"):
            miner.mine_block(block)
    
    def test_mine_block_parallel_success(self) -> None:
        """Test parallel mining succeeds."""
        miner = Miner(max_nonce=10000)
        
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx], difficulty=1)
        
        result = miner.mine_block_parallel(block, num_workers=2)
        
        assert result is True
        assert block.nonce > 0
        assert block.is_hash_valid()
        assert miner._mining_stats["blocks_mined"] == 1
    
    def test_mine_block_parallel_failure(self) -> None:
        """Test parallel mining fails with impossible parameters."""
        miner = Miner(max_nonce=50)  # Very low max nonce
        
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx], difficulty=8)  # Very high difficulty
        
        result = miner.mine_block_parallel(block, num_workers=2)
        
        assert result is False
    
    def test_mine_range_success(self) -> None:
        """Test mining within a specific nonce range."""
        miner = Miner()
        
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx], difficulty=1)
        
        result = miner._mine_range(block, 0, 1000)
        
        if result is not None:  # May or may not find valid nonce in range
            nonce, hash_value = result
            assert 0 <= nonce < 1000
            assert isinstance(hash_value, str)
            assert hash_value.startswith("0")
    
    def test_mine_range_no_success(self) -> None:
        """Test mining range returns None when no valid nonce found."""
        miner = Miner()
        
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx], difficulty=8)  # Very high difficulty
        
        result = miner._mine_range(block, 0, 10)  # Very small range
        
        # Very unlikely to find valid hash in such small range with high difficulty
        assert result is None
    
    def test_copy_block(self) -> None:
        """Test block copying for parallel mining."""
        miner = Miner()
        
        tx = Transaction(from_address=1, to_address=2, value=100)
        original_block = Block(index=1, transactions=[tx], nonce=1000, difficulty=3)
        
        copied_block = miner._copy_block(original_block)
        
        assert copied_block.index == original_block.index
        assert len(copied_block.transactions) == len(original_block.transactions)
        assert copied_block.nonce == original_block.nonce
        assert copied_block.difficulty == original_block.difficulty
        assert copied_block is not original_block  # Should be different objects
    
    def test_estimate_mining_time_with_hash_rate(self) -> None:
        """Test mining time estimation with provided hash rate."""
        miner = Miner()
        
        # Test with 1000 H/s and difficulty 2
        estimated_time = miner.estimate_mining_time(difficulty=2, hash_rate=1000)
        
        # Expected hashes for difficulty 2: 16^2 = 256
        expected_time = 256 / 1000
        assert abs(estimated_time - expected_time) < 0.001
    
    def test_estimate_mining_time_from_stats(self) -> None:
        """Test mining time estimation using previous mining statistics."""
        miner = Miner(max_nonce=1000)
        
        # Do some mining to generate stats
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx], difficulty=1)
        miner.mine_block(block)
        
        # Now estimate time for same difficulty
        estimated_time = miner.estimate_mining_time(difficulty=1)
        
        assert estimated_time > 0
        assert isinstance(estimated_time, float)
    
    def test_estimate_mining_time_no_stats(self) -> None:
        """Test mining time estimation with no previous statistics."""
        miner = Miner()
        
        estimated_time = miner.estimate_mining_time(difficulty=3)
        
        # Should use default hash rate of 1000 H/s
        # Expected hashes for difficulty 3: 16^3 = 4096
        expected_time = 4096 / 1000
        assert abs(estimated_time - expected_time) < 0.001
    
    def test_mine_blockchain_success(self) -> None:
        """Test mining multiple blocks on a blockchain."""
        initial_balances = {0: 1000, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        miner = Miner(max_nonce=10000)
        
        # Add transactions
        for i in range(1, 6):
            tx = Transaction(from_address=0, to_address=i, value=50)
            blockchain.add_transaction(tx)
        
        blocks_mined = miner.mine_blockchain(
            blockchain=blockchain,
            miner_address=99,
            num_blocks=3,
            block_size=2,
            use_parallel=False
        )
        
        assert blocks_mined > 0
        assert len(blockchain.chain) > 1  # Should have more than genesis block
        assert blockchain.get_balance(99) > 0  # Miner should have rewards
        assert miner._mining_stats["blocks_mined"] == blocks_mined
    
    def test_mine_blockchain_no_transactions(self) -> None:
        """Test mining blockchain with no pending transactions."""
        blockchain = Blockchain()
        miner = Miner()
        
        blocks_mined = miner.mine_blockchain(
            blockchain=blockchain,
            miner_address=99,
            num_blocks=5
        )
        
        assert blocks_mined == 0
        assert len(blockchain.chain) == 1  # Only genesis block
    
    def test_mine_blockchain_parallel(self) -> None:
        """Test mining blockchain with parallel mining enabled."""
        initial_balances = {0: 500}
        blockchain = Blockchain(initial_balances=initial_balances)
        miner = Miner(max_nonce=5000)
        
        # Add some transactions
        for i in range(1, 4):
            tx = Transaction(from_address=0, to_address=i, value=50)
            blockchain.add_transaction(tx)
        
        blocks_mined = miner.mine_blockchain(
            blockchain=blockchain,
            miner_address=99,
            num_blocks=2,
            use_parallel=True
        )
        
        assert blocks_mined > 0
        assert miner._mining_stats["blocks_mined"] == blocks_mined
    
    def test_get_mining_stats_empty(self) -> None:
        """Test getting mining statistics with no mining done."""
        miner = Miner()
        stats = miner.get_mining_stats()
        
        assert stats["blocks_mined"] == 0
        assert stats["total_hashes"] == 0
        assert stats["total_time"] == 0.0
        assert stats["average_hash_rate"] == 0
        assert stats["average_mining_time"] == 0
    
    def test_get_mining_stats_with_data(self) -> None:
        """Test getting mining statistics after mining."""
        miner = Miner(max_nonce=5000)
        
        # Mine a block
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx], difficulty=1)
        miner.mine_block(block)
        
        stats = miner.get_mining_stats()
        
        assert stats["blocks_mined"] == 1
        assert stats["total_hashes"] > 0
        assert stats["total_time"] > 0
        assert stats["average_hash_rate"] > 0
        assert stats["average_mining_time"] > 0
    
    def test_reset_stats(self) -> None:
        """Test resetting mining statistics."""
        miner = Miner(max_nonce=5000)
        
        # Mine a block to generate stats
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx], difficulty=1)
        miner.mine_block(block)
        
        # Reset stats
        miner.reset_stats()
        
        stats = miner.get_mining_stats()
        assert stats["blocks_mined"] == 0
        assert stats["total_hashes"] == 0
        assert stats["total_time"] == 0.0
    
    def test_calculate_difficulty_adjustment_no_blocks(self) -> None:
        """Test difficulty adjustment with no blocks."""
        result = Miner.calculate_difficulty_adjustment([])
        assert result == 4  # Default difficulty
    
    def test_calculate_difficulty_adjustment_one_block(self) -> None:
        """Test difficulty adjustment with one block."""
        block = Block(index=0, transactions=[], difficulty=3)
        result = Miner.calculate_difficulty_adjustment([block])
        assert result == 3  # Should return current difficulty
    
    def test_calculate_difficulty_adjustment_increase(self) -> None:
        """Test difficulty adjustment increases when blocks too fast."""
        # Create blocks with timestamps indicating fast mining
        block1 = Block(index=0, transactions=[], timestamp=1000, difficulty=3)
        block2 = Block(index=1, transactions=[], timestamp=1100, difficulty=3)  # 100s gap
        block3 = Block(index=2, transactions=[], timestamp=1200, difficulty=3)  # 100s gap
        
        blocks = [block1, block2, block3]
        target_time = 600  # 10 minutes
        
        result = Miner.calculate_difficulty_adjustment(blocks, target_time)
        
        # Average time is 100s, which is < target_time * 0.5 (300s)
        # So difficulty should increase
        assert result == 4  # Should increase from 3 to 4
    
    def test_calculate_difficulty_adjustment_decrease(self) -> None:
        """Test difficulty adjustment decreases when blocks too slow."""
        # Create blocks with timestamps indicating slow mining
        block1 = Block(index=0, transactions=[], timestamp=1000, difficulty=4)
        block2 = Block(index=1, transactions=[], timestamp=2500, difficulty=4)  # 1500s gap
        block3 = Block(index=2, transactions=[], timestamp=4000, difficulty=4)  # 1500s gap
        
        blocks = [block1, block2, block3]
        target_time = 600  # 10 minutes
        
        result = Miner.calculate_difficulty_adjustment(blocks, target_time)
        
        # Average time is 1500s, which is > target_time * 2 (1200s)
        # So difficulty should decrease
        assert result == 3  # Should decrease from 4 to 3
    
    def test_calculate_difficulty_adjustment_maintain(self) -> None:
        """Test difficulty adjustment maintains when timing is good."""
        # Create blocks with good timing
        block1 = Block(index=0, transactions=[], timestamp=1000, difficulty=4)
        block2 = Block(index=1, transactions=[], timestamp=1600, difficulty=4)  # 600s gap
        block3 = Block(index=2, transactions=[], timestamp=2200, difficulty=4)  # 600s gap
        
        blocks = [block1, block2, block3]
        target_time = 600  # 10 minutes
        
        result = Miner.calculate_difficulty_adjustment(blocks, target_time)
        
        # Average time is 600s, which is exactly target_time
        # So difficulty should stay the same
        assert result == 4  # Should maintain current difficulty
    
    def test_calculate_difficulty_adjustment_bounds(self) -> None:
        """Test difficulty adjustment respects bounds."""
        # Test maximum difficulty bound
        block1 = Block(index=0, transactions=[], timestamp=1000, difficulty=8)
        block2 = Block(index=1, transactions=[], timestamp=1010, difficulty=8)  # Very fast
        
        result = Miner.calculate_difficulty_adjustment([block1, block2], 600)
        assert result <= 8  # Should not exceed maximum
        
        # Test minimum difficulty bound
        block3 = Block(index=0, transactions=[], timestamp=1000, difficulty=1)
        block4 = Block(index=1, transactions=[], timestamp=3000, difficulty=1)  # Very slow
        
        result = Miner.calculate_difficulty_adjustment([block3, block4], 600)
        assert result >= 1  # Should not go below minimum
    
    def test_string_representations(self) -> None:
        """Test string representations of miner."""
        miner = Miner(max_nonce=500000)
        
        # Test before mining
        str_repr = str(miner)
        assert "Miner(blocks_mined=0" in str_repr
        assert "avg_hash_rate=" in str_repr
        
        repr_str = repr(miner)
        assert "Miner(max_nonce=500000)" in repr_str
        
        # Mine a block to get some stats
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx], difficulty=1)
        miner.mine_block(block)
        
        # Test after mining
        str_repr_after = str(miner)
        assert "blocks_mined=1" in str_repr_after