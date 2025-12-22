from educhain.core.model.NFT import NFT
from educhain.core.model.NFTmetadata import NFTMetadata
from typing import Dict,Any,Optional,Set
import json
from pathlib import Path

class NFTSmartContract:
    """Hợp đồng phát hành NFT (mô phỏng)"""
    def __init__(self, owner_pubkey: str):
        self.owner_pubkey = owner_pubkey
        self.total_supply = 0
        self.token_balances: Dict[str, int] = {}
        self.token_registry: Dict[str, NFT] = {}
        self.revoked_tokens: Set[str] = set()

    def mint_nft(self, metadata: NFTMetadata, issuer_pubkey: str,
                 issuer_private_key: str, recipient_address: str) -> NFT:
        """
        Phát hành NFT mới.
        Hiện tại chỉ cho phép owner_pubkey mint (giữ như logic cũ).
        Nếu muốn hỗ trợ nhiều issuer (PoA), mình sẽ thêm authorized list.
        """
        if issuer_pubkey != self.owner_pubkey:
            raise PermissionError("Only contract owner can mint NFTs.")
        nft = NFT(metadata, issuer_pubkey, recipient_address)
        nft.sign(issuer_private_key)

        if nft.token_id in self.token_registry:
            raise ValueError("Token already exists.")

        self.token_registry[nft.token_id] = nft
        self.total_supply += 1
        self.token_balances[recipient_address] = self.token_balances.get(recipient_address, 0) + 1
        return nft

    def transfer_nft(self, token_id: str, from_address: str, to_address: str) -> bool:
        if token_id not in self.token_registry:
            raise ValueError(f"Token {token_id} does not exist.")

        nft = self.token_registry[token_id]
        
        if nft.revoked:
            raise ValueError("Token has been revoked, cannot transfer.")

        if nft.recipient_address != from_address:
            raise ValueError("Not the token owner.")

        if self.token_balances.get(from_address, 0) <= 0:
            raise ValueError("Insufficient balance to transfer.")

        # update balances
        self.token_balances[from_address] = self.token_balances.get(from_address, 0) - 1
        self.token_balances[to_address] = self.token_balances.get(to_address, 0) + 1

        nft.recipient_address = to_address
        return True

    def revoke_nft(self, token_id: str) -> bool:
        if token_id not in self.token_registry:
            raise ValueError(f"Token {token_id} not found.")

        nft = self.token_registry[token_id]
        if nft.revoked:
            return False

        nft.revoke()
        self.revoked_tokens.add(token_id)

        # adjust balance of current owner (if any)
        owner = nft.recipient_address
        if self.token_balances.get(owner, 0) > 0:
            self.token_balances[owner] -= 1

        return True

    def get_nft(self, token_id: str) -> Optional[NFT]:
        return self.token_registry.get(token_id)

    def get_balance(self, address: str) -> int:
        return self.token_balances.get(address, 0)



    def verify_nft(self, token_id: str) -> Dict[str, Any]:
        if token_id not in self.token_registry:
            return {"valid": False, "reason": "Token does not exist."}

        nft = self.token_registry[token_id]
        if nft.revoked:
            return {"valid": False, "reason": "Token has been revoked."}
        if not nft.verify():
            return {"valid": False, "reason": "Invalid signature."}

        return {
            "valid": True,
            "token_id": token_id,
            "student_id": nft.metadata.student_id,
            "degree_type": nft.metadata.degree_type,
            "pdf_url": nft.metadata.pdf_url,
            "pdf_hash": nft.metadata.pdf_hash,
            "recipient_address": nft.recipient_address,
            "minted_at": nft.minted_at
        }

    def save_to_json(self, path: str = "nft_state.json"):
        data = self.to_dict()
        # ensure directory exists
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True) if p.parent != Path('.') else None
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner_pubkey": self.owner_pubkey,
            "total_supply": self.total_supply,
            "token_balances": self.token_balances,
            "token_registry": {tid: nft.to_dict() for tid, nft in self.token_registry.items()},
            "revoked_tokens": list(self.revoked_tokens)
        }
