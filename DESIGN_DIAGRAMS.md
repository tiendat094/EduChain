# Sơ Đồ Thiết Kế EduChain

## 1. Sơ Đồ Kiến Trúc Hệ Thống Ban Đầu (Component Diagram)

```mermaid
graph TD
    subgraph "Lớp API"
        A[Flask API Controller]
    end

    subgraph "Model Core"
        B[Blockchain]
        C[Block]
        D[Transaction]
        E[Mempool]
        F[State DB]
    end

    subgraph "Dịch Vụ"
        G[PoAScheduler]
    end

    subgraph "Hợp Đồng"
        H[NFTContract]
        I[AuthoritySetContract]
    end

    subgraph "Node"
        J[ValidatorNode]
    end

    subgraph "Utils"
        K[CryptoUtils]
    end

    A --> B
    B --> C
    B --> D
    B --> E
    B --> F
    B --> G
    D --> H
    D --> I
    J --> B
    K --> D
    K --> C
    K --> J
    G --> B
```

## 2. Sơ Đồ Tương Tác Component Ban Đầu (Sequence Diagram)

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Blockchain
    participant Scheduler
    participant Contract
    participant CryptoUtils

    User->>API: POST /submit_transaction
    API->>Blockchain: add_transaction_to_mempool(tx)
    Blockchain->>CryptoUtils: verify_signature(tx)
    CryptoUtils-->>Blockchain: chữ ký hợp lệ
    Blockchain-->>API: thêm vào mempool
    API-->>User: thành công

    User->>API: POST /mine_block (với private key)
    API->>Blockchain: mine_block(private_key)
    Blockchain->>Scheduler: get_expected_validator(block_index)
    Scheduler-->>Blockchain: validator_pubkey
    Blockchain->>Blockchain: tạo block với txs
    Blockchain->>CryptoUtils: sign_block(private_key)
    CryptoUtils-->>Blockchain: chữ ký
    Blockchain->>Blockchain: add_block(block)
    Blockchain->>Contract: execute_transaction(tx)
    Contract-->>Blockchain: thành công
    Blockchain-->>API: block đã mine
    API-->>User: chi tiết block
```

## 3. Sơ Đồ Kiến Trúc Hệ Thống Full-Stack (Component Diagram)

Sơ đồ này bao gồm frontend và backend mở rộng:

```mermaid
graph TD
    subgraph "Lớp Frontend"
        FE[Ứng Dụng Web<br/>React/Vue<br/>Dashboard Người Dùng]
    end

    subgraph "Lớp Backend"
        API[Flask API<br/>REST Endpoints]
        BC[Blockchain Core]
        DB[(Database<br/>SQLite/PostgreSQL<br/>cho Persistence)]
        IPFS[IPFS Gateway<br/>Lưu Trữ Metadata NFT]
        UM[Dịch Vụ Quản Lý Người Dùng]
    end

    subgraph "Lớp Domain (Core)"
        B[Blockchain]
        C[Block]
        D[Transaction]
        E[Mempool]
        F[State DB]
        G[PoAScheduler]
        H[NFTContract]
        I[AuthoritySetContract]
        J[ValidatorNode]
        K[CryptoUtils]
    end

    FE --> API
    API --> BC
    API --> UM
    BC --> B
    B --> C
    B --> D
    B --> E
    B --> F
    B --> G
    D --> H
    D --> I
    J --> B
    K --> D
    K --> C
    K --> J
    BC --> DB
    BC --> IPFS
    UM --> DB
