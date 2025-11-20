import json
import hashlib
from ecdsa import SECP256k1, SigningKey, VerifyingKey
from ecdsa.util import sigencode_der, sigdecode_der

# Prefer pycryptodome keccak; fall back to pysha3 if necessary
try:
    from Crypto.Hash import keccak as _keccak

    def _keccak256(data: bytes) -> bytes:
        k = _keccak.new(digest_bits=256)
        k.update(data)
        return k.digest()
except Exception:
    try:
        import sha3 as _sha3  # type: ignore

        def _keccak256(data: bytes) -> bytes:
            return _sha3.keccak_256(data).digest()
    except Exception:
        raise ImportError("No keccak implementation found. Install pycryptodome or pysha3.")


class CryptoUtils:
    """Quản lý các hoạt động mật mã học ECDSA (secp256k1)"""

    @staticmethod
    def generate_key_pair():
        sk = SigningKey.generate(curve=SECP256k1)
        vk = sk.get_verifying_key()
        return vk.to_string().hex(), sk.to_string().hex()

    @staticmethod
    def get_public_key(private_key_hex):
        sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
        return sk.get_verifying_key().to_string().hex()

    @staticmethod
    def get_address_from_pubkey(public_key_hex):
        public_key_bytes = bytes.fromhex(public_key_hex)
        keccak_hash = _keccak256(public_key_bytes)
        return "0x" + keccak_hash[-20:].hex()

    @staticmethod
    def sign_data(data, private_key_hex):
        sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
        if not isinstance(data, bytes):
            print("Signing data (not bytes), converting to JSON string")
            data_str = json.dumps(data, sort_keys=True)
            data_bytes = data_str.encode('utf-8')
        else:
            data_bytes = data
        signature = sk.sign(data_bytes, hashfunc=hashlib.sha256, sigencode=sigencode_der)
        return signature.hex()

    @staticmethod
    def verify_signature(data, signature_hex, public_key_hex):
        vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
        if not isinstance(data, bytes):
            data_str = json.dumps(data, sort_keys=True)
            data_bytes = data_str.encode('utf-8')
        else:
            data_bytes = data
        try:
            vk.verify(bytes.fromhex(signature_hex), data_bytes, hashfunc=hashlib.sha256, sigdecode=sigdecode_der)
            return True
        except Exception:
            return False
