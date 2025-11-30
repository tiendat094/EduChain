import struct
import enum
import json

class MsgType(enum.Enum):
    HANDSHAKE = "HANDSHAKE"
    REQUEST_PEERS = "REQUEST_PEERS"
    REPLY_PEERS = "REPLY_PEERS"
    NEW_BLOCK = "NEW_BLOCK"
    NEW_TX = "NEW_TX"
    PING = "PING"
    PONG = "PONG"
    REQUEST_CHAIN_HEIGHT = "REQUEST_CHAIN_HEIGHT"

class Protocol:
    HEADER_FORMAT = '>I'
    HEADER_SIZE = 4

    @staticmethod
    def pack_message(msg_type, data):
        """Đóng gói bản tin: 4 byte độ dài + JSON body"""
        payload = {
            "type": msg_type.value,
            "data": data
        }
        json_data = json.dumps(payload).encode('utf-8')
        msg_len = len(json_data)
        # Đóng gói: [4 bytes Length][JSON Data]
        return struct.pack(Protocol.HEADER_FORMAT, msg_len) + json_data
    
    @staticmethod
    def unpack_header(conn):
        """Đọc 4 byte đầu để biết độ dài bản tin"""
        try:
            header = conn.recv(Protocol.HEADER_SIZE)
            if not header or len(header) < Protocol.HEADER_SIZE:
                return None
            return struct.unpack(Protocol.HEADER_FORMAT, header)[0]
        except Exception:
            return None