"""
Command-line interface for SampleChain blockchain.

This module provides a comprehensive CLI for interacting with the blockchain,
including creating transactions, mining blocks, and querying blockchain state.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import click

from .blockchain import Blockchain, InvalidTransactionError, InvalidBlockError
from .transaction import Transaction
from .block import Block
from .miner import Miner


# Global blockchain instance (loaded from file or created new)
blockchain: Optional[Blockchain] = None
miner: Optional[Miner] = None


def load_or_create_blockchain(
    blockchain_file: str, initial_balances: Optional[Dict[int, int]] = None
) -> Blockchain:
    """Load blockchain from file or create new one."""
    global blockchain

    if Path(blockchain_file).exists():
        click.echo(f"Loading blockchain from {blockchain_file}")
        blockchain = Blockchain.load_from_file(blockchain_file)
    else:
        click.echo(f"Creating new blockchain")
        blockchain = Blockchain(
            initial_balances=initial_balances or {0: 1000},
            difficulty=4,
            mining_reward=10,
        )
        # Save immediately
        blockchain.save_to_file(blockchain_file)

    return blockchain


def get_miner() -> Miner:
    """Get or create global miner instance."""
    global miner
    if miner is None:
        miner = Miner(max_nonce=1000000)
    return miner


@click.group()
@click.option(
    "--blockchain-file", default="blockchain.json", help="Blockchain data file"
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx: click.Context, blockchain_file: str, verbose: bool) -> None:
    """SampleChain blockchain CLI tool."""
    ctx.ensure_object(dict)
    ctx.obj["blockchain_file"] = blockchain_file
    ctx.obj["verbose"] = verbose

    if verbose:
        click.echo(f"Using blockchain file: {blockchain_file}")


@cli.command()
@click.option(
    "--initial-balances",
    help='JSON string of initial balances, e.g. {"0": 1000, "1": 500}',
)
@click.option("--difficulty", default=4, help="Mining difficulty (1-8)")
@click.option("--mining-reward", default=10, help="Mining reward amount")
@click.pass_context
def init(
    ctx: click.Context,
    initial_balances: Optional[str],
    difficulty: int,
    mining_reward: int,
) -> None:
    """Initialize a new blockchain."""
    blockchain_file = ctx.obj["blockchain_file"]

    if Path(blockchain_file).exists():
        if not click.confirm(f"Blockchain file {blockchain_file} exists. Overwrite?"):
            click.echo("Initialization cancelled.")
            return

    # Parse initial balances
    balances_dict = None
    if initial_balances:
        try:
            parsed_balances = json.loads(initial_balances)
            balances_dict = {int(k): int(v) for k, v in parsed_balances.items()}
        except (json.JSONDecodeError, ValueError) as e:
            click.echo(f"Error parsing initial balances: {e}", err=True)
            return

    # Create new blockchain
    global blockchain
    blockchain = Blockchain(
        initial_balances=balances_dict,
        difficulty=difficulty,
        mining_reward=mining_reward,
    )

    # Save to file
    blockchain.save_to_file(blockchain_file)

    click.echo(f"✓ Initialized new blockchain with difficulty {difficulty}")
    click.echo(f"✓ Mining reward set to {mining_reward}")
    if balances_dict:
        click.echo(f"✓ Initial balances: {balances_dict}")


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show blockchain status and statistics."""
    blockchain_file = ctx.obj["blockchain_file"]

    if not Path(blockchain_file).exists():
        click.echo("No blockchain found. Use 'init' command to create one.", err=True)
        return

    blockchain = load_or_create_blockchain(blockchain_file)
    stats = blockchain.get_chain_stats()

    click.echo("=== Blockchain Status ===")
    click.echo(f"Total Blocks: {stats['total_blocks']}")
    click.echo(f"Total Transactions: {stats['total_transactions']}")
    click.echo(f"Total Value Transferred: {stats['total_value_transferred']}")
    click.echo(f"Pending Transactions: {stats['pending_transactions']}")
    click.echo(f"Difficulty: {stats['difficulty']}")
    click.echo(f"Mining Reward: {stats['mining_reward']}")
    click.echo(f"Active Addresses: {stats['total_addresses']}")

    if blockchain.pending_transactions:
        click.echo("\n=== Pending Transactions ===")
        for i, tx in enumerate(blockchain.pending_transactions[:5]):  # Show first 5
            click.echo(f"{i+1}. {tx}")
        if len(blockchain.pending_transactions) > 5:
            click.echo(f"... and {len(blockchain.pending_transactions) - 5} more")


@cli.command()
@click.argument("address", type=int)
@click.pass_context
def balance(ctx: click.Context, address: int) -> None:
    """Show balance for an address."""
    blockchain_file = ctx.obj["blockchain_file"]
    blockchain = load_or_create_blockchain(blockchain_file)

    balance_value = blockchain.get_balance(address)
    click.echo(f"Address {address}: {balance_value}")