```

## 4. Sơ Đồ Tương Tác Component Đã Cập Nhật (Sequence Diagram)

Sơ đồ này hiển thị luồng người dùng đầy đủ từ frontend đến backend:

```mermaid
sequenceDiagram
    participant User
    participant FE
    participant API
    participant BC
    participant Scheduler
    participant Contract
    participant DB
    participant IPFS

    User->>FE: Đăng Nhập & Gửi Yêu Cầu Mint Bằng Cấp
    FE->>API: POST /submit_transaction (mint NFT)
    API->>BC: add_transaction_to_mempool(tx)
    BC->>BC: validate tx
    BC-->>API: thêm vào mempool
    API-->>FE: thành công
    FE-->>User: xác nhận

    User->>FE: Yêu Cầu Mine Block (làm Validator)
    FE->>API: POST /mine_block
    API->>BC: mine_block(private_key)
    BC->>Scheduler: get_expected_validator
    Scheduler-->>BC: validator
    BC->>BC: tạo Block
    BC->>Contract: execute_transaction (mint NFT)
    Contract->>IPFS: lưu metadata
    IPFS-->>Contract: IPFS hash
    Contract->>DB: persist dữ liệu NFT
    DB-->>Contract: đã lưu
    Contract-->>BC: thành công
    BC->>DB: persist block
    DB-->>BC: đã lưu
    BC-->>API: block đã mine
    API-->>FE: chi tiết block
    FE-->>User: NFT đã mint
```

## 5. Sơ Đồ Phát Triển Domain Layer Có Thể Mở Rộng (DDD Class Diagram)

```mermaid
classDiagram
    class BlockchainAggregate {
        +chain: List<Block>
        +mempool: Dict
        +state_db: Dict
        +authority_set: Set
        +addTransaction(tx)
        +mineBlock(privateKey)
        +addBlock(block)
    }

    class BlockAggregate {
        +index: int
        +prev_hash: str
        +transactions: List<Transaction>
        +validator_pubkey: str
        +calculateHash()
        +signBlock(privateKey)
    }

    class TransactionAggregate {
        +sender_pubkey: str
        +payload: Dict
        +signature: str
        +calculateHash()
        +sign(privateKey)
        +isValid()
    }

    class NFTDomain {
        +NFTContract.mintDegree()
        +NFTContract.transfer()
    }

    class AuthorityDomain {
        +AuthoritySetContract.addValidator()
        +AuthoritySetContract.removeValidator()
    }

    class PoAService {
        +getExpectedValidator(blockIndex)
    }

    class CryptoService {
        +signData(data, privateKey)
        +verifySignature(data, sig, pubKey)
        +generateKeyPair()
    }

    class BlockchainRepository {
        +save(blockchain)
        +load()
    }

    class ApplicationService {
        +submitTransaction(txData)
        +mineBlock(privateKey)
    }

    BlockchainAggregate --> BlockAggregate
    BlockchainAggregate --> TransactionAggregate
    BlockchainAggregate --> PoAService
    TransactionAggregate --> NFTDomain
    TransactionAggregate --> AuthorityDomain
    ApplicationService --> BlockchainAggregate
    ApplicationService --> BlockchainRepository
    NFTDomain --> CryptoService
    AuthorityDomain --> CryptoService
```

## 6. Sơ Đồ Bounded Contexts

```mermaid
graph TD
    subgraph "Blockchain Context"
        BC[Blockchain Aggregate<br/>Block Aggregate<br/>Transaction Aggregate]
    end

    subgraph "NFT Context"
        NFT[NFT Domain<br/>Logic Minting<br/>Tracking Ownership]
    end

    subgraph "Authority Context"
        AUTH[Authority Domain<br/>Quản Lý Validator<br/>Consensus Rules]
    end

    subgraph "Infrastructure Context"
        INF[Crypto Service<br/>Repositories<br/>Adapters Bên Ngoài]
    end

    BC --> NFT
    BC --> AUTH
    NFT --> INF
    AUTH --> INF
