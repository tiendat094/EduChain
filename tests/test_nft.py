import unittest
import sys
from pathlib import Path
import json
import base64

# Thêm đường dẫn để import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from educhain.core.model.NFT import NFT
from educhain.core.model.NFTmetadata import NFTMetadata
from educhain.core.utils.crypto_utils import CryptoUtils


class TestNFTMetadata(unittest.TestCase):
    """Test NFTMetadata"""
    
    def setUp(self):
        self.metadata = NFTMetadata(
            student_id="20210001",
            degree_type="Bachelor",
            pdf_url="ipfs://QmExample123",
            pdf_hash="abc123def456",
            institution="FPT University"
        )
    
    def test_metadata_creation(self):
        """Test tạo metadata"""
        self.assertEqual(self.metadata.student_id, "20210001")
        self.assertEqual(self.metadata.degree_type, "Bachelor")
        self.assertIsNotNone(self.metadata.issued_at)
    
    def test_metadata_to_dict(self):
        """Test convert metadata sang dict"""
        data = self.metadata.to_dict()
        self.assertIn("student_id", data)
        self.assertIn("pdf_hash", data)
        self.assertIn("issued_at", data)
    
    def test_metadata_from_dict(self):
        """Test tạo metadata từ dict"""
        data = self.metadata.to_dict()
        restored = NFTMetadata.from_dict(data)
        self.assertEqual(restored.student_id, self.metadata.student_id)


class TestNFTCreation(unittest.TestCase):
    """Test tạo NFT"""
    
    def setUp(self):
        self.metadata = NFTMetadata(
            student_id="20210002",
            degree_type="Master",
            pdf_url="ipfs://QmExample456",
            pdf_hash="xyz789uvw012",
            institution="FPT University"
        )
        # Tạo keypair test
        self.issuer_pubkey, self.issuer_privkey = CryptoUtils.generate_key_pair()
        self.recipient_address = "0x1234567890abcdef"
    
    def test_nft_creation(self):
        """Test tạo NFT"""
        nft = NFT(self.metadata, self.issuer_pubkey, self.recipient_address)
        
        self.assertIsNotNone(nft.token_id)
        self.assertEqual(nft.issuer_pubkey, self.issuer_pubkey)
        self.assertEqual(nft.recipient_address, self.recipient_address)
        self.assertFalse(nft.revoked)
        self.assertTrue(nft.is_valid)
    
    def test_nft_creation(self):
        """Test tạo NFT"""
        nft = NFT(self.metadata, self.issuer_pubkey, self.recipient_address)
        
        self.assertIsNotNone(nft.token_id)
        self.assertEqual(nft.issuer_pubkey, self.issuer_pubkey)
        self.assertEqual(nft.recipient_address, self.recipient_address)
        self.assertFalse(nft.revoked)
        self.assertTrue(nft.is_valid)
    
    def test_canonical_signing_bytes(self):
        """Test bytes để ký là canonical"""
        nft = NFT(self.metadata, self.issuer_pubkey, self.recipient_address)
        
        bytes1 = nft._canonical_signing_bytes()
        bytes2 = nft._canonical_signing_bytes()
        
        # Phải giống nhau (deterministic)
        self.assertEqual(bytes1, bytes2)


class TestNFTSigning(unittest.TestCase):
    """Test ký và xác minh NFT"""
    
    def setUp(self):
        self.metadata = NFTMetadata(
            student_id="20210003",
            degree_type="PhD",
            pdf_url="ipfs://QmExample789",
            pdf_hash="pqr345stu678",
            institution="FPT University"
        )
        self.issuer_pubkey, self.issuer_privkey = CryptoUtils.generate_key_pair()
        self.recipient_address = "0xabcdef1234567890"
    
    def test_sign_nft(self):
        """Test ký NFT"""
        nft = NFT(self.metadata, self.issuer_pubkey, self.recipient_address)
        
        # Trước khi ký, signature là None
        self.assertIsNone(nft.issuer_signature)
        
        # Ký NFT
        nft.sign(self.issuer_privkey)
        
        # Sau khi ký, signature không None
        self.assertIsNotNone(nft.issuer_signature)
        self.assertIsInstance(nft.issuer_signature, str)
    
    def test_verify_valid_signature(self):
        """Test xác minh signature hợp lệ"""
        nft = NFT(self.metadata, self.issuer_pubkey, self.recipient_address)
        nft.sign(self.issuer_privkey)
        
        # Xác minh phải thành công
        self.assertTrue(nft.verify())
    
    def test_verify_invalid_signature(self):
        """Test xác minh signature không hợp lệ"""
        nft = NFT(self.metadata, self.issuer_pubkey, self.recipient_address)
        
        # Không ký, xác minh phải thất bại
        self.assertFalse(nft.verify())
        
        # Ký rồi thay đổi signature
        nft.sign(self.issuer_privkey)
        nft.issuer_signature = "invalid_signature_data"
        self.assertFalse(nft.verify())
    
    def test_verify_revoked_token(self):
        """Test xác minh token bị thu hồi"""
        nft = NFT(self.metadata, self.issuer_pubkey, self.recipient_address)
        nft.sign(self.issuer_privkey)
        
        # Trước thu hồi
        self.assertTrue(nft.verify())
        
        # Thu hồi
        nft.revoke()
        
        # Sau thu hồi, verify phải trả False
        self.assertFalse(nft.verify())
        self.assertTrue(nft.revoked)
        self.assertFalse(nft.is_valid)


