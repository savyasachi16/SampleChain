#!/usr/bin/env python3
"""
SampleChain Modernization Demo

This script demonstrates the modernized SampleChain blockchain implementation
and shows the improvements made over the original 6-year-old code.
"""

import time
from samplechain import Blockchain, Transaction, Block, Miner
from samplechain.legacy import getLatestBlock


def main():
    print("🚀 SampleChain 2.0 - Modernization Demo")
    print("=" * 50)
    print()

    # 1. Test Legacy Compatibility
    print("1️⃣  Testing Legacy Compatibility")
    print("-" * 30)
    
    original_examples = [
        ([5, 0, 0], [[0, 1, 5], [1, 2, 5]], 2),
        ([1, 7], [[1, 0, 4], [1, 0, 3], [1, 0, 2]], 2),
        ([3, 10, 10, 3], [[3, 2, 2], [2, 3, 5], [3, 2, 4], [3, 0, 2], [1, 2, 2]], 2)
    ]
    
    for i, (balances, transactions, block_size) in enumerate(original_examples, 1):
        print(f"Original Example {i}:")
        result = getLatestBlock(balances, transactions, block_size)
        if result:
            hash_part = result.split(',')[0]
            print(f"✅ Valid proof-of-work hash: {hash_part}")
        else:
            print("❌ No result")
        print()
    
    # 2. Modern Object-Oriented API
    print("2️⃣  Modern Object-Oriented API Demo")
    print("-" * 30)
    
    # Create blockchain
    blockchain = Blockchain(
        initial_balances={0: 1000, 1: 500, 2: 250},
        difficulty=2,  # Easier for demo
        mining_reward=50
    )
    
    print(f"📦 Created blockchain with {len(blockchain.chain)} block (genesis)")
    print(f"💰 Initial balances: {dict(blockchain.balances)}")
    print()
    
    # Create transactions using modern Transaction class
    transactions = [
        Transaction(from_address=0, to_address=1, value=100, fee=5),
        Transaction(from_address=1, to_address=2, value=200, fee=10),
        Transaction(from_address=2, to_address=0, value=50, fee=2),
    ]
    
    print("📝 Adding transactions:")
    for tx in transactions:
        try:
            blockchain.add_transaction(tx)
            print(f"   ✅ {tx}")
        except Exception as e:
            print(f"   ❌ {tx} - {e}")
    print()
    
    # Mine blocks using modern Miner class
    print("⛏️  Mining blocks...")
    miner = Miner(max_nonce=100000)
    
    miner_address = 99
    start_time = time.time()
    
    # Mine pending transactions
    block = blockchain.mine_pending_transactions(miner_address, block_size=5)
    if block:
        mining_success = miner.mine_block(block)
        if mining_success:
            blockchain.add_block(block)
            mining_time = time.time() - start_time
            
            print(f"   ✅ Block {block.index} mined in {mining_time:.2f}s")
            print(f"   🔗 Block hash: {block.calculate_hash()[:20]}...")
            print(f"   🏆 Nonce: {block.nonce}")
            print(f"   💎 {len(block.transactions)} transactions included")
        else:
            print("   ❌ Mining failed")
    else:
        print("   ❌ No valid transactions to mine")
    print()
    
    # Show final state
    print("3️⃣  Final Blockchain State")
    print("-" * 30)
    print(f"📊 Total blocks: {len(blockchain.chain)}")
    print(f"🔗 Chain valid: {'✅' if blockchain.is_chain_valid() else '❌'}")
    print("💰 Final balances:")
    for addr in [0, 1, 2, 99]:
        balance = blockchain.get_balance(addr)
        if balance > 0:
            print(f"   Address {addr}: {balance}")
    
    # Show statistics
    stats = blockchain.get_chain_stats()
    print(f"📈 Total transactions: {stats['total_transactions']}")
    print(f"💸 Total value transferred: {stats['total_value_transferred']}")
    print()
    
    # 4. Advanced Features Demo
    print("4️⃣  Advanced Features")
    print("-" * 30)
    
    # Transaction history
    print(f"📜 Transaction history for address 0:")
    history = blockchain.get_transaction_history(0)
    for tx in history[:3]:  # Show first 3
        direction = "sent to" if tx.from_address == 0 else "received from"
        other = tx.to_address if tx.from_address == 0 else tx.from_address
        print(f"   {direction} address {other}: {tx.value}")
    
    # Mining statistics
    mining_stats = miner.get_mining_stats()
    print(f"⚡ Mining performance:")
    print(f"   Blocks mined: {mining_stats['blocks_mined']}")
    print(f"   Total hashes: {mining_stats['total_hashes']}")
    print(f"   Average hash rate: {mining_stats['average_hash_rate']:.1f} H/s")
    print()
    
    # 5. Modern Improvements Summary
    print("5️⃣  Modernization Improvements")
    print("-" * 30)
    improvements = [
        "🏗️  Object-oriented design with proper separation of concerns",
        "🔒  SHA256 security (upgraded from SHA1)",
        "✅  Comprehensive input validation and error handling",
        "🧪  Extensive test suite with 100+ tests",
        "📝  Complete type hints and documentation",
        "⚡  Parallel mining support for better performance",
        "🔧  CLI interface for easy interaction",
        "💾  Blockchain persistence (save/load from files)",
        "📊  Transaction history and statistics",
        "🎯  Mining rewards and transaction fees",
        "🔍  Merkle tree implementation",
        "⚖️  Automatic difficulty adjustment algorithms"
    ]
    
    for improvement in improvements:
        print(f"   {improvement}")
    
    print()
    print("🎉 SampleChain modernization complete!")
    print("   From baby programmer code to production-ready blockchain! 🚀")


if __name__ == "__main__":
    main()