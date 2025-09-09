"""
Tests for the Blockchain class.
"""

import os
import tempfile
import pytest
from samplechain.blockchain import Blockchain, InvalidTransactionError, InvalidBlockError
from samplechain.block import Block
from samplechain.transaction import Transaction


class TestBlockchain:
    """Test cases for the Blockchain class."""
    
    def test_blockchain_initialization(self) -> None:
        """Test creating a new blockchain."""
        blockchain = Blockchain()
        
        assert len(blockchain.chain) == 1  # Genesis block
        assert len(blockchain.pending_transactions) == 0
        assert blockchain.difficulty == 4
        assert blockchain.mining_reward == 10
    
    def test_blockchain_with_initial_balances(self) -> None:
        """Test creating blockchain with initial balances."""
        initial_balances = {0: 100, 1: 50, 2: 25}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        assert blockchain.get_balance(0) == 100
        assert blockchain.get_balance(1) == 50
        assert blockchain.get_balance(2) == 25
        assert blockchain.get_balance(999) == 0  # Non-existent address
    
    def test_custom_difficulty_and_reward(self) -> None:
        """Test blockchain with custom difficulty and mining reward."""
        blockchain = Blockchain(difficulty=6, mining_reward=25)
        
        assert blockchain.difficulty == 6
        assert blockchain.mining_reward == 25
    
    def test_get_latest_block(self) -> None:
        """Test getting the latest block."""
        blockchain = Blockchain()
        latest = blockchain.get_latest_block()
        
        assert latest.index == 0
        assert len(latest.transactions) == 0
    
    def test_add_valid_transaction(self) -> None:
        """Test adding a valid transaction."""
        initial_balances = {0: 100, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        tx = Transaction(from_address=0, to_address=1, value=50)
        result = blockchain.add_transaction(tx)
        
        assert result is True
        assert len(blockchain.pending_transactions) == 1
        assert blockchain.pending_transactions[0] == tx
    
    def test_add_invalid_transaction_insufficient_balance(self) -> None:
        """Test adding transaction with insufficient balance."""
        initial_balances = {0: 50, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        tx = Transaction(from_address=0, to_address=1, value=100)
        
        with pytest.raises(InvalidTransactionError):
            blockchain.add_transaction(tx)
    
    def test_add_transaction_with_fee(self) -> None:
        """Test adding transaction with fee."""
        initial_balances = {0: 100, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        tx = Transaction(from_address=0, to_address=1, value=50, fee=5)
        result = blockchain.add_transaction(tx)
        
        assert result is True
        assert len(blockchain.pending_transactions) == 1
    
    def test_add_transaction_insufficient_for_fee(self) -> None:
        """Test transaction fails when insufficient balance for value + fee."""
        initial_balances = {0: 50, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        tx = Transaction(from_address=0, to_address=1, value=50, fee=5)
        
        with pytest.raises(InvalidTransactionError):
            blockchain.add_transaction(tx)
    
    def test_is_transaction_valid(self) -> None:
        """Test transaction validation."""
        initial_balances = {0: 100, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        valid_tx = Transaction(from_address=0, to_address=1, value=50)
        invalid_tx = Transaction(from_address=0, to_address=1, value=150)
        
        assert blockchain.is_transaction_valid(valid_tx) is True
        assert blockchain.is_transaction_valid(invalid_tx) is False
    
    def test_validate_transactions_for_block(self) -> None:
        """Test validating transactions for block inclusion."""
        initial_balances = {0: 100, 1: 50, 2: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        tx1 = Transaction(from_address=0, to_address=2, value=30)  # Valid
        tx2 = Transaction(from_address=1, to_address=2, value=40)  # Valid  
        tx3 = Transaction(from_address=0, to_address=2, value=80)  # Invalid (insufficient after tx1)
        tx4 = Transaction(from_address=1, to_address=2, value=10)  # Valid
        
        transactions = [tx1, tx2, tx3, tx4]
        valid_txs = blockchain.validate_transactions_for_block(transactions, 10)
        
        assert len(valid_txs) == 3  # tx1, tx2, tx4 should be valid
        assert tx1 in valid_txs
        assert tx2 in valid_txs
        assert tx3 not in valid_txs
        assert tx4 in valid_txs
    
    def test_validate_transactions_respects_block_size(self) -> None:
        """Test that transaction validation respects block size limit."""
        initial_balances = {0: 1000}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        transactions = []
        for i in range(1, 6):  # Create 5 valid transactions
            tx = Transaction(from_address=0, to_address=i, value=10)
            transactions.append(tx)
        
        valid_txs = blockchain.validate_transactions_for_block(transactions, 3)
        
        assert len(valid_txs) == 3  # Should be limited by block_size
    
    def test_mine_pending_transactions_empty(self) -> None:
        """Test mining when no pending transactions."""
        blockchain = Blockchain()
        
        result = blockchain.mine_pending_transactions(miner_address=99)
        
        assert result is None
    
    def test_mine_pending_transactions_success(self) -> None:
        """Test successful mining of pending transactions."""
        initial_balances = {0: 100, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        tx = Transaction(from_address=0, to_address=1, value=50)
        blockchain.add_transaction(tx)
        
        block = blockchain.mine_pending_transactions(miner_address=99, block_size=10)
        
        assert block is not None
        assert block.index == 1
        assert len(block.transactions) == 2  # Original tx + mining reward
        
        # Check mining reward transaction
        reward_tx = block.transactions[0]
        assert reward_tx.from_address == -1
        assert reward_tx.to_address == 99
        assert reward_tx.value == blockchain.mining_reward
    
    def test_mine_pending_transactions_no_mining_reward(self) -> None:
        """Test mining with no mining reward."""
        initial_balances = {0: 100, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances, mining_reward=0)
        
        tx = Transaction(from_address=0, to_address=1, value=50)
        blockchain.add_transaction(tx)
        
        block = blockchain.mine_pending_transactions(miner_address=99)
        
        assert block is not None
        assert len(block.transactions) == 1  # Only original transaction
        assert block.transactions[0] == tx
    
    def test_add_block_success(self) -> None:
        """Test successfully adding a block to the blockchain."""
        initial_balances = {0: 100, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        tx = Transaction(from_address=0, to_address=1, value=50)
        blockchain.add_transaction(tx)
        
        block = blockchain.mine_pending_transactions(miner_address=99)
        result = blockchain.add_block(block, skip_mining=True)
        
        assert result is True
        assert len(blockchain.chain) == 2
        assert blockchain.get_balance(0) == 50  # 100 - 50
        assert blockchain.get_balance(1) == 50  # 0 + 50
        assert blockchain.get_balance(99) == 10  # Mining reward
        assert len(blockchain.pending_transactions) == 0  # Should be cleared
    
    def test_add_block_with_mining_reward(self) -> None:
        """Test adding block updates balances correctly with mining reward."""
        initial_balances = {0: 100, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        tx = Transaction(from_address=0, to_address=1, value=50, fee=5)
        blockchain.add_transaction(tx)
        
        block = blockchain.mine_pending_transactions(miner_address=99)
        blockchain.add_block(block, skip_mining=True)
        
        assert blockchain.get_balance(0) == 45  # 100 - 50 - 5
        assert blockchain.get_balance(1) == 50  # 0 + 50
        assert blockchain.get_balance(99) == 10  # Mining reward (fee not included)
    
    def test_add_invalid_block(self) -> None:
        """Test adding an invalid block."""
        blockchain = Blockchain()
        
        # Create block with wrong index
        invalid_block = Block(
            index=5,  # Should be 1
            transactions=[],
            previous_hash=blockchain.get_latest_block().calculate_hash()
        )
        
        with pytest.raises(InvalidBlockError):
            blockchain.add_block(invalid_block, skip_mining=True)
    
    def test_is_block_valid(self) -> None:
        """Test block validation."""
        initial_balances = {0: 100, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        # Valid block
        tx = Transaction(from_address=0, to_address=1, value=50)
        valid_block = Block(
            index=1,
            transactions=[tx],
            previous_hash=blockchain.get_latest_block().calculate_hash()
        )
        
        assert blockchain.is_block_valid(valid_block, skip_mining=True) is True
        
        # Invalid block (wrong index)
        invalid_block = Block(
            index=2,
            transactions=[tx],
            previous_hash=blockchain.get_latest_block().calculate_hash()
        )
        
        assert blockchain.is_block_valid(invalid_block, skip_mining=True) is False
    
    def test_is_chain_valid_empty_chain(self) -> None:
        """Test chain validation on genesis block only."""
        blockchain = Blockchain()
        
        assert blockchain.is_chain_valid() is True
    
    def test_is_chain_valid_with_blocks(self) -> None:
        """Test chain validation with multiple blocks."""
        initial_balances = {0: 1000}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        # Add a few valid blocks
        for i in range(3):
            tx = Transaction(from_address=0, to_address=i+1, value=50)
            blockchain.add_transaction(tx)
            block = blockchain.mine_pending_transactions(miner_address=99)
            blockchain.add_block(block, skip_mining=True)
        
        assert blockchain.is_chain_valid() is True
    
    def test_get_transaction_history(self) -> None:
        """Test getting transaction history for an address."""
        initial_balances = {0: 1000, 1: 0, 2: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        # Add transactions
        tx1 = Transaction(from_address=0, to_address=1, value=50)
        tx2 = Transaction(from_address=0, to_address=2, value=30)
        tx3 = Transaction(from_address=1, to_address=2, value=20)
        
        blockchain.add_transaction(tx1)
        blockchain.add_transaction(tx2)
        
        # Mine first block
        block1 = blockchain.mine_pending_transactions(miner_address=99, block_size=2)
        if block1:
            blockchain.add_block(block1, skip_mining=True)
        
        # Now address 1 has 50 coins, so tx3 should be valid
        blockchain.add_transaction(tx3)
        
        # Mine second block
        block2 = blockchain.mine_pending_transactions(miner_address=99, block_size=2)
        if block2:
            blockchain.add_block(block2, skip_mining=True)
        
        # Check transaction history
        history_0 = blockchain.get_transaction_history(0)
        history_1 = blockchain.get_transaction_history(1)
        
        # Address 0 should appear in tx1 and tx2 as sender
        assert len([tx for tx in history_0 if tx.from_address == 0]) >= 2
        
        # Address 1 should appear in tx1 as receiver and tx3 as sender
        addr_1_txs = [tx for tx in history_1 if tx.from_address == 1 or tx.to_address == 1]
        assert len(addr_1_txs) >= 2
    
    def test_get_chain_stats(self) -> None:
        """Test getting blockchain statistics."""
        initial_balances = {0: 1000}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        stats = blockchain.get_chain_stats()
        
        assert stats["total_blocks"] == 1  # Genesis block
        assert stats["total_transactions"] == 0
        assert stats["total_value_transferred"] == 0
        assert stats["pending_transactions"] == 0
        assert stats["difficulty"] == 4
        assert stats["mining_reward"] == 10
    
    def test_get_chain_stats_with_activity(self) -> None:
        """Test chain statistics with blockchain activity."""
        initial_balances = {0: 1000}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        # Add and mine some transactions
        tx1 = Transaction(from_address=0, to_address=1, value=100)
        tx2 = Transaction(from_address=0, to_address=2, value=50)
        blockchain.add_transaction(tx1)
        blockchain.add_transaction(tx2)
        
        block = blockchain.mine_pending_transactions(miner_address=99)
        blockchain.add_block(block, skip_mining=True)
        
        stats = blockchain.get_chain_stats()
        
        assert stats["total_blocks"] == 2  # Genesis + 1 mined block
        assert stats["total_transactions"] >= 2  # At least our 2 transactions
        assert stats["total_value_transferred"] >= 150  # At least 100 + 50
        assert stats["pending_transactions"] == 0
    
    def test_save_and_load_blockchain(self) -> None:
        """Test saving and loading blockchain from file."""
        initial_balances = {0: 1000, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances, difficulty=3, mining_reward=15)
        
        # Add some activity
        tx = Transaction(from_address=0, to_address=1, value=100)
        blockchain.add_transaction(tx)
        
        # Add pending transaction (not mined)
        pending_tx = Transaction(from_address=0, to_address=1, value=50)
        blockchain.add_transaction(pending_tx)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filename = f.name
        
        try:
            # Save blockchain
            blockchain.save_to_file(filename)
            
            # Load blockchain
            loaded_blockchain = Blockchain.load_from_file(filename)
            
            # Verify loaded blockchain
            assert len(loaded_blockchain.chain) == len(blockchain.chain)
            assert loaded_blockchain.difficulty == 3
            assert loaded_blockchain.mining_reward == 15
            assert loaded_blockchain.get_balance(0) == 1000
            assert loaded_blockchain.get_balance(1) == 0
            assert len(loaded_blockchain.pending_transactions) == 2
            
        finally:
            if os.path.exists(filename):
                os.unlink(filename)
    
    def test_string_representations(self) -> None:
        """Test string representations of blockchain."""
        initial_balances = {0: 100}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        # Add a pending transaction
        tx = Transaction(from_address=0, to_address=1, value=50)
        blockchain.add_transaction(tx)
        
        str_repr = str(blockchain)
        assert "Blockchain(1 blocks" in str_repr
        assert "1 pending transactions" in str_repr
        
        repr_str = repr(blockchain)
        assert "Blockchain(blocks=1" in repr_str
        assert "pending=1" in repr_str
        assert "difficulty=4" in repr_str
    
    def test_transaction_validation_with_temp_balances(self) -> None:
        """Test transaction validation with temporary balances."""
        initial_balances = {0: 100, 1: 0}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        tx = Transaction(from_address=0, to_address=1, value=150)
        temp_balances = {0: 200, 1: 0}
        
        # Should be invalid with real balances
        assert blockchain.is_transaction_valid(tx) is False
        
        # Should be valid with temp balances
        assert blockchain.is_transaction_valid(tx, temp_balances) is True
    
    def test_multiple_blocks_mining(self) -> None:
        """Test mining multiple blocks in sequence."""
        initial_balances = {0: 1000}
        blockchain = Blockchain(initial_balances=initial_balances)
        
        # Add multiple transactions
        for i in range(1, 6):
            tx = Transaction(from_address=0, to_address=i, value=50)
            blockchain.add_transaction(tx)
        
        # Mine blocks with limited size
        blocks_mined = 0
        while blockchain.pending_transactions and blocks_mined < 3:
            block = blockchain.mine_pending_transactions(miner_address=99, block_size=2)
            if block:
                blockchain.add_block(block, skip_mining=True)
                blocks_mined += 1
        
        assert len(blockchain.chain) > 1  # Should have more than genesis
        assert len(blockchain.pending_transactions) < 5  # Some transactions should be processed
        assert blockchain.get_balance(99) > 0  # Miner should have rewards