from educhain.core.utils.crypto_utils import CryptoUtils
from educhain.core.model.NFTmetadata import NFTMetadata
from typing import Dict, Any,Optional
from datetime import datetime
import hashlib
import json
import base64

class NFT:
    """NFT chuẩn theo ERC-721 (mô phỏng)"""
    def __init__(self, metadata: NFTMetadata, issuer_pubkey: str, recipient_address: str):
        # token_id tạo từ student_id + issued_at + recipient_address để giảm xác suất collision
        seed = f"{metadata.student_id}|{metadata.issued_at}|{recipient_address}"
        self.token_id = hashlib.sha256(seed.encode()).hexdigest()
        
        self.metadata = metadata
        self.issuer_pubkey = issuer_pubkey # khóa công khai của tổ chức phát hành
        self.recipient_address = recipient_address # địa chỉ người nhận (chủ sở hữu ban đầu)
        self.minted_at = datetime.utcnow().isoformat()
        
        self.issuer_signature: Optional[str] = None  # base64-encoded signature
        self.is_valid = True
        self.revoked = False

    def _canonical_signing_bytes(self) -> bytes:
        """
        Tạo byte string JSON canonical để ký/xác minh.
        Quan trọng: phải dùng cùng cách serialize cho sign và verify.
        """
        signing_obj = {
            "token_id": self.token_id,
            "metadata": self.metadata.to_dict(),
            "issuer_pubkey": self.issuer_pubkey,
            "recipient_address": self.recipient_address,
            "minted_at": self.minted_at
        }
        return json.dumps(signing_obj, sort_keys=True, separators=(',', ':')).encode()

    def sign(self, issuer_private_key: str):
        """Ký NFT bằng khóa riêng của tổ chức phát hành"""
        data_bytes = self._canonical_signing_bytes()
        sig = CryptoUtils.sign_data(data_bytes, issuer_private_key)
        # chuẩn hoá signature về base64 string để dễ lưu/serialize
        if isinstance(sig, bytes):
            sig_b64 = base64.b64encode(sig).decode()
        else:
            # nếu thư viện trả string (hex hoặc khác), encode rồi base64 cho đồng nhất
            try:
                sig_b64 = base64.b64encode(sig.encode()).decode()
            except Exception:
                sig_b64 = str(sig)
        self.issuer_signature = sig_b64

    def revoke(self):
        """Thu hồi NFT"""
        self.revoked = True
        self.is_valid = False

    def verify(self) -> bool:
        """Xác minh chữ ký NFT (dùng cùng canonical bytes)."""
        if self.revoked or not self.issuer_signature:
            return False

        data_bytes = self._canonical_signing_bytes()

        # decode signature từ base64
        try:
            sig_bytes = base64.b64decode(self.issuer_signature)
            # sig_bytes là bytes, nhưng verify_signature expects hex string
            sig_hex = sig_bytes.decode() if isinstance(sig_bytes, bytes) else sig_bytes
        except Exception:
            # nếu không decode được, truyền raw string (fallback)
            sig_hex = self.issuer_signature

        try:
            return CryptoUtils.verify_signature(data_bytes, sig_hex, self.issuer_pubkey)
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "metadata": self.metadata.to_dict(),
            "issuer_pubkey": self.issuer_pubkey,
            "recipient_address": self.recipient_address,
            "minted_at": self.minted_at,
            "issuer_signature": self.issuer_signature,
            "is_valid": self.is_valid,
            "revoked": self.revoked
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'NFT':
        metadata_dict = data["metadata"]
        metadata = NFTMetadata.from_dict(metadata_dict)
        nft = NFT(metadata, data["issuer_pubkey"], data["recipient_address"])
        nft.token_id = data.get("token_id", nft.token_id)
        nft.minted_at = data.get("minted_at", nft.minted_at)
        nft.issuer_signature = data.get("issuer_signature")
        nft.is_valid = data.get("is_valid", True)
        nft.revoked = data.get("revoked", False)
        return nft
