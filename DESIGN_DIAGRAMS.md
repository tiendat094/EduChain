# Sơ Đồ Thiết Kế EduChain

## Tổng Quan Kiến Trúc Hệ Thống

```mermaid
graph TB
    subgraph "Lớp Client"
        SW[Ví Sinh Viên<br/>Trình Duyệt/Ứng Dụng]
        UW[Ví Trường Đại Học<br/>Trình Duyệt/Ứng Dụng]
        CA[Ứng Dụng Client<br/>Giao Diện Web]
    end

    subgraph "Lớp Mạng"
        SV[Super Validator<br/>Node Bộ GD&ĐT]
        V1[Validator 1<br/>Trường Đại Học A]
        V2[Validator 2<br/>Trường Đại Học B]
        V3[Validator 3<br/>Trường Đại Học C]
        O1[Observer Node 1<br/>Trường Đại Học D]
        O2[Observer Node 2<br/>Tổ Chức Công Cộng]
    end

    subgraph "Lớp Lưu Trữ"
        IPFS[(IPFS<br/>File Bằng Cấp)]
        SQLite[(CSDL SQLite<br/>Trạng Thái & Người Dùng)]
        Ledger[(Sổ Cái Blockchain<br/>Các Khối)]
    end

    SW -->|Truy Vấn NFTs| CA
    UW -->|Mint Bằng Cấp| CA
    CA -->|Gọi API| O1
    CA -->|Gọi API| O2
    SV -->|Quản Lý Bộ Ủy Quyền| V1
    SV -->|Quản Lý Bộ Ủy Quyền| V2
    SV -->|Quản Lý Bộ Ủy Quyền| V3
    V1 -->|Tạo Khối| Ledger
    V2 -->|Tạo Khối| Ledger
    V3 -->|Tạo Khối| Ledger
    V1 -->|Đồng Bộ| O1
    V2 -->|Đồng Bộ| O2
    Ledger -->|Cập Nhật Trạng Thái| SQLite
    UW -->|Tải Lên PDF| IPFS
```

## Vai Trò Node và Tương Tác

```mermaid
stateDiagram-v2
    [*] --> Registration: Trường Đại Học đăng ký với Bộ GD&ĐT

    Registration --> Approved: Bộ GD&ĐT xác minh tính hợp pháp
    Registration --> Rejected: Thông tin không hợp lệ

    Approved --> Validator: Được chọn làm Validator
    Approved --> Observer: Không được chọn làm Validator

    Validator --> BlockCreation: Lượt Round-Robin
    BlockCreation --> Validation: Ký và phát tán khối
    Validation --> Confirmed: Các validator khác xác minh
    Validation --> Failed: Chữ ký không hợp lệ

    Confirmed --> BlockCreation: Lượt tiếp theo
    Failed --> Skip: Chuyển sang validator tiếp theo

    Observer --> Query: Cung cấp API chỉ đọc
    Query --> [*]

    note right of Validator
        Sử dụng HSM cho private key
        Tạo khối mỗi 5 giây
    end note

    note right of Observer
        Quyền truy cập chỉ đọc
        Truy vấn cân bằng tải
    end note
```

## Luồng Đồng Thuận PoA

```mermaid
sequenceDiagram
    participant Mempool
    participant Scheduler
    participant Validator
    participant Network
    participant StateDB

    loop Mỗi 5 giây
        Scheduler->>Mempool: Thu thập giao dịch đang chờ
        Scheduler->>Validator: Phân công tạo khối (Round-Robin)
        Validator->>Validator: Tạo khối với các giao dịch
        Validator->>Validator: Ký khối bằng private key
        Validator->>Network: Phát tán khối đã ký
        Network->>Network: Các validator khác xác minh chữ ký
        Network->>StateDB: Cập nhật trạng thái nếu hợp lệ
        Network->>Mempool: Xóa giao dịch đã xử lý
    end

    alt Validator bỏ lỡ lượt
        Scheduler->>Scheduler: Chuyển sang validator tiếp theo
    end
```

## Quy Trình Minting Bằng Cấp

```mermaid
flowchart TD
    A[Trường Đại Học Chuẩn Bị PDF Bằng Cấp] --> B[Tải Lên IPFS]
    B --> C[Tạo Metadata<br/>Thông Tin SV + Hash IPFS]
    C --> D[Tạo Giao Dịch Mint<br/>NFT_Contract.mintDegree]
    D --> E[Ký Giao Dịch<br/>Private Key Trường]
    E --> F[Gửi Đến Blockchain]
    F --> G{Validator Xác Minh<br/>Chữ Ký Trường?}
    G -->|Hợp Lệ| H[Thực Thi Smart Contract]
    G -->|Không Hợp Lệ| I[Từ Chối Giao Dịch]
    H --> J[Cập Nhật State DB<br/>NFT -> Sinh Viên]
    J --> K[Phát Tán Khối]
    I --> L[Xóa Khỏi Mempool]
```

