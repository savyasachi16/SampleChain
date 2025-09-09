"""
Tests for the Block class.
"""

import json
import time
import pytest
from samplechain.block import Block
from samplechain.transaction import Transaction


class TestBlock:
    """Test cases for the Block class."""
    
    def test_valid_block_creation(self) -> None:
        """Test creating a valid block."""
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx])
        
        assert block.index == 1
        assert len(block.transactions) == 1
        assert block.transactions[0] == tx
        assert block.nonce == 0
        assert block.difficulty == 4
        assert len(block.previous_hash) == 64
    
    def test_empty_block_creation(self) -> None:
        """Test creating a block with no transactions."""
        block = Block(index=0, transactions=[])
        
        assert block.index == 0
        assert len(block.transactions) == 0
    
    def test_custom_parameters(self) -> None:
        """Test creating a block with custom parameters."""
        tx = Transaction(from_address=1, to_address=2, value=100)
        custom_time = int(time.time())
        
        block = Block(
            index=5,
            transactions=[tx],
            timestamp=custom_time,
            previous_hash="a" * 64,
            nonce=12345,
            difficulty=6
        )
        
        assert block.index == 5
        assert block.timestamp == custom_time
        assert block.previous_hash == "a" * 64
        assert block.nonce == 12345
        assert block.difficulty == 6
    
    def test_invalid_negative_index(self) -> None:
        """Test that negative index raises ValueError."""
        with pytest.raises(ValueError, match="Block index must be non-negative"):
            Block(index=-1, transactions=[])
    
    def test_invalid_difficulty(self) -> None:
        """Test that invalid difficulty raises ValueError."""
        with pytest.raises(ValueError, match="Difficulty must be non-negative"):
            Block(index=0, transactions=[], difficulty=-1)
    
    def test_invalid_previous_hash_length(self) -> None:
        """Test that invalid previous hash length raises ValueError."""
        with pytest.raises(ValueError, match="Previous hash must be 64 characters"):
            Block(index=1, transactions=[], previous_hash="short")
    
    def test_invalid_transaction_type(self) -> None:
        """Test that invalid transaction types raise TypeError."""
        with pytest.raises(TypeError, match="All transactions must be Transaction objects"):
            Block(index=0, transactions=["not a transaction"])
    
    def test_calculate_hash(self) -> None:
        """Test block hash calculation."""
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx], timestamp=1640995200)
        
        hash_value = block.calculate_hash()
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64-character hex strings
        
        # Hash should be deterministic
        assert block.calculate_hash() == hash_value
    
    def test_hash_consistency(self) -> None:
        """Test that identical blocks produce identical hashes."""
        tx = Transaction(from_address=1, to_address=2, value=100)
        
        block1 = Block(index=1, transactions=[tx], timestamp=1640995200, nonce=100)
        block2 = Block(index=1, transactions=[tx], timestamp=1640995200, nonce=100)
        
        assert block1.calculate_hash() == block2.calculate_hash()
    
    def test_hash_changes_with_nonce(self) -> None:
        """Test that hash changes when nonce changes."""
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx])
        
        hash1 = block.calculate_hash()
        block.nonce = 1000
        hash2 = block.calculate_hash()
        
        assert hash1 != hash2
    
    def test_is_hash_valid_with_valid_hash(self) -> None:
        """Test hash validation with a valid hash."""
        block = Block(index=0, transactions=[], difficulty=2)
        valid_hash = "00abcdef" + "1" * 56  # Hash starting with "00"
        
        assert block.is_hash_valid(valid_hash) is True
    
    def test_is_hash_valid_with_invalid_hash(self) -> None:
        """Test hash validation with an invalid hash."""
        block = Block(index=0, transactions=[], difficulty=2)
        invalid_hash = "1" * 64  # Hash not starting with "00"
        
        assert block.is_hash_valid(invalid_hash) is False
    
    def test_is_hash_valid_current_hash(self) -> None:
        """Test hash validation using current block hash."""
        block = Block(index=0, transactions=[], difficulty=1)
        
        # Most blocks won't have valid hashes initially
        is_valid = block.is_hash_valid()
        current_hash = block.calculate_hash()
        expected = current_hash.startswith("0")
        
        assert is_valid == expected
    
    def test_get_merkle_root_empty_transactions(self) -> None:
        """Test Merkle root calculation with no transactions."""
        block = Block(index=0, transactions=[])
        merkle_root = block.get_merkle_root()
        
        assert merkle_root == "0" * 64
    
    def test_get_merkle_root_single_transaction(self) -> None:
        """Test Merkle root calculation with single transaction."""
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx])
        
        merkle_root = block.get_merkle_root()
        
        assert isinstance(merkle_root, str)
        assert len(merkle_root) == 64
        assert merkle_root == tx.calculate_hash()
    
    def test_get_merkle_root_multiple_transactions(self) -> None:
        """Test Merkle root calculation with multiple transactions."""
        tx1 = Transaction(from_address=1, to_address=2, value=100)
        tx2 = Transaction(from_address=2, to_address=3, value=50)
        block = Block(index=1, transactions=[tx1, tx2])
        
        merkle_root = block.get_merkle_root()
        
        assert isinstance(merkle_root, str)
        assert len(merkle_root) == 64
        
        # Should be different from individual transaction hashes
        assert merkle_root != tx1.calculate_hash()
        assert merkle_root != tx2.calculate_hash()
    
    def test_get_merkle_root_odd_transactions(self) -> None:
        """Test Merkle root calculation with odd number of transactions."""
        tx1 = Transaction(from_address=1, to_address=2, value=100)
        tx2 = Transaction(from_address=2, to_address=3, value=50)
        tx3 = Transaction(from_address=3, to_address=4, value=25)
        block = Block(index=1, transactions=[tx1, tx2, tx3])
        
        merkle_root = block.get_merkle_root()
        
        assert isinstance(merkle_root, str)
        assert len(merkle_root) == 64
    
    def test_get_transaction_total(self) -> None:
        """Test calculation of total transaction value."""
        tx1 = Transaction(from_address=1, to_address=2, value=100)
        tx2 = Transaction(from_address=2, to_address=3, value=50)
        tx3 = Transaction(from_address=3, to_address=4, value=25)
        
        block = Block(index=1, transactions=[tx1, tx2, tx3])
        
        assert block.get_transaction_total() == 175
    
    def test_get_transaction_total_empty(self) -> None:
        """Test transaction total with no transactions."""
        block = Block(index=0, transactions=[])
        
        assert block.get_transaction_total() == 0
    
    def test_get_total_fees(self) -> None:
        """Test calculation of total fees."""
        tx1 = Transaction(from_address=1, to_address=2, value=100, fee=5)
        tx2 = Transaction(from_address=2, to_address=3, value=50, fee=3)
        tx3 = Transaction(from_address=3, to_address=4, value=25, fee=2)
        
        block = Block(index=1, transactions=[tx1, tx2, tx3])
        
        assert block.get_total_fees() == 10
    
    def test_get_total_fees_no_fees(self) -> None:
        """Test total fees calculation with no fees."""
        tx1 = Transaction(from_address=1, to_address=2, value=100)
        tx2 = Transaction(from_address=2, to_address=3, value=50)
        
        block = Block(index=1, transactions=[tx1, tx2])
        
        assert block.get_total_fees() == 0
    
    def test_to_dict(self) -> None:
        """Test converting block to dictionary."""
        tx = Transaction(from_address=1, to_address=2, value=100, fee=5)
        block = Block(index=1, transactions=[tx], timestamp=1640995200, nonce=1000)
        
        block_dict = block.to_dict()
        
        expected_keys = {
            "index", "timestamp", "previous_hash", "nonce", "difficulty",
            "hash", "merkle_root", "transaction_count", "transactions",
            "total_value", "total_fees"
        }
        assert set(block_dict.keys()) == expected_keys
        assert block_dict["index"] == 1
        assert block_dict["timestamp"] == 1640995200
        assert block_dict["nonce"] == 1000
        assert block_dict["transaction_count"] == 1
        assert block_dict["total_value"] == 100
        assert block_dict["total_fees"] == 5
    
    def test_to_json(self) -> None:
        """Test converting block to JSON."""
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx])
        
        json_str = block.to_json()
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["index"] == 1
        assert parsed["transaction_count"] == 1
        assert len(parsed["transactions"]) == 1
    
    def test_from_dict(self) -> None:
        """Test creating block from dictionary."""
        tx_dict = {
            "from_address": 1,
            "to_address": 2,
            "value": 100,
            "fee": 5
        }
        
        block_dict = {
            "index": 1,
            "timestamp": 1640995200,
            "previous_hash": "a" * 64,
            "nonce": 1000,
            "difficulty": 6,
            "transactions": [tx_dict]
        }
        
        block = Block.from_dict(block_dict)
        
        assert block.index == 1
        assert block.timestamp == 1640995200
        assert block.previous_hash == "a" * 64
        assert block.nonce == 1000
        assert block.difficulty == 6
        assert len(block.transactions) == 1
        assert block.transactions[0].from_address == 1
    
    def test_from_json(self) -> None:
        """Test creating block from JSON."""
        json_str = '''
        {
            "index": 1,
            "timestamp": 1640995200,
            "previous_hash": "''' + "a" * 64 + '''",
            "nonce": 1000,
            "difficulty": 4,
            "transactions": [
                {
                    "from_address": 1,
                    "to_address": 2,
                    "value": 100,
                    "fee": 5
                }
            ]
        }
        '''
        
        block = Block.from_json(json_str)
        
        assert block.index == 1
        assert block.timestamp == 1640995200
        assert len(block.transactions) == 1
        assert block.transactions[0].value == 100
    
    def test_create_genesis_block(self) -> None:
        """Test creating genesis block."""
        genesis = Block.create_genesis_block()
        
        assert genesis.index == 0
        assert len(genesis.transactions) == 0
        assert genesis.previous_hash == "0" * 64
        assert genesis.nonce == 0
        assert isinstance(genesis.timestamp, int)
    
    def test_round_trip_dict(self) -> None:
        """Test dictionary serialization/deserialization round trip."""
        tx = Transaction(from_address=1, to_address=2, value=100, fee=5)
        original = Block(index=1, transactions=[tx], timestamp=1640995200, nonce=1000)
        
        reconstructed = Block.from_dict(original.to_dict())
        
        assert original.index == reconstructed.index
        assert original.timestamp == reconstructed.timestamp
        assert original.nonce == reconstructed.nonce
        assert original.difficulty == reconstructed.difficulty
        assert len(original.transactions) == len(reconstructed.transactions)
        assert original.transactions[0].value == reconstructed.transactions[0].value
    
    def test_string_representations(self) -> None:
        """Test string representations of blocks."""
        tx = Transaction(from_address=1, to_address=2, value=100)
        block = Block(index=1, transactions=[tx])
        
        str_repr = str(block)
        assert "Block 1" in str_repr
        assert "1 transactions" in str_repr
        assert "hash:" in str_repr
        
        repr_str = repr(block)
        assert "Block(index=1" in repr_str
        assert "transactions=1" in repr_str
    
    def test_merkle_root_deterministic(self) -> None:
        """Test that Merkle root calculation is deterministic."""
        tx1 = Transaction(from_address=1, to_address=2, value=100)
        tx2 = Transaction(from_address=2, to_address=3, value=50)
        
        block1 = Block(index=1, transactions=[tx1, tx2])
        block2 = Block(index=1, transactions=[tx1, tx2])
        
        assert block1.get_merkle_root() == block2.get_merkle_root()
    
    def test_merkle_root_order_sensitive(self) -> None:
        """Test that Merkle root is sensitive to transaction order."""
        tx1 = Transaction(from_address=1, to_address=2, value=100)
        tx2 = Transaction(from_address=2, to_address=3, value=50)
        
        block1 = Block(index=1, transactions=[tx1, tx2])
        block2 = Block(index=1, transactions=[tx2, tx1])
        
        # Different order should produce different Merkle roots
        assert block1.get_merkle_root() != block2.get_merkle_root()