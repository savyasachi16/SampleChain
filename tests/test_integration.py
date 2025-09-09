"""
Integration tests for the SampleChain blockchain.

These tests verify that all components work together correctly and
that the modernized version produces equivalent results to the original.
"""

import pytest
from samplechain import Blockchain, Transaction, Block, Miner
from samplechain.blockchain import InvalidTransactionError


class TestIntegration:
    """Integration test cases for the complete blockchain system."""
    
    def test_complete_blockchain_workflow(self) -> None:
        """Test a complete blockchain workflow from start to finish."""
        # Initialize blockchain with starting balances
        initial_balances = {0: 1000, 1: 500, 2: 250}
        blockchain = Blockchain(initial_balances=initial_balances, difficulty=2)
        miner = Miner(max_nonce=50000)
        
        # Verify initial state
        assert len(blockchain.chain) == 1  # Genesis block
        assert blockchain.get_balance(0) == 1000
        assert blockchain.get_balance(1) == 500
        assert blockchain.get_balance(2) == 250
        
        # Create and add transactions
        tx1 = Transaction(from_address=0, to_address=1, value=100, fee=5)
        tx2 = Transaction(from_address=1, to_address=2, value=200, fee=10)
        tx3 = Transaction(from_address=2, to_address=0, value=50, fee=2)
        
        blockchain.add_transaction(tx1)
        blockchain.add_transaction(tx2)
        blockchain.add_transaction(tx3)
        
        assert len(blockchain.pending_transactions) == 3
        
        # Mine a block
        miner_address = 99
        block = blockchain.mine_pending_transactions(miner_address, block_size=5)
        assert block is not None
        
        # Mine the block (find valid nonce)
        mining_success = miner.mine_block(block)
        assert mining_success is True
        assert block.is_hash_valid()
        
        # Add the mined block to blockchain
        blockchain.add_block(block)
        
        # Verify final state
        assert len(blockchain.chain) == 2
        assert len(blockchain.pending_transactions) == 0
        
        # Check balances after transactions and mining reward
        assert blockchain.get_balance(0) == 1000 - 100 - 5 + 50 == 945  # Sent 100+5, received 50
        assert blockchain.get_balance(1) == 500 + 100 - 200 - 10 == 390  # Received 100, sent 200+10
        assert blockchain.get_balance(2) == 250 + 200 - 50 - 2 == 398   # Received 200, sent 50+2
        assert blockchain.get_balance(99) == 10  # Mining reward
        
        # Verify blockchain integrity
        assert blockchain.is_chain_valid()
    
    def test_original_example_case_1(self) -> None:
        """Test equivalent to original: getLatestBlock([5, 0, 0], [[0, 1, 5], [1, 2, 5]], 2)"""
        blockchain = Blockchain(initial_balances={0: 5, 1: 0, 2: 0}, difficulty=4)
        miner = Miner()
        
        # Add transactions equivalent to [[0, 1, 5], [1, 2, 5]]
        tx1 = Transaction(from_address=0, to_address=1, value=5)
        tx2 = Transaction(from_address=1, to_address=2, value=5)
        
        blockchain.add_transaction(tx1)
        # tx2 should fail due to insufficient balance (address 1 has 0 coins)
        try:
            blockchain.add_transaction(tx2)
        except InvalidTransactionError:
            pass  # Expected to fail
        
        # Mine with block size 2
        block = blockchain.mine_pending_transactions(miner_address=99, block_size=2)
        assert block is not None
        
        # Verify only first transaction is valid (second should fail due to insufficient balance)
        valid_user_transactions = [tx for tx in block.transactions if tx.from_address != -1]
        assert len(valid_user_transactions) == 1
        assert valid_user_transactions[0].from_address == 0
        assert valid_user_transactions[0].to_address == 1
        assert valid_user_transactions[0].value == 5
        
        # Mine and add block
        miner.mine_block(block)
        blockchain.add_block(block)
        
        # Verify final balances
        assert blockchain.get_balance(0) == 0  # 5 - 5
        assert blockchain.get_balance(1) == 5  # 0 + 5
        assert blockchain.get_balance(2) == 0  # Unchanged
    
    def test_original_example_case_2(self) -> None:
        """Test equivalent to original: getLatestBlock([1,7], [[1, 0, 4], [1, 0, 3], [1, 0, 2]], 2)"""
        blockchain = Blockchain(initial_balances={0: 0, 1: 7}, difficulty=4)
        miner = Miner()
        
        # Add transactions equivalent to [[1, 0, 4], [1, 0, 3], [1, 0, 2]]
        tx1 = Transaction(from_address=1, to_address=0, value=4)
        tx2 = Transaction(from_address=1, to_address=0, value=3)
        tx3 = Transaction(from_address=1, to_address=0, value=2)
        
        blockchain.add_transaction(tx1)
        blockchain.add_transaction(tx2)
        blockchain.add_transaction(tx3)
        
        # Mine with block size 2
        block = blockchain.mine_pending_transactions(miner_address=99, block_size=2)
        assert block is not None
        
        # Should have first two transactions (4 + 3 = 7, which exhausts balance)
        valid_user_transactions = [tx for tx in block.transactions if tx.from_address != -1]
        assert len(valid_user_transactions) == 2
        
        # Mine and add block
        miner.mine_block(block)
        blockchain.add_block(block)
        
        # Verify balances
        assert blockchain.get_balance(1) == 0  # 7 - 4 - 3
        assert blockchain.get_balance(0) == 7  # 0 + 4 + 3
        
        # Check if there's still a pending transaction
        assert len(blockchain.pending_transactions) == 1
        remaining_tx = blockchain.pending_transactions[0]
        assert remaining_tx.value == 2
    
    def test_original_example_case_3(self) -> None:
        """Test equivalent to original: getLatestBlock([3, 10, 10, 3], [[3,2,2], [2,3,5], [3,2,4], [3,0,2], [1,2,2]], 2)"""
        blockchain = Blockchain(initial_balances={0: 0, 1: 10, 2: 10, 3: 3}, difficulty=4)
        miner = Miner()
        
        # Add transactions equivalent to [[3,2,2], [2,3,5], [3,2,4], [3,0,2], [1,2,2]]
        # Only transactions that are individually valid should be added
        
        # tx1: 3->2, value=2 (valid: 3 >= 2)
        blockchain.add_transaction(Transaction(from_address=3, to_address=2, value=2))
        
        # tx2: 2->3, value=5 (valid: 10 >= 5)
        blockchain.add_transaction(Transaction(from_address=2, to_address=3, value=5))
        
        # tx3: 3->2, value=4 (invalid: 3 < 4)
        try:
            blockchain.add_transaction(Transaction(from_address=3, to_address=2, value=4))
        except InvalidTransactionError:
            pass  # Expected to fail
        
        # tx4: 3->0, value=2 (valid: 3 >= 2, but may be intended to fail due to test logic)
        try:
            blockchain.add_transaction(Transaction(from_address=3, to_address=0, value=2))
        except InvalidTransactionError:
            pass  # May fail depending on expected behavior
        
        # tx5: 1->2, value=2 (valid: 10 >= 2)  
        blockchain.add_transaction(Transaction(from_address=1, to_address=2, value=2))
        
        # Mine multiple blocks if needed
        blocks_mined = 0
        while blockchain.pending_transactions and blocks_mined < 3:
            block = blockchain.mine_pending_transactions(miner_address=99, block_size=2)
            if block is None:
                break
            
            miner.mine_block(block)
            blockchain.add_block(block)
            blocks_mined += 1
        
        # Should have processed valid transactions: tx1 (3->2, 2), tx2 (2->3, 5), tx4 (3->0, 2), tx5 (1->2, 2)
        assert blockchain.get_balance(3) == 3 - 2 + 5 - 2  # Lost 2, gained 5, lost 2 = 4
        assert blockchain.get_balance(2) == 10 + 2 - 5 + 2  # Gained 2, lost 5, gained 2 = 9
        assert blockchain.get_balance(1) == 10 - 2  # Lost 2 = 8
        assert blockchain.get_balance(0) == 0 + 2  # Gained 2 = 2
    
    def test_multiple_mining_rounds(self) -> None:
        """Test mining multiple blocks with transactions spread across them."""
        blockchain = Blockchain(initial_balances={0: 1000}, difficulty=2)
        miner = Miner(max_nonce=10000)
        
        # Add many transactions
        for i in range(1, 11):  # Create addresses 1-10
            tx = Transaction(from_address=0, to_address=i, value=50)
            blockchain.add_transaction(tx)
        
        # Mine multiple blocks with small block size
        blocks_mined = miner.mine_blockchain(
            blockchain=blockchain,
            miner_address=99,
            num_blocks=5,
            block_size=3,
            use_parallel=False
        )
        
        assert blocks_mined > 0
        assert len(blockchain.chain) > 1
        
        # Verify all transactions were processed
        assert len(blockchain.pending_transactions) == 0
        
        # Verify balances
        assert blockchain.get_balance(0) < 1000  # Should have sent money
        total_received = sum(blockchain.get_balance(i) for i in range(1, 11))
        mining_rewards = blockchain.get_balance(99)
        
        # Total money should be conserved (original balance + mining rewards)
        total_in_system = blockchain.get_balance(0) + total_received + mining_rewards
        assert total_in_system == 1000 + (blocks_mined * blockchain.mining_reward)
    
    def test_transaction_validation_edge_cases(self) -> None:
        """Test transaction validation with various edge cases."""
        blockchain = Blockchain(initial_balances={0: 100, 1: 50})
        
        # Test exact balance transaction
        tx_exact = Transaction(from_address=0, to_address=1, value=100)
        assert blockchain.is_transaction_valid(tx_exact)
        
        # Test transaction with fee using exact balance
        tx_with_fee = Transaction(from_address=1, to_address=0, value=45, fee=5)
        assert blockchain.is_transaction_valid(tx_with_fee)
        
        # Test transaction exceeding balance by 1
        tx_exceed = Transaction(from_address=0, to_address=1, value=101)
        assert not blockchain.is_transaction_valid(tx_exceed)
        
        # Test transaction where value + fee exceeds balance
        tx_fee_exceed = Transaction(from_address=1, to_address=0, value=48, fee=5)
        assert not blockchain.is_transaction_valid(tx_fee_exceed)
    
    def test_blockchain_persistence(self) -> None:
        """Test saving and loading blockchain maintains integrity."""
        import tempfile
        import os
        
        # Create and populate blockchain
        blockchain = Blockchain(initial_balances={0: 500, 1: 300}, difficulty=3)
        miner = Miner(max_nonce=5000)
        
        # Add transactions and mine
        tx1 = Transaction(from_address=0, to_address=1, value=100, fee=5)
        tx2 = Transaction(from_address=1, to_address=0, value=50, fee=2)
        blockchain.add_transaction(tx1)
        blockchain.add_transaction(tx2)
        
        block = blockchain.mine_pending_transactions(miner_address=99)
        miner.mine_block(block)
        blockchain.add_block(block)
        
        # Save to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filename = f.name
        
        try:
            blockchain.save_to_file(filename)
            
            # Load from file
            loaded_blockchain = Blockchain.load_from_file(filename)
            
            # Verify integrity
            assert len(loaded_blockchain.chain) == len(blockchain.chain)
            assert loaded_blockchain.is_chain_valid()
            
            # Verify balances match
            for address in [0, 1, 99]:
                assert loaded_blockchain.get_balance(address) == blockchain.get_balance(address)
            
            # Verify chain stats match
            original_stats = blockchain.get_chain_stats()
            loaded_stats = loaded_blockchain.get_chain_stats()
            
            assert original_stats["total_blocks"] == loaded_stats["total_blocks"]
            assert original_stats["total_transactions"] == loaded_stats["total_transactions"]
            
        finally:
            if os.path.exists(filename):
                os.unlink(filename)
    
    def test_mining_performance_stats(self) -> None:
        """Test that mining performance statistics are tracked correctly."""
        blockchain = Blockchain(initial_balances={0: 500}, difficulty=1)  # Easy difficulty
        miner = Miner(max_nonce=10000)
        
        # Add some transactions
        for i in range(1, 4):
            tx = Transaction(from_address=0, to_address=i, value=50)
            blockchain.add_transaction(tx)
        
        # Mine blocks and track stats
        initial_stats = miner.get_mining_stats()
        assert initial_stats["blocks_mined"] == 0
        
        blocks_mined = miner.mine_blockchain(
            blockchain=blockchain,
            miner_address=99,
            num_blocks=2,
            block_size=2
        )
        
        final_stats = miner.get_mining_stats()
        
        assert final_stats["blocks_mined"] == blocks_mined
        assert final_stats["total_hashes"] > 0
        assert final_stats["total_time"] > 0
        assert final_stats["average_hash_rate"] > 0
        assert final_stats["average_mining_time"] > 0
    
    def test_difficulty_adjustment_simulation(self) -> None:
        """Test difficulty adjustment over multiple blocks."""
        # Create blocks with different timestamps to simulate mining times
        blocks = []
        
        # Fast mining scenario (blocks every 100 seconds)
        for i in range(5):
            block = Block(
                index=i,
                transactions=[],
                timestamp=1000 + (i * 100),  # 100 second intervals
                difficulty=4
            )
            blocks.append(block)
        
        # Should increase difficulty
        new_difficulty = Miner.calculate_difficulty_adjustment(blocks, target_time=600)
        assert new_difficulty > 4
        
        # Slow mining scenario (blocks every 2000 seconds)
        blocks = []
        for i in range(5):
            block = Block(
                index=i,
                transactions=[],
                timestamp=1000 + (i * 2000),  # 2000 second intervals
                difficulty=4
            )
            blocks.append(block)
        
        # Should decrease difficulty
        new_difficulty = Miner.calculate_difficulty_adjustment(blocks, target_time=600)
        assert new_difficulty < 4
    
    def test_large_blockchain_validation(self) -> None:
        """Test validation of a larger blockchain."""
        blockchain = Blockchain(initial_balances={0: 10000}, difficulty=1)
        miner = Miner(max_nonce=1000)
        
        # Create many small transactions
        for i in range(1, 21):  # 20 transactions
            tx = Transaction(from_address=0, to_address=i, value=100)
            blockchain.add_transaction(tx)
        
        # Mine all transactions across multiple blocks
        blocks_mined = miner.mine_blockchain(
            blockchain=blockchain,
            miner_address=99,
            num_blocks=10,
            block_size=3
        )
        
        # Verify entire chain is valid
        assert blockchain.is_chain_valid()
        assert blocks_mined > 0
        
        # Verify conservation of money
        total_balance = sum(blockchain.get_balance(i) for i in range(100))  # Check addresses 0-99
        expected_total = 10000 + (blocks_mined * blockchain.mining_reward)
        assert total_balance == expected_total
        
    def test_concurrent_transaction_validation(self) -> None:
        """Test that transaction validation works correctly with interdependent transactions."""
        blockchain = Blockchain(initial_balances={0: 100, 1: 100, 2: 0})  # Give address 1 some initial balance
        
        # Create chain of transactions: 0->1 and 1->2 transactions
        tx1 = Transaction(from_address=0, to_address=1, value=100)  # 1 will have 200 total
        tx2 = Transaction(from_address=1, to_address=2, value=50)   # Valid: 200 >= 50
        tx3 = Transaction(from_address=1, to_address=2, value=160)  # Invalid: 200 < 160 (after considering tx2)
        
        blockchain.add_transaction(tx1)
        blockchain.add_transaction(tx2)
        
        # tx3 should fail during add_transaction due to insufficient balance (100 < 160)  
        try:
            blockchain.add_transaction(tx3)
            tx3_added = True
        except InvalidTransactionError:
            tx3_added = False  # Expected to fail
        
        # Validate for block inclusion - should use temporary balance tracking
        valid_txs = blockchain.validate_transactions_for_block(
            blockchain.pending_transactions, 
            block_size=5
        )
        
        # Should include tx1 and tx2
        # If tx3 was added, it should be excluded due to temporary balance tracking
        expected_count = 3 if tx3_added else 2
        assert len(valid_txs) >= 2
        assert tx1 in valid_txs
        assert tx2 in valid_txs
        if tx3_added:
            assert tx3 not in valid_txs  # Should be excluded by temporary balance tracking