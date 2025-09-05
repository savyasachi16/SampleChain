"""
Pytest configuration and fixtures for SampleChain tests.
"""

import pytest
from samplechain import Blockchain, Transaction, Block, Miner


@pytest.fixture
def simple_blockchain():
    """Create a simple blockchain with basic initial balances."""
    return Blockchain(initial_balances={0: 1000, 1: 500, 2: 250})


@pytest.fixture
def blockchain_with_transactions():
    """Create a blockchain with some pending transactions."""
    blockchain = Blockchain(initial_balances={0: 1000, 1: 500})
    
    tx1 = Transaction(from_address=0, to_address=1, value=100)
    tx2 = Transaction(from_address=1, to_address=0, value=50)
    
    blockchain.add_transaction(tx1)
    blockchain.add_transaction(tx2)
    
    return blockchain


@pytest.fixture
def simple_miner():
    """Create a miner with reasonable settings for testing."""
    return Miner(max_nonce=10000)


@pytest.fixture
def sample_transaction():
    """Create a sample transaction for testing."""
    return Transaction(from_address=1, to_address=2, value=100, fee=5)


@pytest.fixture
def sample_block():
    """Create a sample block for testing."""
    tx = Transaction(from_address=1, to_address=2, value=100)
    return Block(index=1, transactions=[tx], difficulty=2)


@pytest.fixture
def genesis_block():
    """Create a genesis block."""
    return Block.create_genesis_block()


# Test data for original compatibility tests
ORIGINAL_TEST_CASES = [
    {
        "name": "case_1",
        "start_balances": {0: 5, 1: 0, 2: 0},
        "transactions": [
            (0, 1, 5),
            (1, 2, 5)
        ],
        "block_size": 2,
        "expected_valid_txs": 1  # Second tx should fail
    },
    {
        "name": "case_2", 
        "start_balances": {0: 0, 1: 7},
        "transactions": [
            (1, 0, 4),
            (1, 0, 3),
            (1, 0, 2)
        ],
        "block_size": 2,
        "expected_valid_txs": 2  # First two should succeed
    },
    {
        "name": "case_3",
        "start_balances": {0: 0, 1: 10, 2: 10, 3: 3},
        "transactions": [
            (3, 2, 2),
            (2, 3, 5),
            (3, 2, 4),  # Should fail
            (3, 0, 2),  # Should fail
            (1, 2, 2)   # Should succeed
        ],
        "block_size": 2,
        "expected_patterns": "complex"  # Multiple blocks needed
    }
]


@pytest.fixture(params=ORIGINAL_TEST_CASES)
def original_test_case(request):
    """Parametrized fixture for original test cases."""
    return request.param


# Performance test configurations
PERFORMANCE_TEST_CONFIGS = [
    {"difficulty": 1, "max_nonce": 1000, "expected_time": 1.0},
    {"difficulty": 2, "max_nonce": 5000, "expected_time": 5.0},
    {"difficulty": 3, "max_nonce": 10000, "expected_time": 10.0},
]


@pytest.fixture(params=PERFORMANCE_TEST_CONFIGS)
def performance_config(request):
    """Parametrized fixture for performance test configurations."""
    return request.param