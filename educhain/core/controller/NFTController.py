from flask import Flask, request, jsonify
from educhain.core.model.NFT import NFT, NFTMetadata
from educhain.core.model.NFTSmartContract import NFTSmartContract