from educhain.core.model.transaction import Transaction
from typing import Dict, Any, List
from educhain.core.utils.crypto_utils import CryptoUtils
import time
import hashlib
import json
class Block:
    def __init__(self, index: int, prev_hash: str, validator_pubkey: str, transactions: List[Transaction] = None, timestamp: float = None):
        self.index = index
        self.prev_hash = prev_hash
        self.timestamp = timestamp or time.time()
        self.transactions = transactions or []
        self.validator_pubkey = validator_pubkey
        self.validator_signature = None
        self.merkle_root = self.calculate_merkle_root()
        self.hash = self.calculate_hash()

    def calculate_merkle_root(self) -> str:
        if not self.transactions:
            return hashlib.sha256(b"").hexdigest()
        tx_hashes = [tx.tx_hash for tx in self.transactions]
        hashes_str = "".join(sorted(tx_hashes))
        return hashlib.sha256(hashes_str.encode('utf-8')).hexdigest()
        
    def get_signing_data(self):
        return self.hash 
    
    def calculate_hash(self) -> str:
        block_header = {
            "index": self.index,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "validator_pubkey": self.validator_pubkey,
            "merkle_root": self.merkle_root
        }

        header_str = json.dumps(block_header, sort_keys = True).encode('utf-8')
        return hashlib.sha256(header_str).hexdigest()
    
    def sign_block(self, validator_private_key: str):
        data_to_sign = self.get_signing_data()
        self.validator_signature = CryptoUtils.sign_data(data_to_sign, validator_private_key)


    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "prev_hash": self.prev_hash,
            "validator_pubkey": self.validator_pubkey,
            "merkle_root": self.merkle_root,
            "hash": self.hash,
            "validator_signature": self.validator_signature
        }