## Quy Trình Xác Minh Bằng Cấp

```mermaid
flowchart TD
    A[Nhà Tuyển Dụng Yêu Cầu Xác Minh] --> B[Cung Cấp Địa Chỉ SV/NFT ID]
    B --> C[Ứng Dụng Client Truy Vấn Observer Node]
    C --> D[Observer Node Kiểm Tra State DB]
    D --> E{Quyền Sở Hữu NFT<br/>Được Xác Nhận?}
    E -->|Có| F[Lấy Khối Mint Gốc]
    E -->|Không| G[Trả Về Không Hợp Lệ]
    F --> H[Xác Minh Chữ Ký PoA Validator]
    H --> I{Kiểm Tra Hash IPFS<br/>Tính Toàn Vẹn?}
    I -->|Hợp Lệ| J[Trả Về Bằng Cấp Đã Xác Minh]
    I -->|Không Hợp Lệ| G
    J --> K[Hiển Thị Chi Tiết Bằng Cấp]
```

## Kiến Trúc Quản Lý Khóa

```mermaid
graph LR
    subgraph "Tạo Phía Client"
        ECDSA[Thuật Toán ECDSA<br/>secp256k1]
        RNG[Bộ Sinh Số Ngẫu Nhiên<br/>An Toàn]
        ECDSA --> PK[Private Key<br/>Không Bao Giờ Rời Client]
        ECDSA --> PubK[Public Key]
        RNG --> PK
        PubK --> Addr[Địa Chỉ Ví<br/>Hash của Public Key]
    end

    subgraph "Lưu Trữ"
        Local[(Lưu Trữ Local<br/>Mã Hóa/Riêng Tư)]
        HSM[(Mô-đun Bảo Mật Phần Cứng<br/>Cho Validators)]
        IPFS[(IPFS<br/>File Bằng Cấp)]
    end

    subgraph "Blockchain"
        TX[Giao Dịch<br/>Ký Bằng Private Key]
        BLK[Khối<br/>Ký Bởi Validators]
        STATE[State DB<br/>Public Keys & Địa Chỉ]
    end

    PK --> Local
    PK --> HSM
    PubK --> TX
    Addr --> TX
    TX --> BLK
    BLK --> STATE
    IPFS --> TX
```

## Data Flow Architecture

```mermaid
graph TD
    subgraph "Input Sources"
        Student[Student Data]
        University[University Systems]
        MOET[MOET Authority]
    end

    subgraph "Processing"
        Client[Client Applications]
        Nodes[Blockchain Nodes]
        Consensus[PoA Consensus]
    end

    subgraph "Storage"
        Mempool[(Mempool<br/>Pending TX)]
        Ledger[(Blockchain Ledger<br/>Confirmed Blocks)]
        State[(State Database<br/>Current State)]
        IPFS[(IPFS<br/>Files)]
    end

    subgraph "Output"
        API[API Endpoints]
        UI[User Interfaces]
        Reports[Verification Reports]
    end

    Student --> Client
    University --> Client
    MOET --> Nodes
    Client --> Nodes
    Nodes --> Consensus
    Consensus --> Mempool
    Mempool --> Ledger
    Ledger --> State
    Client --> IPFS
    State --> API
    API --> UI
    API --> Reports
```

## Sơ Đồ Vai Trò và Phân Quyền