```

## 7. Sơ Đồ Kiến Trúc Hệ Thống Toàn Diện (Bao Gồm Các Tính Năng Thiếu)

```mermaid
graph TD
    subgraph "Lớp Frontend"
        FE[Ứng Dụng Web<br/>React/Vue<br/>Dashboard Người Dùng]
        WS_FE[WebSocket Client<br/>Cập Nhật Thời Gian Thực]
    end
    
    subgraph "Lớp Backend"
        API[Flask API<br/>REST Endpoints]
        WS_BE[WebSocket Server<br/>Streaming Sự Kiện]
        UM[Dịch Vụ Quản Lý Người Dùng]
        LOG[Dịch Vụ Logging<br/>Logs Cấu Trúc]
    end
    
    subgraph "Lớp Domain (Core)"
        BC[Blockchain Core]
        B[Blockchain Aggregate]
        C[Block Aggregate]
        D[Transaction Aggregate<br/>+ Gas/Nonce]
        E[Mempool<br/>+ Giới Hạn/Hết Hạn]
        F[State DB<br/>+ Persistence]
        G[PoAScheduler<br/>+ Slashing]
        H[NFTContract]
        I[AuthorityContract<br/>+ Slashing]
        J[ValidatorNode]
        K[CryptoUtils]
    end
    
    subgraph "Lớp Infrastructure"
        DB[(Database<br/>SQLite/PostgreSQL<br/>Chain & State)]
        IPFS[IPFS Gateway<br/>Metadata NFT]
        DOCKER[Docker Containers<br/>Triển Khai]
        TEST[Bộ Test<br/>Unit/Integration]
    end
    
    subgraph "Lớp Mạng"
        P2P[Mạng P2P<br/>libp2p/asyncio<br/>Propagation Block<br/>Peer Discovery]
        CONS[Lớp Consensus<br/>Phát Hiện Fork<br/>Reorg Chain]
    end
    
    FE --> API
    FE --> WS_FE
    WS_FE --> WS_BE
    API --> BC
    API --> UM
    WS_BE --> BC
    BC --> B
    B --> C
    B --> D
    B --> E
    B --> F
    B --> G
    D --> H
    D --> I
    J --> B
    K --> D
    K --> C
    K --> J
    BC --> DB
    BC --> IPFS
    BC --> LOG
    UM --> DB
    P2P --> BC
    CONS --> BC
    DOCKER --> API
    DOCKER --> BC
    TEST --> BC
```

## 8. Sơ Đồ Mạng P2P
Hiển thị cách các node kết nối và giao tiếp:

```mermaid
graph TD
    subgraph "Node 1 (MOET)"
        N1_BC[Blockchain]
        N1_P2P[P2P Handler]
        N1_API[Máy Chủ API]
    end
    
    subgraph "Node 2 (Trường A)"
        N2_BC[Blockchain]
        N2_P2P[P2P Handler]
        N2_API[Máy Chủ API]
    end
    
    subgraph "Node 3 (Trường B)"
        N3_BC[Blockchain]
        N3_P2P[P2P Handler]
        N3_API[Máy Chủ API]
    end
    
    N1_P2P -->|Propagation Block| N2_P2P
    N1_P2P -->|Broadcast Transaction| N3_P2P
    N2_P2P -->|Block Mới| N3_P2P
    N2_P2P -->|Peer Discovery| N1_P2P
    N3_P2P -->|Sync Consensus| N1_P2P
    
    N1_BC --> N1_P2P
    N2_BC --> N2_P2P
    N3_BC --> N3_P2P
    
    N1_API -->|Truy Cập Bên Ngoài| Users
    N2_API -->|Truy Cập Bên Ngoài| Users
    N3_API -->|Truy Cập Bên Ngoài| Users
```

## 9. Sơ Đồ Tương Tác Với P2P
Luồng mining và propagation block qua mạng:

```mermaid
sequenceDiagram
    participant User
    participant Local_API
    participant Local_BC
    participant Local_P2P
    participant Remote_P2P
    participant Remote_BC

    User->>Local_API: POST /mine_block
    Local_API->>Local_BC: mine_block(private_key)
    Local_BC->>Local_BC: tạo & ký block
    Local_BC->>Local_BC: thực thi transactions
    Local_BC-->>Local_API: block đã mine
    Local_API-->>User: thành công

    Local_BC->>Local_P2P: broadcast_new_block(block)
    Local_P2P->>Remote_P2P: send_block(block)
    Remote_P2P->>Remote_BC: receive_block(block)
    Remote_BC->>Remote_BC: validate_block(block)
    Remote_BC->>Remote_BC: add_block(block)
    Remote_BC-->>Remote_P2P: block_accepted
    Remote_P2P-->>Local_P2P: ack
    Local_P2P-->>Local_BC: propagation_success
```
