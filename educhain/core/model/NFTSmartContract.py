
from educhain.core.utils.crypto_utils import CryptoUtils
from typing import Dict, Any, List
from datetime import datetime
import hashlib
import json
import base64
class NFTMetadata:
     """Chuẩn metatadata cho chứng chỉ NFT"""
     def __init__(self, student_name:str,student_id:str, degree_type:str,
                  pdf_url:str,pdf_hash:str,institution:str):

        self.student_name = student_name
        self.student_id = student_id
        self.degree_type = degree_type
        self.pdf_url = pdf_url
        self.pdf_hash = pdf_hash
        self.institution = institution
        self.issued_at = datetime.utcnow().isoformat()

     def to_dict(self) -> Dict[str, Any]:
          return{
               "student_name": self.student_name,
               "student_id": self.student_id,
               "degree_type": self.degree_type,
               "pdf_url": self.pdf_url,
               "pdf_hash": self.pdf_hash,
               "institution": self.institution,
               "issued_at": self.issued_at
          }
               
class NFT:
     """NFT chuẩn theo ERC-721"""
     def __init__(self,metadata:NFTMetadata, issuer_pubkey:str,recipient_address:str):
          self.token_id = hashlib.sha256(
               f"{metadata.student_id}{metadata.issued_at}".encode()).hexdigest()[:16]
          self.metadata = metadata
          self.issuer_pubkey = issuer_pubkey
          self.recipient_address = recipient_address
          self.minted_at = datetime.utcnow().isoformat()
          self.issuer_signature = None
          self.is_valid = True
          self.revoked = False
     
     def get_signing_data(self) -> Dict[str, Any]:
          return {
               "token_id": self.token_id,
               "metadata": self.metadata.to_dict(),
               "issuer_pubkey": self.issuer_pubkey,
               "recipient_address": self.recipient_address,
               "minted_at": self.minted_at
          }
     def sign_nft(self, issuer_private_key:str):
          """Ký NFT bằng khóa riêng của tổ chức phát hành"""
          data_to_sign = self.get_signing_data()
          self.issuer_signature = CryptoUtils.sign_data(data_to_sign, issuer_private_key)
          
     def revoke(self):
          """Thu hồi NFT"""
          self.revoked = True
          self.is_valid = False
     
     def verify_nft(self) -> bool:
          """Xác minh chữ ký NFT"""
          if self.revoked or not self.issuer_signature:
               return False
          data_to_verify = self.get_signing_data()
          return CryptoUtils.verify_signature(data_to_verify, self.issuer_signature, self.issuer_pubkey)
     
     
     def to_dict(self) -> Dict[str, Any]:
          return{   
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
     def from_dict(data:Dict[str,Any]) -> 'NFT':
          metadata_dict = data["metadata"]
          metadata = NFTMetadata(
               student_name=metadata_dict["student_name"],
               student_id=metadata_dict["student_id"],
               degree_type=metadata_dict["degree_type"],
               pdf_url=metadata_dict["pdf_url"],
               pdf_hash=metadata_dict["pdf_hash"],
               institution=metadata_dict["institution"]
          )
          nft = NFT(metadata,data["issuer_pubkey"],data["recipient_address"])
          nft.token_id = data["token_id"]
          nft.minted_at = data["minted_at"]
          nft.issuer_signature = data.get("issuer_signature")
          nft.is_valid = data.get("is_valid",False)
          nft.revoked = data.get("revoked",True)
          return nft
     
class NFTSmartContract:
     """Hợp đồng phát hành NFT"""
     def __init__(self, contract_owner:str):
          self.contract_owner = contract_owner
          self.total_supply = 0
          self.token_balances: Dict[str, int] = {}
          self.token_registry: Dict[str, NFT] = {}
          self.revoked_tokens: List[str] = []
          
          
     """Phát hành NFT mới"""
     def mint_nft(self, metadata:NFTMetadata, issuer_pubkey:str,
                 issuer_private_key:str, recipient_address:str) -> NFT:
          if issuer_pubkey != self.contract_owner:
               raise PermissionError("Only contract owner can mint NFTs.")
          nft = NFT(metadata, issuer_pubkey, recipient_address)
          nft.sign_nft(issuer_private_key)
          
          self.token_registry[nft.token_id] = nft
          self.total_supply += 1
          self.token_balances[recipient_address] = self.token_balances.get(recipient_address,0) +1
          return nft
     
     """Chuyển NFT"""
     def transfer_nft(self,token_id:str, from_address:str, to_address:str)-> bool:
          if token_id not in self.token_registry:
               raise ValueError(f"Token {token_id} does not exist.")
          
          nft = self.token_registry[token_id]
          if nft.recipient_address != from_address:
               raise ValueError("Not the token owner.")
          nft = self.recipient_address = to_address
          self.token_balances[from_address] -= 1
          self.token_balances[to_address] = self.token_balances.get(to_address,0) +1
          return True
     
     
     """Thu hồi NFT"""
     def revoke_nft(self, token_id:str)-> bool:
          if token_id not in self.token_registry:
               raise ValueError(f"Token {token_id} not found.")

          nft = self.token_registry[token_id]
          nft.revoke()
          self.revoked_tokens.append(token_id)
          return True
     
     """Lấy thông tin NFT theo token_id"""
     def get_nft(self,token_id:str) -> NFT:
          return self.token_registry.get(token_id)
     
     
     """Lấy số lượng NFT của một địa chỉ"""
     def get_balance(self, address:str) -> int:
          return self.token_balances.get(address,0)
     
     """Xác minh NFT theo token_id"""
     def verify_nft(self, token_id:str) -> Dict[str,Any]:
         if token_id not in self.token_registry:
               return {"valid": False, "reason": "Token does not exist."}
         
         nft = self.token_registry[token_id]
         if nft.revoked:
               return {"valid": False, "reason": "Token has been revoked."}
         if not nft.verify_nft():
               return {"valid": False, "reason": "Invalid signature."}
          
         return{
               "valid":True,
               "token_id": token_id,
               "student_name": nft.metadata.student_name,
               "student_id": nft.metadata.student_id,
               "degree_type": nft.metadata.degree_type,
               "pdf_url": nft.metadata.pdf_url,
               "pdf_hash": nft.metadata.pdf_hash,
               "recipient_address": nft.recipient_address,
               "minted_at": nft.minted_at
          }
           
     def to_dict(self) -> Dict[str,Any]:
          return{
               "contract_owner": self.contract_owner,
               "total_supply": self.total_supply,
               "token_balances": self.token_balances,
               "token_registry": {tid: nft.to_dict() for tid, nft in self.token_registry.items()},
               "revoked_tokens": self.revoked_tokens
          }

         
         