```mermaid
graph TD
    subgraph "Bộ Giáo Dục và Đào Tạo (MOET)"
        MOET_ADMIN[Quản Trị Viên MOET<br/>Super Validator]
        MOET_ADMIN -->|Quyền Cao Nhất| AUTHORITY_SET[Quản Lý Bộ Ủy Quyền<br/>Thêm/Xóa Validators]
        MOET_ADMIN -->|Phê Duyệt| UNIVERSITY_REG[Đăng Ký Trường Đại Học]
        MOET_ADMIN -->|Giám Sát| NETWORK_MONITOR[Giám Sát Mạng Lưới]
    end

    subgraph "Trường Đại Học (Validators)"
        UNI_ADMIN[Quản Trị Viên Trường<br/>Validator Node]
        UNI_ADMIN -->|Mint NFT| DEGREE_MINT[Phát Hành Bằng Cấp<br/>Ký Giao Dịch]
        UNI_ADMIN -->|Tạo Khối| BLOCK_CREATE[Tạo Khối<br/>Round-Robin]
        UNI_ADMIN -->|Xác Minh| TX_VERIFY[Xác Minh Giao Dịch]
        UNI_ADMIN -->|Ký Khối| BLOCK_SIGN[Ký Khối<br/>HSM Bắt Buộc]
    end

    subgraph "Trường Đại Học (Observer Nodes)"
        OBSERVER_ADMIN[Quản Trị Viên Observer]
        OBSERVER_ADMIN -->|Truy Vấn| READ_API[API Chỉ Đọc<br/>Trạng Thái Blockchain]
        OBSERVER_ADMIN -->|Cung Cấp| PUBLIC_QUERY[Truy Vấn Công Cộng<br/>Load Balancing]
        OBSERVER_ADMIN -->|Đồng Bộ| CHAIN_SYNC[Đồng Bộ Chuỗi Khối]
    end

    subgraph "Sinh Viên"
        STUDENT_USER[Người Dùng Sinh Viên]
        STUDENT_USER -->|Nhận NFT| DEGREE_RECEIVE[Nhận Bằng Cấp NFT]
        STUDENT_USER -->|Quản Lý| WALLET_MANAGE[Quản Lý Ví Local<br/>Mnemonic Phrase]
        STUDENT_USER -->|Chỉ Đọc| DEGREE_VIEW[Xem Bằng Cấp Cá Nhân]
    end

    subgraph "Nhà Tuyển Dụng"
        EMPLOYER_USER[Người Dùng Nhà Tuyển Dụng]
        EMPLOYER_USER -->|Xác Minh| DEGREE_VERIFY[Yêu Cầu Xác Minh<br/>Bằng Cấp]
        EMPLOYER_USER -->|Truy Vấn| PUBLIC_VERIFY[Truy Vấn Công Cộng<br/>Không Cần Đăng Nhập]
    end

    subgraph "Quyền và Giới Hạn"
        PERM_MINT[Quyền Mint<br/>Chỉ Trường Đã Đăng Ký]
        PERM_BLOCK[Quyền Tạo Khối<br/>Chỉ Validators]
        PERM_VERIFY[Quyền Xác Minh<br/>Tất Cả Nodes]
        PERM_READ[Quyền Đọc<br/>Công Cộng]
    end

    AUTHORITY_SET --> UNI_ADMIN
    UNIVERSITY_REG --> UNI_ADMIN
    NETWORK_MONITOR --> UNI_ADMIN
    NETWORK_MONITOR --> OBSERVER_ADMIN

    DEGREE_MINT --> PERM_MINT
    BLOCK_CREATE --> PERM_BLOCK
    TX_VERIFY --> PERM_VERIFY
    READ_API --> PERM_READ
    PUBLIC_QUERY --> PERM_READ

    DEGREE_RECEIVE --> STUDENT_USER
    WALLET_MANAGE --> STUDENT_USER
    DEGREE_VIEW --> STUDENT_USER

    DEGREE_VERIFY --> EMPLOYER_USER
    PUBLIC_VERIFY --> EMPLOYER_USER
```

## Kiến Trúc Mạng Lưới

```mermaid
graph TB
    subgraph "Lớp Ứng Dụng"
        HTTP_API[HTTP/HTTPS APIs<br/>RESTful Endpoints]
        WS[WebSocket<br/>Cập Nhật Thời Gian Thực]
        RPC[Giao Diện RPC<br/>Truyền Thông Node]
    end

    subgraph "Lớp Vận Chuyển"
        TCP[Kết Nối TCP<br/>Giao Vận Đáng Tin Cậy]
        TLS[TLS 1.3<br/>Mã Hóa End-to-End]
        DTLS[DTLS<br/>Bảo Mật UDP]
    end

    subgraph "Lớp Mạng"
        P2P[Mạng P2P Overlay<br/>Giao Thức Gossip]
        DISCOVERY[Khám Phá Node<br/>Bootstrap Nodes]
        NAT[NAT Traversal<br/>STUN/TURN]
    end

    subgraph "Lớp Liên Kết"
        WIFI[WiFi/Ethernet<br/>Mạng Campus]
        VPN[Đường Hầm VPN<br/>Kết Nối An Toàn]
        CLOUD[Kết Nối Đám Mây<br/>AWS/Azure/GCP]
    end

    subgraph "Topology Mạng"
        STAR[Topology Sao<br/>MOET làm Hub]
        MESH[Mạng Mesh<br/>Peer-to-Peer]
        HYBRID[Mô Hình Hybrid<br/>Hierarchical]
    end

    HTTP_API --> TCP
    WS --> TCP
    RPC --> TCP
    TCP --> TLS
    TLS --> P2P
    P2P --> DISCOVERY
    P2P --> NAT
    DISCOVERY --> WIFI
    NAT --> WIFI
    WIFI --> VPN
    VPN --> CLOUD

    STAR -->|Tập Trung| HYBRID
    MESH -->|Phi Tập Trung| HYBRID
```

## Giao Thức Truyền Thông Giữa Các Nodes

