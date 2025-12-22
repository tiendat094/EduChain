"""Top-level runner: initialize keys, blockchain, scheduler and run the API."""
from educhain.core.utils.crypto_utils import CryptoUtils
from educhain.core.model.blockchain import Blockchain
from educhain.core.service.scheduler import PoAScheduler
from educhain.core.controller.api import create_app
import threading


def main():
    # Generate keys for MOET (super validator) and School validator and student for demo
    moet_priv, moet_pub = CryptoUtils.generate_key_pair()
    school_priv, school_pub = CryptoUtils.generate_key_pair()
    student_priv, student_pub = CryptoUtils.generate_key_pair()

    print("MOET address:", CryptoUtils.get_address_from_pubkey(moet_pub))
    print("School address:", CryptoUtils.get_address_from_pubkey(school_pub))

    # Init blockchain and scheduler
    bc = Blockchain(super_validator_pubkey=moet_pub, initial_authorities_pubkeys=[school_pub])
    sched = PoAScheduler(bc)
    bc.scheduler = sched

    app = create_app(bc)

    # Run API
    app.run(host='127.0.0.1', port=5000, debug=True)


if __name__ == '__main__':
    main()
