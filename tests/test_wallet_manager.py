import pytest
from src.wallet.wallet_manager import WalletManager
import os
from datetime import datetime, timedelta

@pytest.fixture
def wallet_manager():
    # Set up test environment variables with mock URLs
    os.environ['ETH_RPC_URL'] = 'http://localhost:8545'
    os.environ['SOLANA_RPC_URL'] = 'http://localhost:8899'
    os.environ['STELLAR_HORIZON_URL'] = 'http://localhost:8000'
    os.environ['POLYGON_RPC_URL'] = 'http://localhost:8546'
    
    return WalletManager()

def test_create_wallet(wallet_manager):
    # Test Ethereum wallet creation
    eth_wallet = wallet_manager.create_wallet('user1', 'ethereum')
    assert 'address' in eth_wallet
    assert 'private_key' in eth_wallet
    assert 'seed' in eth_wallet
    assert len(eth_wallet['address']) > 0
    
    # Test Solana wallet creation
    sol_wallet = wallet_manager.create_wallet('user1', 'solana')
    assert 'address' in sol_wallet
    assert 'private_key' in sol_wallet
    assert 'seed' in sol_wallet
    assert len(sol_wallet['address']) > 0

def test_wallet_balance(wallet_manager):
    # Create a test wallet
    wallet = wallet_manager.create_wallet('user2', 'ethereum')
    
    # Get balance (should be 0 for new wallet)
    balance = wallet_manager.get_wallet_balance('user2', 'ethereum')
    assert isinstance(balance, float)
    assert balance >= 0

def test_engagement_scoring(wallet_manager):
    # Create multiple wallets for a user
    wallet_manager.create_wallet('user3', 'ethereum')
    wallet_manager.create_wallet('user3', 'solana')
    wallet_manager.create_wallet('user3', 'polygon')
    
    # Analyze some sentiment
    wallet_manager.analyze_user_sentiment('user3', "I love this wallet manager! It's amazing!")
    
    # Get engagement metrics
    engagement = wallet_manager.get_user_engagement('user3')
    assert engagement['wallet_count'] == 3
    assert engagement['sentiment_score'] > 0
    assert engagement['engagement_score'] > 0

def test_wallet_persistence(wallet_manager):
    # Create a test wallet
    wallet_manager.create_wallet('user4', 'ethereum')
    
    # Save wallets
    wallet_manager.save_wallets('test_wallets.json')
    
    # Create new manager and load wallets
    new_manager = WalletManager()
    new_manager.load_wallets('test_wallets.json')
    
    # Verify wallet was loaded
    assert 'user4_ethereum' in new_manager.wallets
    
    # Clean up
    if os.path.exists('test_wallets.json'):
        os.remove('test_wallets.json')

def test_activity_patterns(wallet_manager):
    # Create a user and simulate activity
    user_id = 'user5'
    wallet_manager.create_wallet(user_id, 'ethereum')
    
    # Simulate some activity
    for i in range(5):
        wallet_manager.user_engagement[user_id]['activity_pattern'].append(i)
    
    # Update engagement score
    wallet_manager._update_engagement_score(user_id)
    
    # Verify engagement metrics
    engagement = wallet_manager.get_user_engagement(user_id)
    assert engagement['wallet_count'] == 1
    assert engagement['engagement_score'] > 0 