@cli.command()
@click.argument("from_address", type=int)
@click.argument("to_address", type=int)
@click.argument("value", type=int)
@click.option("--fee", default=0, help="Transaction fee")
@click.pass_context
def send(
    ctx: click.Context, from_address: int, to_address: int, value: int, fee: int
) -> None:
    """Send a transaction."""
    blockchain_file = ctx.obj["blockchain_file"]
    blockchain = load_or_create_blockchain(blockchain_file)

    try:
        # Create and add transaction
        tx = Transaction(
            from_address=from_address,
            to_address=to_address,
            value=value,
            fee=fee,
            timestamp=int(time.time()),
        )

        blockchain.add_transaction(tx)
        blockchain.save_to_file(blockchain_file)

        click.echo(
            f"✓ Transaction added: {from_address} → {to_address} ({value} + {fee} fee)"
        )
        click.echo(f"Transaction hash: {tx.calculate_hash()[:16]}...")

    except (ValueError, InvalidTransactionError) as e:
        click.echo(f"Transaction failed: {e}", err=True)


@cli.command()
@click.argument("miner_address", type=int)
@click.option("--block-size", default=10, help="Maximum transactions per block")
@click.option("--parallel", is_flag=True, help="Use parallel mining")
@click.option("--max-nonce", default=1000000, help="Maximum nonce to try")
@click.pass_context
def mine(
    ctx: click.Context,
    miner_address: int,
    block_size: int,
    parallel: bool,
    max_nonce: int,
) -> None:
    """Mine pending transactions into a new block."""
    blockchain_file = ctx.obj["blockchain_file"]
    blockchain = load_or_create_blockchain(blockchain_file)

    if not blockchain.pending_transactions:
        click.echo("No pending transactions to mine.")
        return

    # Create miner
    miner = Miner(max_nonce=max_nonce)

    # Progress callback for mining
    def progress_callback(nonce: int, current_hash: str) -> None:
        if ctx.obj["verbose"]:
            click.echo(f"Mining... nonce: {nonce}, hash: {current_hash[:16]}...")

    miner.progress_callback = progress_callback

    click.echo(f"Mining {len(blockchain.pending_transactions)} pending transactions...")
    start_time = time.time()

    # Mine block
    block = blockchain.mine_pending_transactions(miner_address, block_size)
    if block is None:
        click.echo("No valid transactions to mine.")
        return

    # Find valid nonce
    mining_method = miner.mine_block_parallel if parallel else miner.mine_block
    success = mining_method(block)

    if not success:
        click.echo("Mining failed: could not find valid nonce within limit.", err=True)
        return

    # Add block to blockchain
    blockchain.add_block(block)
    blockchain.save_to_file(blockchain_file)

    mining_time = time.time() - start_time

    click.echo(f"✓ Block {block.index} mined successfully!")
    click.echo(f"Block hash: {block.calculate_hash()[:16]}...")
    click.echo(f"Nonce: {block.nonce}")
    click.echo(
        f"Transactions: {len([tx for tx in block.transactions if tx.from_address != -1])}"
    )
    click.echo(f"Mining time: {mining_time:.2f} seconds")
    click.echo(f"Miner reward: {blockchain.mining_reward}")


@cli.command()
@click.argument("address", type=int)
@click.option("--limit", default=10, help="Maximum number of transactions to show")
@click.pass_context
def history(ctx: click.Context, address: int, limit: int) -> None:
    """Show transaction history for an address."""
    blockchain_file = ctx.obj["blockchain_file"]
    blockchain = load_or_create_blockchain(blockchain_file)

    transactions = blockchain.get_transaction_history(address)

    if not transactions:
        click.echo(f"No transactions found for address {address}")
        return

    click.echo(f"=== Transaction History for Address {address} ===")

    for i, tx in enumerate(transactions[:limit]):
        direction = "→" if tx.from_address == address else "←"
        other_address = tx.to_address if tx.from_address == address else tx.from_address
        amount = tx.value
        fee_text = f" (fee: {tx.fee})" if tx.fee > 0 else ""

        click.echo(f"{i+1}. {direction} {other_address}: {amount}{fee_text}")
        if ctx.obj["verbose"]:
            click.echo(f"    Hash: {tx.calculate_hash()[:16]}...")

    if len(transactions) > limit:
        click.echo(f"... and {len(transactions) - limit} more transactions")


