from typing import Dict, List, Optional
from mnemonic import Mnemonic
from hdwallet import HDWallet
from web3 import Web3
from solana.rpc.api import Client
from stellar_sdk import Server, Keypair
from tronpy import Tron
import json
import os
from datetime import datetime
import numpy as np
from sklearn.cluster import KMeans
from transformers import pipeline

class WalletManager:
    def __init__(self):
        self.mnemonic = Mnemonic("english")
        self.wallets: Dict[str, Dict] = {}
        self.user_engagement: Dict[str, Dict] = {}
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        
        # Initialize blockchain connections
        self.web3 = Web3(Web3.HTTPProvider(os.getenv('ETH_RPC_URL')))
        self.solana = Client(os.getenv('SOLANA_RPC_URL'))
        self.stellar = Server(horizon_url=os.getenv('STELLAR_HORIZON_URL'))
        self.tron = Tron(network='mainnet')
        self.polygon = Web3(Web3.HTTPProvider(os.getenv('POLYGON_RPC_URL')))

    def create_wallet(self, user_id: str, blockchain: str) -> Dict:
        """Create a new wallet for a specific blockchain"""
        seed = self.mnemonic.generate(strength=256)
        wallet_data = {
            'seed': seed,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'engagement_score': 0.0
        }

        if blockchain == 'ethereum':
            wallet = HDWallet(symbol="ETH")
            wallet.from_mnemonic(mnemonic=seed)
            wallet_data['address'] = wallet.p2pkh_address()
            wallet_data['private_key'] = wallet.private_key()
        elif blockchain == 'solana':
            keypair = Keypair.random()
            wallet_data['address'] = keypair.public_key
            wallet_data['private_key'] = keypair.secret
        elif blockchain == 'stellar':
            keypair = Keypair.random()
            wallet_data['address'] = keypair.public_key
            wallet_data['private_key'] = keypair.secret
        elif blockchain == 'tron':
            wallet = self.tron.generate_address()
            wallet_data['address'] = wallet['base58check_address']
            wallet_data['private_key'] = wallet['private_key']
        elif blockchain == 'polygon':
            wallet = HDWallet(symbol="MATIC")
            wallet.from_mnemonic(mnemonic=seed)
            wallet_data['address'] = wallet.p2pkh_address()
            wallet_data['private_key'] = wallet.private_key()

        self.wallets[f"{user_id}_{blockchain}"] = wallet_data
        self._update_engagement_score(user_id)
        return wallet_data

    def get_wallet_balance(self, user_id: str, blockchain: str) -> float:
        """Get balance for a specific wallet"""
        wallet_key = f"{user_id}_{blockchain}"
        if wallet_key not in self.wallets:
            return 0.0

        wallet = self.wallets[wallet_key]
        try:
            if blockchain == 'ethereum':
                return self.web3.eth.get_balance(wallet['address'])
            elif blockchain == 'solana':
                balance = self.solana.get_balance(wallet['address'])
                return balance['result']['value'] / 1e9
            elif blockchain == 'stellar':
                account = self.stellar.accounts().account_id(wallet['address']).call()
                return float(account['balances'][0]['balance'])
            elif blockchain == 'tron':
                return self.tron.get_account_balance(wallet['address'])
            elif blockchain == 'polygon':
                return self.polygon.eth.get_balance(wallet['address'])
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0.0

    def _update_engagement_score(self, user_id: str):
        """Update user engagement score based on activity patterns"""
        if user_id not in self.user_engagement:
            self.user_engagement[user_id] = {
                'wallet_count': 0,
                'transaction_count': 0,
                'last_activity': datetime.now().isoformat(),
                'activity_pattern': [],
                'sentiment_score': 0.0
            }

        user_data = self.user_engagement[user_id]
        user_data['wallet_count'] = len([k for k in self.wallets.keys() if k.startswith(user_id)])
        
        # Calculate engagement score using multiple factors
        time_since_last_activity = (datetime.now() - datetime.fromisoformat(user_data['last_activity'])).total_seconds()
        activity_frequency = len(user_data['activity_pattern']) / (time_since_last_activity + 1)
        
        # Use K-means clustering to identify activity patterns
        if len(user_data['activity_pattern']) > 0:
            X = np.array(user_data['activity_pattern']).reshape(-1, 1)
            kmeans = KMeans(n_clusters=2).fit(X)
            pattern_score = np.mean(kmeans.score(X))
        else:
            pattern_score = 0.0

        # Calculate final engagement score
        engagement_score = (
            0.4 * user_data['wallet_count'] +
            0.3 * activity_frequency +
            0.2 * pattern_score +
            0.1 * user_data['sentiment_score']
        )

        user_data['engagement_score'] = engagement_score
        self.user_engagement[user_id] = user_data

    def analyze_user_sentiment(self, user_id: str, text: str):
        """Analyze user sentiment from interactions"""
        if user_id not in self.user_engagement:
            self.user_engagement[user_id] = {
                'wallet_count': 0,
                'transaction_count': 0,
                'last_activity': datetime.now().isoformat(),
                'activity_pattern': [],
                'sentiment_score': 0.0
            }

        sentiment = self.sentiment_analyzer(text)[0]
        score = 1.0 if sentiment['label'] == 'POSITIVE' else -1.0
        self.user_engagement[user_id]['sentiment_score'] = (
            0.7 * self.user_engagement[user_id]['sentiment_score'] +
            0.3 * score
        )
        self._update_engagement_score(user_id)

    def get_user_engagement(self, user_id: str) -> Dict:
        """Get user engagement metrics"""
        return self.user_engagement.get(user_id, {
            'wallet_count': 0,
            'transaction_count': 0,
            'last_activity': datetime.now().isoformat(),
            'activity_pattern': [],
            'sentiment_score': 0.0,
            'engagement_score': 0.0
        })

    def save_wallets(self, filename: str = 'wallets.json'):
        """Save wallets to file"""
        with open(filename, 'w') as f:
            json.dump(self.wallets, f)

    def load_wallets(self, filename: str = 'wallets.json'):
        """Load wallets from file"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                self.wallets = json.load(f) 