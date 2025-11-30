import socket
import threading
import time
from .peer import PeerConnection
from .protocol import Protocol, MsgType

class P2PNode:
    def __init__(self, host, port, genesis_node = None):
        self.host = host
        self.port = port
        self.my_addr = (host, port)
        self.genesis_node = genesis_node

        self.peers = []
        self.lock = threading.Lock()
        self.seen_messages = set()
        self.blockchain = None  # Đây sẽ là thể hiện của lớp Blockchain
        self.mempool = set()  # Tập hợp các giao dịch chưa được xác nhận
    def start(self):
        "Start Server"
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Cho phép sử dụng lại cổng ngay lập tức để tránh lỗi WinError 10048
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(self.my_addr)
        server.listen()
        print(f"[+] P2P Node listening on {self.host}:{self.port}")

        # Neu co genesis node thi ket noi den no
        if self.genesis_node:
            # Chạy kết nối trong luồng riêng để không chặn việc accept kết nối mới
            threading.Thread(target=self.connect_to, args=(self.genesis_node[0], self.genesis_node[1])).start()

        while True:
            conn, addr = server.accept()
            peer = PeerConnection(conn, addr, self, connect_direction="INCOMING")
            with self.lock:
                self.peers.append(peer)
            peer.start()

    def connect_to(self, ip, port):
        """ Active connect with other node"""
        try:
            # Kiểm tra xem đã kết nối chưa để tránh kết nối trùng
            if self.is_connected(ip, port):
                return

            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((ip,port))
            peer = PeerConnection(conn, (ip,port), self, connect_direction="OUTGOING")


            with self.lock:
                self.peers.append(peer)
            
            peer.start()
            
            # Gui handshake ngay sau khi kết nối
            handshake_data = {"listen_port": self.port} 
            peer.send(MsgType.HANDSHAKE, handshake_data)

        except Exception as e:
            print(f"[!] Không thể kết nối tới {ip}:{port} - {e}")

    def broadcast(self, msg_type, data, exclude_peer=None):
        """ Gửi tin nhắn tới toàn bộ mạng"""
        with self.lock:
            for peer in self.peers:
                if peer != exclude_peer:
                    peer.send(msg_type, data)
    
    def remove_peer(self, peer):
        """ Xóa peer khỏi danh sách khi ngắt kết nối """
        with self.lock:
            if peer in self.peers:
                self.peers.remove(peer)
                print(f"[-] Đã xóa kết nối với {peer.addr}")

    def is_connected(self, ip, port):
        """ Kiểm tra xem đã có kết nối với địa chỉ này chưa """
        with self.lock:
            for peer in self.peers:
                if peer.addr == (ip, port):
                    return True
        return False
    
    def validate_transaction(self, data):
        # Đây là nơi logic chữ ký và cân bằng số dư được chạy
        return self.blockchain.validate_transaction(data) 
        
    def validate_block(self, data):
        # Đây là nơi logic kiểm tra hash, nonce và previous_hash được chạy
        return self.blockchain.validate_block(data)

    # Hàm yêu cầu đồng bộ hóa (Đã được gọi trong process_message)
    def request_chain_sync(self, peer):
        peer.send(MsgType.REQUEST_CHAIN_HEIGHT, {})

    def request_blocks_from_peer(self, peer, start_height, end_height):
        # Thường yêu cầu theo lô 100-1000 Block để tránh quá tải
        peer.send(MsgType.REQUEST_BLOCKS, {"start": start_height, "end": end_height})

    def process_message(self, sender_peer, msg_type, data):
        """Xử lý các loại tin nhắn nhận được từ Peer"""

        # --- 1. Xử lý KHÁM PHÁ MẠNG LƯỚI (Peer Discovery) ---

        if msg_type == MsgType.HANDSHAKE.value:
            # 1.1. Handshake (Bắt tay): Khi Node mới kết nối
            sender_listen_port = data['listen_port']
            print(f"[v] Handshake thanh cong voi {sender_peer.addr[0]}:{sender_listen_port}")
            # Ghi lại cổng lắng nghe thực tế của Peer.
            sender_peer.listen_port = sender_listen_port 
            
            # Sau khi Handshake xong, xin danh sách Peer để mở rộng mạng
            sender_peer.send(MsgType.REQUEST_PEERS, {})

        elif msg_type == MsgType.REQUEST_PEERS.value:
            # 1.2. Trả lời Yêu cầu Peer
            active_peers = []
            with self.lock:
                # Gửi danh sách các Peer đang kết nối (IP và Listen Port)
                for p in self.peers:
                    # Rất quan trọng: Gửi IP và port lắng nghe thực tế của Peer
                    active_peers.append((p.addr[0], p.listen_port if hasattr(p, 'listen_port') else p.addr[1]))
            sender_peer.send(MsgType.REPLY_PEERS, active_peers)

        elif msg_type == MsgType.REPLY_PEERS.value:
            # 1.3. Nhận Danh sách Peer mới
            new_peers = data
            for (ip, port) in new_peers:
                # Tránh kết nối với chính mình và kết nối trùng
                if (ip, port) != self.my_addr and not self.is_connected(ip, port):
                    print(f"[*] Tim thay peer moi tu danh sach: {ip}:{port}")
                    # Kết nối trong luồng mới để tránh chặn luồng hiện tại
                    threading.Thread(target=self.connect_to, args=(ip, port)).start()


        # --- 2. Xử lý GIAO DỊCH và BLOCK (Consensus/Propagation) ---

        elif msg_type == MsgType.NEW_TX.value:
            # 2.1. Nhận Giao dịch mới
            tx_hash = data.get('tx_hash') # Giả sử giao dịch có hash
            
            if tx_hash not in self.seen_messages:
                # Xác minh giao dịch (chữ ký, số dư, v.v.)
                if self.validate_transaction(data):
                    print(f"[TX] Nhan giao dich moi hop le: {tx_hash}")
                    # Thêm giao dịch vào Mempool
                    self.mempool.add(data) 
                    self.seen_messages.add(tx_hash)
                    
                    # Lan truyền tiếp cho các node khác
                    self.broadcast(MsgType.NEW_TX, data, exclude_peer=sender_peer)
                else:
                    print(f"[!] Giao dich {tx_hash} khong hop le hoac bi tu choi.")

        elif msg_type == MsgType.NEW_BLOCK.value:
            # 2.2. Nhận Block mới
            block_hash = data.get('hash')
            
            if block_hash not in self.seen_messages:
                # Xác minh Block (hash, nonce, previous_hash, v.v.)
                if self.validate_block(data):
                    print(f"[BLOCK] Nhan block moi hop le: {block_hash}")
                    self.blockchain.add_block(data) # Thêm vào chuỗi cục bộ
                    self.seen_messages.add(block_hash)
                    
                    # Lan truyền tiếp cho các node khác
                    self.broadcast(MsgType.NEW_BLOCK, data, exclude_peer=sender_peer)
                else:
                    # Nếu Block không hợp lệ, có thể yêu cầu đồng bộ hóa lại
                    print(f"[!] Block {block_hash} khong hop le. Bat dau yeu cau sync.")
                    self.request_chain_sync(sender_peer)


        # --- 3. Xử lý ĐỒNG BỘ HÓA CHUỖI (Chain Synchronization) ---

        elif msg_type == MsgType.REQUEST_CHAIN_HEIGHT.value:
            # 3.1. Yêu cầu Chiều cao Chuỗi
            current_height = self.blockchain.get_height()
            sender_peer.send(MsgType.REPLY_CHAIN_HEIGHT, {"height": current_height})

        elif msg_type == MsgType.REPLY_CHAIN_HEIGHT.value:
            # 3.2. Nhận Chiều cao Chuỗi từ Peer
            peer_height = data.get("height", 0)
            my_height = self.blockchain.get_height()

            if peer_height > my_height:
                print(f"[*] Peer {sender_peer.addr[0]} co chuoi dai hon ({peer_height}). Bat dau sync.")
                # Yêu cầu các Block còn thiếu
                self.request_blocks_from_peer(sender_peer, start_height=my_height + 1, end_height=peer_height)
            elif peer_height < my_height:
                # Peer bị tụt hậu, gửi cho họ Block mới nhất của mình (Tùy chọn)
                print(f"[!] Peer {sender_peer.addr[0]} bi tut hau ({peer_height}).")
                # self.send_missing_blocks(sender_peer, start_height=peer_height + 1)
                pass

        elif msg_type == MsgType.REQUEST_BLOCKS.value:
            # 3.3. Yêu cầu Gửi các Block (Node khác đang yêu cầu mình)
            start = data.get('start')
            end = data.get('end')
            
            blocks = self.blockchain.get_blocks(start, end) # Hàm truy vấn SQLite
            if blocks:
                sender_peer.send(MsgType.REPLY_BLOCKS, {"blocks": blocks})
            else:
                # Gửi Block Genesis nếu Node yêu cầu từ đầu và mình không có gì
                sender_peer.send(MsgType.REPLY_BLOCKS, {"blocks": []})

        elif msg_type == MsgType.REPLY_BLOCKS.value:
            # 3.4. Nhận các Block để Đồng bộ hóa
            blocks = data.get("blocks", [])
            for block in blocks:
                # Phải xác minh từng Block trước khi lưu vào DB cục bộ
                if self.validate_block(block):
                    self.blockchain.add_block(block)
                else:
                    print(f"[!] Block nhan duoc trong qua trinh sync bi loi. Ngung sync.")
                    break


        # --- 4. Xử lý CƠ CHẾ SINH TỒN (Heartbeat/Keep Alive) ---

        elif msg_type == MsgType.PING.value:
            # 4.1. Nhận PING
            # Trả lời PONG để xác nhận kết nối vẫn còn sống
            sender_peer.send(MsgType.PONG, {})
        
        elif msg_type == MsgType.PONG.value:
            # 4.2. Nhận PONG
            # Cập nhật thời gian hoạt động cuối cùng của Peer
            sender_peer.last_seen = time.time()