@cli.command()
@click.option("--block-index", type=int, help="Show specific block by index")
@click.option("--latest", is_flag=True, help="Show latest block")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def show_block(
    ctx: click.Context, block_index: Optional[int], latest: bool, verbose: bool
) -> None:
    """Show block information."""
    blockchain_file = ctx.obj["blockchain_file"]
    blockchain = load_or_create_blockchain(blockchain_file)

    if latest:
        block = blockchain.get_latest_block()
    elif block_index is not None:
        if block_index < 0 or block_index >= len(blockchain.chain):
            click.echo(f"Invalid block index: {block_index}", err=True)
            return
        block = blockchain.chain[block_index]
    else:
        click.echo("Specify --latest or --block-index", err=True)
        return

    click.echo(f"=== Block {block.index} ===")
    click.echo(f"Hash: {block.calculate_hash()}")
    click.echo(f"Previous Hash: {block.previous_hash}")
    click.echo(f"Timestamp: {time.ctime(block.timestamp)}")
    click.echo(f"Nonce: {block.nonce}")
    click.echo(f"Difficulty: {block.difficulty}")
    click.echo(f"Transaction Count: {len(block.transactions)}")
    click.echo(f"Total Value: {block.get_transaction_total()}")
    click.echo(f"Total Fees: {block.get_total_fees()}")

    if verbose or ctx.obj["verbose"]:
        click.echo(f"Merkle Root: {block.get_merkle_root()}")
        click.echo("\nTransactions:")
        for i, tx in enumerate(block.transactions):
            click.echo(f"  {i+1}. {tx}")


@cli.command()
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Validate the entire blockchain."""
    blockchain_file = ctx.obj["blockchain_file"]
    blockchain = load_or_create_blockchain(blockchain_file)

    click.echo("Validating blockchain...")

    if blockchain.is_chain_valid():
        click.echo("✓ Blockchain is valid!")
    else:
        click.echo("✗ Blockchain validation failed!", err=True)
        return

    # Additional checks
    total_supply = sum(blockchain.balances.values())
    stats = blockchain.get_chain_stats()

    click.echo(f"Total supply: {total_supply}")
    click.echo(f"Total blocks validated: {stats['total_blocks']}")
    click.echo(f"Total transactions validated: {stats['total_transactions']}")


@cli.command()
@click.argument("output_file")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "csv"]),
    default="json",
    help="Export format",
)
@click.pass_context
def export(ctx: click.Context, output_file: str, output_format: str) -> None:
    """Export blockchain data."""
    blockchain_file = ctx.obj["blockchain_file"]
    blockchain = load_or_create_blockchain(blockchain_file)

    if output_format == "json":
        # Export full blockchain as JSON
        with open(output_file, "w") as f:
            blockchain.save_to_file(output_file)
        click.echo(f"✓ Blockchain exported to {output_file}")

    elif output_format == "csv":
        # Export transactions as CSV
        import csv

        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["Block", "From", "To", "Value", "Fee", "Hash", "Timestamp"]
            )

            for block in blockchain.chain:
                for tx in block.transactions:
                    writer.writerow(
                        [
                            block.index,
                            tx.from_address,
                            tx.to_address,
                            tx.value,
                            tx.fee,
                            tx.calculate_hash(),
                            tx.timestamp or block.timestamp,
                        ]
                    )

        click.echo(f"✓ Transactions exported to {output_file}")


@cli.command()
@click.argument("start_balances")
@click.argument("pending_transactions")
@click.argument("block_size", type=int)
@click.pass_context
def legacy(
    ctx: click.Context, start_balances: str, pending_transactions: str, block_size: int
) -> None:
    """Run legacy compatibility mode (matches original SampleChain interface)."""
    try:
        # Parse inputs (expecting JSON-like format)
        import ast

        balances_list = ast.literal_eval(start_balances)
        transactions_list = ast.literal_eval(pending_transactions)

        # Convert to our format
        initial_balances = {i: balance for i, balance in enumerate(balances_list)}

        # Create temporary blockchain
        temp_blockchain = Blockchain(
            initial_balances=initial_balances, difficulty=4, mining_reward=0
        )

        # Add transactions
        for from_addr, to_addr, value in transactions_list:
            try:
                tx = Transaction(
                    from_address=from_addr, to_address=to_addr, value=value
                )
                temp_blockchain.add_transaction(tx)
            except InvalidTransactionError:
                pass  # Skip invalid transactions like original

        # Mine block
        miner = Miner(max_nonce=100000)
        block = temp_blockchain.mine_pending_transactions(
            miner_address=-1, block_size=block_size
        )

        if block:
            # Remove mining reward transaction to match original
            user_transactions = [
                tx for tx in block.transactions if tx.from_address != -1
            ]
            block.transactions = user_transactions

            # Mine the block
            miner.mine_block(block)

            # Format output like original
            tx_list = [
                [tx.from_address, tx.to_address, tx.value] for tx in block.transactions
            ]
            result = f"{block.calculate_hash()}, {block.previous_hash}, {block.nonce}, {tx_list}"
            click.echo(result)
        else:
            click.echo("No valid transactions to process")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
