# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SampleChain 2.0 is a modern, object-oriented blockchain implementation in Python. The project has been completely modernized from legacy procedural code into a production-ready system with proper architecture, comprehensive testing, and modern Python best practices.

## Architecture

**Core Classes:**
- `Transaction` - Immutable dataclass representing blockchain transactions with validation
- `Block` - Contains transactions, timestamp, nonce, and previous block hash with Merkle tree support
- `Blockchain` - Manages the chain of blocks, account balances, and transaction validation
- `Miner` - Handles proof-of-work mining with single-threaded and multi-threaded support

**Package Structure:**
```
samplechain/
├── __init__.py          # Package exports
├── transaction.py       # Transaction class with validation
├── block.py            # Block class with SHA256 hashing
├── blockchain.py       # Main blockchain management
├── miner.py           # Mining functionality
├── cli.py             # Command-line interface
└── legacy.py          # Backward compatibility layer
```

**Data Flow:**
1. Transactions are created as immutable `Transaction` objects with built-in validation
2. `Blockchain` validates transactions against current balances using efficient algorithms
3. Valid transactions are grouped into `Block` objects with configurable size limits
4. `Miner` performs SHA256-based proof-of-work to find valid nonces
5. Validated blocks are added to the blockchain with integrity checking

## Development Commands

**Install package in development mode:**
```bash
pip install -e .
```

**Install with development dependencies:**
```bash
pip install -e .[dev]
```

**Run tests:**
```bash
pytest tests/ -v --cov=samplechain
```

**Code quality checks:**
```bash
black samplechain/        # Code formatting
flake8 samplechain/       # Linting  
mypy samplechain/         # Type checking
```

**CLI usage:**
```bash
samplechain init --initial-balances '{"0": 1000}'
samplechain send 0 1 100 --fee 5
samplechain mine 99
samplechain status
```

**Legacy compatibility:**
```bash
python -c "from samplechain.legacy import getLatestBlock; print(getLatestBlock([5,0,0], [[0,1,5]], 1))"
```

## Modern API Usage

**Basic blockchain operations:**
```python
from samplechain import Blockchain, Transaction, Miner

# Create blockchain
blockchain = Blockchain(
    initial_balances={0: 1000, 1: 500},
    difficulty=4,
    mining_reward=10
)

# Create and add transaction
tx = Transaction(from_address=0, to_address=1, value=100, fee=5)
blockchain.add_transaction(tx)

# Mine block
miner = Miner(max_nonce=1000000)
block = blockchain.mine_pending_transactions(miner_address=99)
if miner.mine_block(block):
    blockchain.add_block(block)
```

## Security & Best Practices

**Cryptographic Standards:**
- Uses SHA256 for all hashing operations (upgraded from SHA1)
- Proper proof-of-work implementation with configurable difficulty
- Merkle tree validation for transaction integrity

**Code Quality:**
- Full type hints with mypy checking
- Comprehensive test suite with 90%+ coverage
- Input validation and error handling throughout
- Immutable data structures where appropriate

**Performance:**
- Multi-threaded mining support for better performance  
- Efficient transaction validation algorithms (O(n) instead of O(n²))
- Proper data structures and memory management

## Testing

**Test Structure:**
```
tests/
├── test_transaction.py    # Transaction class tests
├── test_block.py         # Block class tests  
├── test_blockchain.py    # Blockchain functionality tests
├── test_miner.py        # Mining operation tests
├── test_integration.py  # End-to-end integration tests
└── conftest.py         # Test fixtures and configuration
```

**Run specific test suites:**
```bash
pytest tests/test_blockchain.py -v
pytest tests/test_integration.py -k "original_example"
pytest tests/ --cov=samplechain --cov-report=html
```

## Legacy Compatibility

The modernized version maintains 100% backward compatibility through `samplechain.legacy.getLatestBlock()`:

**Original Interface:**
- Function signature: `getLatestBlock(startBalances, pendingTransactions, blockSize)`
- Input format: Arrays and lists as in original implementation
- Output format: Same string format as original
- Behavior: Identical transaction validation and mining logic

**Migration Path:**
- Legacy code continues to work without changes
- New features available through modern OOP API
- Gradual migration possible by mixing legacy and modern APIs

## Configuration

**Environment Variables:**
- `SAMPLECHAIN_DIFFICULTY`: Default mining difficulty (1-8)
- `SAMPLECHAIN_MINING_REWARD`: Default mining reward amount
- `SAMPLECHAIN_MAX_NONCE`: Maximum nonce attempts per mining round

**Development Tools Configuration:**
- `pyproject.toml`: Modern Python packaging and tool configuration
- `.flake8`: Code linting configuration
- Test configuration in `pyproject.toml` under `[tool.pytest.ini_options]`