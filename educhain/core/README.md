# EduChain PoA (Refactored Structure)

This project contains a minimalist Proof-of-Authority (PoA) private blockchain in Python focused on minting NFT degrees.

Project layout

- `educhain/crypto_utils.py` — cryptographic helpers (ECDSA secp256k1, keccak address derivation)
- `educhain/models.py` — `Transaction`, `Block` data models
- `educhain/contracts.py` — `NFTContract`, `AuthoritySetContract` business logic
- `educhain/scheduler.py` — PoA round-robin scheduler
- `educhain/blockchain.py` — `Blockchain` class (mempool, chain, state_db)
- `educhain/node.py` — simple `ValidatorNode` wrapper
- `educhain/api.py` — Flask app factory for RPC / observer endpoints
- `run.py` — top-level runner to initialize demo and start the API
- `requirements.txt` — project dependencies

Quick start

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
python run.py
```

API endpoints are available at `http://127.0.0.1:5000` (see `educhain/api.py`).



fk u