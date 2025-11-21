from educhain.core.utils.crypto_utils import CryptoUtils
from typing import Dict, Any, List  
import time
import json
import hashlib
class Transaction:
    def __init__(self, sender_pubkey:str, recipient_address:str , payload: Dict[str, Any], timestamp: float = None, signature: str = None):
        self.sender_pubkey = sender_pubkey
        self.sender_address = CryptoUtils.get_address_from_pubkey(sender_pubkey)
        self.recipient_address = recipient_address
        self.payload = payload
        self.timestamp = timestamp or time.time()
        self.signature = signature
        self.tx_hash = self.calculate_hash()

    def get_singing_data(self):
        return {
            "sender_pubkey": self.sender_pubkey,
            "recipient_address": self.recipient_address,
            "payload": self.payload,
            "timestamp": self.timestamp
        }
    
    def calculate_hash(self):
        data = self.get_singing_data()
        data_str = json.dumps(data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(data_str).hexdigest()
    
    def sign(self, private_key_hex: str):
        data_to_sign = self.get_singing_data()
        self.signature = CryptoUtils.sign_data(data_to_sign, private_key_hex)
    
    def is_valid(self) -> bool:
        if not self.signature or not self.sender_pubkey:
            return False
        
        data_to_verify = self.get_singing_data()
        return CryptoUtils.verify_signature(data_to_verify, self.signature, self.sender_pubkey)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_hash": self.tx_hash,
            "sender_address": self.sender_address,
            "sender_pubkey": self.sender_pubkey,
            "recipient_address": self.recipient_address,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "signature": self.signature
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        return Transaction(
            sender_pubkey=data['sender_pubkey'],
            recipient_address=data['recipient_address'],
            payload=data['payload'],
            timestamp=data.get('timestamp'),
            signature=data.get('signature')
        )

