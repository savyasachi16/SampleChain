"""
Tests for the Transaction class.
"""

import json
import pytest
from samplechain.transaction import Transaction


class TestTransaction:
    """Test cases for the Transaction class."""
    
    def test_valid_transaction_creation(self) -> None:
        """Test creating a valid transaction."""
        tx = Transaction(from_address=1, to_address=2, value=100)
        
        assert tx.from_address == 1
        assert tx.to_address == 2
        assert tx.value == 100
        assert tx.fee == 0
        assert tx.timestamp is None
    
    def test_transaction_with_fee(self) -> None:
        """Test creating a transaction with a fee."""
        tx = Transaction(from_address=1, to_address=2, value=100, fee=5)
        
        assert tx.fee == 5
    
    def test_transaction_with_timestamp(self) -> None:
        """Test creating a transaction with timestamp."""
        tx = Transaction(from_address=1, to_address=2, value=100, timestamp=1640995200)
        
        assert tx.timestamp == 1640995200
    
    def test_invalid_negative_value(self) -> None:
        """Test that negative values raise ValueError."""
        with pytest.raises(ValueError, match="Transaction value must be positive"):
            Transaction(from_address=1, to_address=2, value=-100)
    
    def test_invalid_zero_value(self) -> None:
        """Test that zero values raise ValueError."""
        with pytest.raises(ValueError, match="Transaction value must be positive"):
            Transaction(from_address=1, to_address=2, value=0)
    
    def test_invalid_negative_fee(self) -> None:
        """Test that negative fees raise ValueError."""
        with pytest.raises(ValueError, match="Transaction fee cannot be negative"):
            Transaction(from_address=1, to_address=2, value=100, fee=-5)
    
    def test_invalid_negative_addresses(self) -> None:
        """Test that negative addresses raise ValueError (except -1 for mining)."""
        with pytest.raises(ValueError, match="Addresses must be non-negative integers"):
            Transaction(from_address=-2, to_address=2, value=100)
        
        with pytest.raises(ValueError, match="Addresses must be non-negative integers"):
            Transaction(from_address=1, to_address=-2, value=100)
    
    def test_mining_reward_address_allowed(self) -> None:
        """Test that -1 is allowed as from_address for mining rewards."""
        tx = Transaction(from_address=-1, to_address=0, value=10)
        assert tx.from_address == -1
        assert tx.to_address == 0
        assert tx.value == 10
    
    def test_same_address_transaction(self) -> None:
        """Test that transactions to the same address raise ValueError."""
        with pytest.raises(ValueError, match="Cannot send transaction to the same address"):
            Transaction(from_address=1, to_address=1, value=100)
    
    def test_calculate_hash(self) -> None:
        """Test transaction hash calculation."""
        tx = Transaction(from_address=1, to_address=2, value=100, fee=5, timestamp=1640995200)
        hash_value = tx.calculate_hash()
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64-character hex strings
        
        # Hash should be deterministic
        assert tx.calculate_hash() == hash_value
    
    def test_hash_consistency(self) -> None:
        """Test that identical transactions produce identical hashes."""
        tx1 = Transaction(from_address=1, to_address=2, value=100, fee=5, timestamp=1640995200)
        tx2 = Transaction(from_address=1, to_address=2, value=100, fee=5, timestamp=1640995200)
        
        assert tx1.calculate_hash() == tx2.calculate_hash()
    
    def test_hash_uniqueness(self) -> None:
        """Test that different transactions produce different hashes."""
        tx1 = Transaction(from_address=1, to_address=2, value=100)
        tx2 = Transaction(from_address=1, to_address=2, value=101)
        
        assert tx1.calculate_hash() != tx2.calculate_hash()
    
    def test_to_dict(self) -> None:
        """Test converting transaction to dictionary."""
        tx = Transaction(from_address=1, to_address=2, value=100, fee=5, timestamp=1640995200)
        tx_dict = tx.to_dict()
        
        expected_keys = {"from_address", "to_address", "value", "fee", "timestamp", "hash"}
        assert set(tx_dict.keys()) == expected_keys
        assert tx_dict["from_address"] == 1
        assert tx_dict["to_address"] == 2
        assert tx_dict["value"] == 100
        assert tx_dict["fee"] == 5
        assert tx_dict["timestamp"] == 1640995200
        assert tx_dict["hash"] == tx.calculate_hash()
    
    def test_to_json(self) -> None:
        """Test converting transaction to JSON."""
        tx = Transaction(from_address=1, to_address=2, value=100, fee=5)
        json_str = tx.to_json()
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["from_address"] == 1
        assert parsed["to_address"] == 2
        assert parsed["value"] == 100
        assert parsed["fee"] == 5
    
    def test_from_dict(self) -> None:
        """Test creating transaction from dictionary."""
        tx_dict = {
            "from_address": 1,
            "to_address": 2,
            "value": 100,
            "fee": 5,
            "timestamp": 1640995200
        }
        
        tx = Transaction.from_dict(tx_dict)
        
        assert tx.from_address == 1
        assert tx.to_address == 2
        assert tx.value == 100
        assert tx.fee == 5
        assert tx.timestamp == 1640995200
    
    def test_from_dict_minimal(self) -> None:
        """Test creating transaction from minimal dictionary."""
        tx_dict = {
            "from_address": 1,
            "to_address": 2,
            "value": 100
        }
        
        tx = Transaction.from_dict(tx_dict)
        
        assert tx.from_address == 1
        assert tx.to_address == 2
        assert tx.value == 100
        assert tx.fee == 0
        assert tx.timestamp is None
    
    def test_from_json(self) -> None:
        """Test creating transaction from JSON."""
        json_str = '''
        {
            "from_address": 1,
            "to_address": 2,
            "value": 100,
            "fee": 5,
            "timestamp": 1640995200
        }
        '''
        
        tx = Transaction.from_json(json_str)
        
        assert tx.from_address == 1
        assert tx.to_address == 2
        assert tx.value == 100
        assert tx.fee == 5
        assert tx.timestamp == 1640995200
    
    def test_round_trip_dict(self) -> None:
        """Test dictionary serialization/deserialization round trip."""
        original = Transaction(from_address=1, to_address=2, value=100, fee=5, timestamp=1640995200)
        reconstructed = Transaction.from_dict(original.to_dict())
        
        assert original.from_address == reconstructed.from_address
        assert original.to_address == reconstructed.to_address
        assert original.value == reconstructed.value
        assert original.fee == reconstructed.fee
        assert original.timestamp == reconstructed.timestamp
    
    def test_round_trip_json(self) -> None:
        """Test JSON serialization/deserialization round trip."""
        original = Transaction(from_address=1, to_address=2, value=100, fee=5)
        reconstructed = Transaction.from_json(original.to_json())
        
        assert original.from_address == reconstructed.from_address
        assert original.to_address == reconstructed.to_address
        assert original.value == reconstructed.value
        assert original.fee == reconstructed.fee
    
    def test_string_representations(self) -> None:
        """Test string representations of transactions."""
        tx = Transaction(from_address=1, to_address=2, value=100, fee=5, timestamp=1640995200)
        
        str_repr = str(tx)
        assert "Transaction(1 -> 2: 100)" in str_repr
        
        repr_str = repr(tx)
        assert "Transaction(from_address=1" in repr_str
        assert "to_address=2" in repr_str
        assert "value=100" in repr_str
        assert "fee=5" in repr_str
        assert "timestamp=1640995200" in repr_str
    
    def test_transaction_immutability(self) -> None:
        """Test that transactions are immutable (frozen dataclass)."""
        tx = Transaction(from_address=1, to_address=2, value=100)
        
        with pytest.raises(AttributeError):
            tx.value = 200  # Should raise error due to frozen=True
    
    def test_equality(self) -> None:
        """Test transaction equality."""
        tx1 = Transaction(from_address=1, to_address=2, value=100, fee=5, timestamp=1640995200)
        tx2 = Transaction(from_address=1, to_address=2, value=100, fee=5, timestamp=1640995200)
        tx3 = Transaction(from_address=1, to_address=2, value=101, fee=5, timestamp=1640995200)
        
        assert tx1 == tx2
        assert tx1 != tx3
        assert hash(tx1) == hash(tx2)  # Equal objects should have same hash