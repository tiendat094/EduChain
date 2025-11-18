
import hashlib
from educhain.core.model.block import Block
from educhain.core.model.transaction import Transaction
from educhain.core.model.contracts import NFTContract
from educhain.core.model.contracts import AuthoritySetContract
from educhain.core.utils.crypto_utils import CryptoUtils
class Blockchain:
    def __init__(self, super_validator_pubkey, initial_authorities_pubkeys):
        self.chain = []
        self.mempool = {}
        self.super_validator_pubkey = super_validator_pubkey
        self.authority_set = set(initial_authorities_pubkeys)
        self.authority_set.add(super_validator_pubkey)
        self.state_db = {"accounts": {}, "nfts": {}}

    def create_genesis_block(self):
        genesis_block = Block(index= 0, prev_hash="0"*64, validator_pubkey= self.super_validator_pubkey, transactions=[])
        genesis_block.validator_signature = "GENESIS_SIGNATURE"
        self.chain.append(genesis_block)

    def get_last_block(self):
        return self.chain[-1]
    
    def add_transaction_to_mempool(self,tx:Transaction):
        if not tx.is_valid():
            return False
        if tx.tx_hash in self.mempool:
            return False
        self.mempool[tx.tx_hash] = tx
        return True

    def execute_transaction(self, tx: Transaction):
        payload_type = tx.payload.get('type')
        if payload_type == 'MINT_DEGREE':
            return NFTContract.mintDegree(self, tx)
        elif payload_type == 'ADD_VALIDATOR':
            return AuthoritySetContract.addValidator(self, tx)
        else:
            return False

    def is_valid_new_block(self, block: Block):
        last_block = self.get_last_block()
        if block.index != last_block.index + 1:
            return False
        if block.prev_hash != last_block.hash:
            return False
        expected_validator = self.scheduler.get_expected_validator(block.index)
        if block.validator_pubkey != expected_validator:
            return False
        data_to_verify = block.get_signing_data()
        if not CryptoUtils.verify_signature(data_to_verify, block.validator_signature, block.validator_pubkey):
            return False
        if block.merkle_root != block.calculate_merkle_root():
            return False
        return True

    def mine_block(self, validator_private_key: str):
        validator_pubkey = CryptoUtils.get_public_key(validator_private_key)
        last_block = self.get_last_block()
        next_index = last_block.index + 1
        expected_validator = self.scheduler.get_expected_validator(next_index)
        if validator_pubkey != expected_validator:
            return None
        txs_to_mine_hashes = list(self.mempool.keys())[:10]
        txs_to_mine = [self.mempool[tx_hash] for tx_hash in txs_to_mine_hashes]
        new_block = Block(index=next_index, prev_hash=last_block.hash, validator_pubkey=validator_pubkey, transactions=txs_to_mine)
        new_block.sign_block(validator_private_key)
        if self.add_block(new_block):
            return new_block
        return None

    def add_block(self, block: Block):
        if not self.is_valid_new_block(block):
            return False
        self.chain.append(block)
        successful_txs = []
        for tx in block.transactions:
            if self.execute_transaction(tx):
                successful_txs.append(tx)
            if tx.tx_hash in self.mempool:
                del self.mempool[tx.tx_hash]
        return True


        