# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SampleChain is a blockchain implementation in Python with transaction validation, proof-of-work mining, and account balance management.

## Architecture

**Core Classes:**
- `Transaction` - Represents blockchain transactions with validation
- `Block` - Contains transactions, timestamp, nonce, and previous block hash
- `Blockchain` - Manages the chain of blocks, account balances, and transaction validation
- `Miner` - Handles proof-of-work mining

**Package Structure:**
```
samplechain/
├── __init__.py          # Package exports
├── transaction.py       # Transaction class
├── block.py            # Block class
├── blockchain.py       # Blockchain management
├── miner.py           # Mining functionality
├── cli.py             # Command-line interface
└── legacy.py          # Legacy getLatestBlock function
```

## Development Commands

```bash
# Install package
pip install -e .

# Install with dev dependencies
pip install -e .[dev]

# Run tests
pytest tests/ -v --cov=samplechain

# Code formatting and linting
black samplechain/
flake8 samplechain/
mypy samplechain/

# CLI usage
samplechain init --initial-balances '{"0": 1000}'
samplechain send 0 1 100 --fee 5
samplechain mine 99
samplechain status
```

## API Usage

```python
from samplechain import Blockchain, Transaction, Miner

# Create blockchain
blockchain = Blockchain(initial_balances={0: 1000, 1: 500})

# Add transaction
tx = Transaction(from_address=0, to_address=1, value=100, fee=5)
blockchain.add_transaction(tx)

# Mine block
miner = Miner()
block = blockchain.mine_pending_transactions(miner_address=99)
if miner.mine_block(block):
    blockchain.add_block(block)
```

## Legacy Interface

The original `getLatestBlock` function is available in `samplechain.legacy`:

```python
from samplechain.legacy import getLatestBlock

result = getLatestBlock(
    startBalances=[5, 0, 0], 
    pendingTransactions=[[0, 1, 5], [1, 2, 5]], 
    blockSize=2
)
# Returns: "blockHash, prevBlockHash, nonce, [[0, 1, 5]]"
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific tests
pytest tests/test_blockchain.py -v

# With coverage
pytest tests/ --cov=samplechain --cov-report=html
```

Test files:
- `test_transaction.py` - Transaction class tests
- `test_block.py` - Block class tests  
- `test_blockchain.py` - Blockchain functionality tests
- `test_miner.py` - Mining operation tests
- `test_integration.py` - End-to-end tests