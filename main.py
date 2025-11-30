# main.py
import threading
import time
from educhain.core.p2p.p2pNode import P2PNode, MsgType

class MockBlockChain:
    """Giả lập các hàm cơ bản của Blockchain"""
    def __init__(self, height=10):
        self._height = height
        self._blocks = [{"height": i, "data": f"Block_{i}", "hash": f"HASH_{i}"} for i in range(height + 1)]

    def get_height(self):
        return self._height

    def get_blocks(self, start, end):
        # Giả lập truy vấn SQLite (trả về JSON/Dict)
        if start > end or start > self._height:
            return []
        return self._blocks[start:end+1]

    def validate_transaction(self, tx):
        return True # Luôn trả về True cho mục đích test

    def validate_block(self, block):
        return True # Luôn trả về True cho mục đích test

    def add_block(self, block):
        print(f"[DB] Node added block {block.get('hash')}")
        self._height = block.get('height')
        # Thêm logic lưu DB tại đây

# --- LOGIC KHỞI TẠO CÁC NODE ---

def run_genesis():
    # Node khởi tạo (Bootnode) - Giả lập có 10 Block
    node1 = P2PNode("127.0.0.1", 7000)
    node1.blockchain = MockBlockChain(height=10)
    print(f"--- Node 1 (Genesis) có {node1.blockchain.get_height()} Blocks ---")
    node1.start()

def run_node_2():
    time.sleep(1) # Chờ Node 1 khởi động
    # Node 2 (Mới tham gia) - Giả lập chỉ có 0 Block
    node2 = P2PNode("127.0.0.1", 7001, genesis_node=("127.0.0.1", 7000))
    node2.blockchain = MockBlockChain(height=0)
    node2.mempool = set() # Cần có mempool để lưu TX

    # --- KÍCH HOẠT TEST ĐỒNG BỘ HÓA (MsgType.REQUEST_CHAIN_HEIGHT) ---
    def start_sync():
        print("\n[TEST SYNC] Node 2 bắt đầu yêu cầu đồng bộ hóa!")
        # Hàm này sẽ kích hoạt logic REPLY_CHAIN_HEIGHT và REQUEST_BLOCKS
        node2.broadcast(MsgType.REQUEST_CHAIN_HEIGHT, {})
    
    threading.Timer(5, start_sync).start() 
    
    node2.start()

def run_node_3():
    time.sleep(2) # Chờ Node 1 & 2 khởi động
    # Node 3 (Đã có 5 Block) - Sẽ sync 5 Block còn lại
    node3 = P2PNode("127.0.0.1", 7002, genesis_node=("127.0.0.1", 7000))
    node3.blockchain = MockBlockChain(height=5)
    node3.mempool = set()
    print(f"--- Node 3 (Đang chạy) có {node3.blockchain.get_height()} Blocks ---")

    # --- KÍCH HOẠT TEST NEW_TX và NEW_BLOCK ---
    def trigger_messages():
        print("\n[TEST PROPAGATION] Node 3 bắt đầu lan truyền tin nhắn:")
        
        # 1. TEST NEW_TX: Gửi giao dịch mới
        tx_data = {"id": "TX_123_ABC", "sender": "School_A", "amount": 10, "tx_hash": "TX_HASH_XYZ"}
        node3.broadcast(MsgType.NEW_TX, tx_data)
        
        # 2. TEST NEW_BLOCK: Giả lập tạo và lan truyền Block mới (giả lập Block 11)
        new_block = {"height": 11, "data": "Newest Block", "hash": "HASH_11", "prev_hash": "HASH_10"}
        node3.broadcast(MsgType.NEW_BLOCK, new_block)

        # 3. TEST PING/PONG: Gửi Ping
        node3.broadcast(MsgType.PING, {}) # Các node khác sẽ trả lời PONG
    
    threading.Timer(10, trigger_messages).start()
    node3.start()

if __name__ == "__main__":
    print("Khởi động mạng EduChain P2P...")
    
    # Chạy 3 node trên các luồng riêng biệt
    t1 = threading.Thread(target=run_genesis, daemon=True)
    t2 = threading.Thread(target=run_node_2, daemon=True)
    t3 = threading.Thread(target=run_node_3, daemon=True)

    t1.start()
    t2.start()
    t3.start()

    # Giữ luồng chính chạy để các Thread hoạt động
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nĐã tắt tất cả các Node.")