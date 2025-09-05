# SampleChain

A blockchain implementation in Python with transaction validation, proof-of-work mining, and account balance management.

## Installation

```bash
pip install -e .
```

## Usage

### Python API
```python
from samplechain import Blockchain, Transaction, Miner

# Create blockchain
blockchain = Blockchain(initial_balances={0: 1000, 1: 500})

# Add transactions
tx = Transaction(from_address=0, to_address=1, value=100)
blockchain.add_transaction(tx)

# Mine a block
miner = Miner()
block = blockchain.mine_pending_transactions(miner_address=99)
if miner.mine_block(block):
    blockchain.add_block(block)

# Check balance
print(blockchain.get_balance(0))  # 900
```

### Command Line Interface
```bash
samplechain init --initial-balances '{"0": 1000}'
samplechain send 0 1 100 --fee 5
samplechain mine 99
samplechain balance 0
```

### Legacy Interface

The original `getLatestBlock` function is available:

```python
from samplechain.legacy import getLatestBlock

result = getLatestBlock([5, 0, 0], [[0, 1, 5], [1, 2, 5]], 2)
print(result)  # "blockHash, prevHash, nonce, [[0, 1, 5]]"
```

## Components

- **Transaction**: Represents value transfers between addresses with optional fees
- **Block**: Container for transactions with proof-of-work nonce and previous block hash  
- **Blockchain**: Manages the chain, validates transactions, and maintains balances
- **Miner**: Finds valid nonces for blocks using SHA256-based proof-of-work

## Development

```bash
pip install -e .[dev]
pytest tests/
black samplechain/
flake8 samplechain/
```
