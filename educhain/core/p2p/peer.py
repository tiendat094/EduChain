import threading
import socket
import json
from educhain.core.p2p.protocol import Protocol, MsgType

class PeerConnection(threading.Thread):
    def __init__(self, conn, addr, main_node, connect_direction="INCOMING"):
        super().__init__()
        self.conn = conn
        self.addr = addr
        self.main_node = main_node
        self.connection_direction = connect_direction
        self.active = True
        self.peer_id = None

    def run(self):
        print(f"[+] Ket noi moi tu {self.addr}")
        
        try:
            while self.active:
                # 1. Đọc độ dài bản tin (Header)
                msg_len = Protocol.unpack_header(self.conn)
                if not msg_len: 
                    break # Kết nối bị ngắt hoặc lỗi header

                # 2. Đọc nội dung bản tin (Body)
                data = b""
                while len(data) < msg_len:
                    # Chỉ đọc số byte còn thiếu
                    packet = self.conn.recv(msg_len - len(data))
                    if not packet: 
                        break
                    data += packet

                # 3. Xử lý bản tin nếu nhận đủ dữ liệu
                if len(data) == msg_len:
                    try:
                        message = json.loads(data.decode('utf-8'))
                        self.handle_message(message)
                    except json.JSONDecodeError:
                        print(f"[!] Lỗi giải mã JSON từ {self.addr}")
                        continue
                else:
                    break # Dữ liệu không đủ, ngắt kết nối

        except ConnectionResetError:
            print(f"[!] Peer {self.addr} reset connection")
        except Exception as e:
            print(f"[!] Lỗi kết nối với {self.addr}: {e}")
        finally:
            self.close()

    def send(self, msg_type, data):
        """Gửi dữ liệu cho peer này"""
        try:
            packet = Protocol.pack_message(msg_type, data)
            self.conn.sendall(packet)
        except Exception as e:
            print(f"[!] Loi gui tin toi {self.addr}: {e}")
            self.close()
    
    def close(self):
        if self.active:
            self.active = False
            try:
                self.conn.close()
            except:
                pass
            # Gọi hàm remove_peer bên Node chính
            self.main_node.remove_peer(self)

    def handle_message(self, msg):
        """Chuyen ban tin ve Node trung tam xu ly"""
        msg_type = msg.get("type")
        data = msg.get("data")
        # Sửa lỗi chính tả: main_code -> main_node
        self.main_node.process_message(self, msg_type, data)