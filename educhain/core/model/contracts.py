from uuid import uuid4
from educhain.core.utils.crypto_utils import CryptoUtils


class NFTContract:
    @staticmethod
    def mintDegree(blockchain, tx):
        sender_pubkey = tx.sender_pubkey
        if sender_pubkey not in blockchain.authority_set:
            print(f"[CONTRACT_REJECT] {tx.sender_address} không có quyền mint.")
            return False

        payload = tx.payload
        recipient_address = payload.get('recipient_address')
        ipfs_hash = payload.get('ipfs_hash')

        if not recipient_address or not ipfs_hash:
            print(f"[CONTRACT_REJECT] Payload không hợp lệ cho MINT_DEGREE.")
            return False

        nft_id = f"EDU-{uuid4().hex[:6].upper()}"
        blockchain.state_db.setdefault('nfts', {})[nft_id] = {
            "owner": recipient_address,
            "ipfs_hash": ipfs_hash,
            "minted_by": sender_pubkey
        }
        account_nfts = blockchain.state_db.setdefault('accounts', {}).setdefault(recipient_address, {'nfts': []})
        account_nfts['nfts'].append(nft_id)
        print(f"[CONTRACT_SUCCESS] Minted {nft_id} (IPFS: {ipfs_hash}) cho {recipient_address}.")
        return True


class AuthoritySetContract:
    @staticmethod
    def addValidator(blockchain, tx):
        sender_pubkey = tx.sender_pubkey
        if sender_pubkey != blockchain.super_validator_pubkey:
            print(f"[CONTRACT_REJECT] {tx.sender_address} không có quyền thêm validator (Không phải MOET).")
            return False
        new_pubkey = tx.payload.get('new_validator_pubkey')
        if not new_pubkey:
            print(f"[CONTRACT_REJECT] Payload không hợp lệ cho ADD_VALIDATOR.")
            return False
        if new_pubkey in blockchain.authority_set:
            print(f"[CONTRACT_WARN] Validator {new_pubkey} đã tồn tại.")
            return True
        blockchain.authority_set.add(new_pubkey)
        print(f"[CONTRACT_SUCCESS] Đã thêm Validator mới: {CryptoUtils.get_address_from_pubkey(new_pubkey)}")
        return True