class TestNFTSerialization(unittest.TestCase):
    """Test serialize/deserialize NFT"""
    
    def setUp(self):
        self.metadata = NFTMetadata(
            student_id="20210004",
            degree_type="Bachelor",
            pdf_url="ipfs://QmExample999",
            pdf_hash="lmn012opq345",
            institution="FPT University"
        )
        self.issuer_pubkey, self.issuer_privkey = CryptoUtils.generate_key_pair()
        self.recipient_address = "0xfedcba9876543210"
    
    def test_nft_to_dict(self):
        """Test convert NFT sang dict"""
        nft = NFT(self.metadata, self.issuer_pubkey, self.recipient_address)
        nft.sign(self.issuer_privkey)
        
        data = nft.to_dict()
        
        self.assertIn("token_id", data)
        self.assertIn("metadata", data)
        self.assertIn("issuer_signature", data)
        self.assertIn("revoked", data)
    
    def test_nft_from_dict(self):
        """Test tạo NFT từ dict"""
        nft = NFT(self.metadata, self.issuer_pubkey, self.recipient_address)
        nft.sign(self.issuer_privkey)
        
        # Convert to dict
        data = nft.to_dict()
        
        # Restore from dict
        restored = NFT.from_dict(data)
        
        self.assertEqual(restored.token_id, nft.token_id)
        self.assertEqual(restored.issuer_pubkey, nft.issuer_pubkey)
        self.assertEqual(restored.issuer_signature, nft.issuer_signature)
        self.assertTrue(restored.verify())
    
    def test_json_serialization(self):
        """Test serialize NFT to JSON"""
        nft = NFT(self.metadata, self.issuer_pubkey, self.recipient_address)
        nft.sign(self.issuer_privkey)
        
        # Convert to dict then to JSON
        data = nft.to_dict()
        json_str = json.dumps(data, indent=2)
        
        # Parse JSON back
        parsed = json.loads(json_str)
        restored = NFT.from_dict(parsed)
        
        self.assertTrue(restored.verify())


class TestNFTRevocation(unittest.TestCase):
    """Test thu hồi NFT"""
    
    def setUp(self):
        self.metadata = NFTMetadata(
            student_id="20210005",
            degree_type="Master",
            pdf_url="ipfs://QmExample111",
            pdf_hash="abc111def222",
            institution="FPT University"
        )
        self.issuer_pubkey, self.issuer_privkey = CryptoUtils.generate_key_pair()
        self.recipient_address = "0x0000000000000000"
    
    def test_revoke_nft(self):
        """Test thu hồi NFT"""
        nft = NFT(self.metadata, self.issuer_pubkey, self.recipient_address)
        nft.sign(self.issuer_privkey)
        
        self.assertTrue(nft.is_valid)
        self.assertFalse(nft.revoked)
        
        nft.revoke()
        
        self.assertFalse(nft.is_valid)
        self.assertTrue(nft.revoked)
    
    def test_revoked_token_cannot_verify(self):
        """Test token bị thu hồi không thể xác minh"""
        nft = NFT(self.metadata, self.issuer_pubkey, self.recipient_address)
        nft.sign(self.issuer_privkey)
        nft.revoke()
        
        self.assertFalse(nft.verify())


if __name__ == '__main__':
    unittest.main()