```mermaid
sequenceDiagram
    participant Client
    participant LoadBalancer
    participant Observer
    participant Validator
    participant MOET

    Client->>LoadBalancer: Yêu Cầu HTTP (Gọi API)
    LoadBalancer->>Observer: Chuyển Đến Observer Gần Nhất
    Observer->>Observer: Truy Vấn State DB Local
    Observer->>Validator: Chuyển Tiếp Truy Vấn Phức Tạp
    Validator->>Validator: Xử Lý Dữ Liệu Đồng Thuận
    Validator->>MOET: Xác Minh Ủy Quyền
    MOET->>Validator: Phản Hồi Phê Duyệt
    Validator->>Observer: Trả Về Dữ Liệu Đã Xử Lý
    Observer->>LoadBalancer: Dữ Liệu Phản Hồi
    LoadBalancer->>Client: Phản Hồi JSON

    Note over Observer,Validator: P2P Gossip để Truyền Bá Khối
    Validator->>Validator: Phát Tán Khối Mới
    Validator->>Observer: Đồng Bộ Trạng Thái Blockchain
```

## Cấu Trúc Mạng P2P

```mermaid
graph TD
    subgraph "Bootstrap Nodes"
        BS1[Node MOET<br/>Bootstrap Chính]
        BS2[Validator A<br/>Bootstrap Phụ]
        BS3[Validator B<br/>Bootstrap Dự Phòng]
    end

    subgraph "Mạng Validator"
        V1[Validator 1<br/>Sản Xuất Khối Hoạt Động]
        V2[Validator 2<br/>Sản Xuất Khối Hoạt Động]
        V3[Validator 3<br/>Sản Xuất Khối Hoạt Động]
        V4[Validator 4<br/>Chờ Sẵn]
    end

    subgraph "Mạng Observer"
        O1[Observer 1<br/>Vùng Bắc]
        O2[Observer 2<br/>Vùng Nam]
        O3[Observer 3<br/>Vùng Trung]
        O4[Observer 4<br/>Quốc Tế]
    end

    subgraph "Kết Nối Client"
        C1[Clients Trường Đại Học]
        C2[Clients Sinh Viên]
        C3[Clients Nhà Tuyển Dụng]
    end

    BS1 --> V1
    BS1 --> V2
    BS1 --> V3
    BS2 --> V4
    BS3 --> O1

    V1 --> O1
    V1 --> O2
    V2 --> O2
    V2 --> O3
    V3 --> O3
    V3 --> O4
    V4 --> O4

    O1 --> C1
    O2 --> C2
    O3 --> C3
    O4 --> C1

    C1 -.->|Yêu Cầu Mint| V1
    C2 -.->|Xác Minh| O1
    C3 -.->|Truy Vấn Công Cộng| O2
```

## Bảo Mật Mạng

```mermaid
flowchart TD
    A[Yêu Cầu Đến] --> B{Xác Thực?}
    B -->|Không| C[Từ Chối Kết Nối]
    B -->|Có| D{Uỷ Quyền?}
    D -->|Không| E[Truy Cập Bị Từ Chối]
    D -->|Có| F{Giới Hạn Tốc Độ?}
    F -->|Vượt Quá| G[Hạn Chế Phản Hồi]
    F -->|OK| H{Mã Hóa?}
    H -->|Không| I[Mã Hóa Phản Hồi]
    H -->|Có| J[Xử Lý Yêu Cầu]
    J --> K[Xác Minh Dữ Liệu]
    K --> L[Thực Thi Hoạt Động]
    L --> M[Ghi Nhật Ký Hoạt Động]
    M --> N[Gửi Phản Hồi]
```

## Cân Bằng Tải và Dự Phòng

```mermaid
graph LR
    subgraph "Load Balancers"
        LB1[LB Chính<br/>AWS ELB]
        LB2[LB Phụ<br/>Azure LB]
        LB3[LB Dự Phòng<br/>GCP LB]
    end

    subgraph "Observer Clusters"
        OC1[Cluster Bắc<br/>3 Nodes]
        OC2[Cluster Nam<br/>3 Nodes]
        OC3[Cluster Trung<br/>3 Nodes]
    end

    subgraph "Validator Clusters"
        VC1[Validators Hoạt Động<br/>3 Nodes]
        VC2[Validators Chờ Sẵn<br/>2 Nodes]
    end

    subgraph "Hệ Thống Backup"
        BK1[Backup Ngoài Site<br/>AWS S3]
        BK2[Backup Local<br/>On-premise]
    end

    LB1 --> OC1
    LB1 --> OC2
    LB2 --> OC2
    LB2 --> OC3
    LB3 --> OC3
    LB3 --> OC1

    OC1 --> VC1
    OC2 --> VC1
    OC3 --> VC2

    VC1 --> BK1
    VC2 --> BK2