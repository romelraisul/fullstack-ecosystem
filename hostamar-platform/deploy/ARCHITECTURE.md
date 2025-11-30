# Hostamar Platform - Deployment Architecture

## Complete System Diagram

```mermaid
graph TB
    subgraph "Local Development"
        DEV[VS Code]
        AI[AI Agent/Copilot]
        GCLOUD[gcloud CLI]
    end
    
    subgraph "Network Layer"
        SSH[SSH Tunnel]
        RSYNC[rsync Data Transfer]
    end
    
    subgraph "GCP Mumbai VM (asia-south1-a)"
        subgraph "Application Layer"
            NODE[Node.js 20.x]
            NEXT[Next.js 14.2]
            PRISMA[Prisma ORM]
        end
        
        subgraph "Process Management"
            PM2[PM2 Process Manager]
        end
        
        subgraph "Database"
            SQLITE[(SQLite prod.db)]
        end
        
        subgraph "Web Server"
            NGINX[Nginx Reverse Proxy]
            SSL[Let's Encrypt SSL]
        end
    end
    
    subgraph "DNS & CDN"
        CF[Cloudflare]
        DNS[DNS Management]
    end
    
    subgraph "Users"
        BROWSER[Web Browser]
        MOBILE[Mobile App]
    end
    
    DEV -->|Commands| AI
    AI -->|Generate Scripts| GCLOUD
    GCLOUD -->|config-ssh| SSH
    DEV -->|Code Upload| RSYNC
    RSYNC --> NODE
    SSH --> NODE
    
    NODE --> NEXT
    NEXT --> PRISMA
    PRISMA --> SQLITE
    
    NEXT --> PM2
    PM2 -->|Restart on Crash| NEXT
    PM2 -->|Port 3000| NGINX
    
    NGINX --> SSL
    SSL -->|Port 443| CF
    CF --> DNS
    
    DNS -->|hostamar.com| BROWSER
    DNS -->|hostamar.com| MOBILE
    
    style DEV fill:#4CAF50
    style AI fill:#2196F3
    style NEXT fill:#000000,color:#fff
    style PM2 fill:#2B037A,color:#fff
    style NGINX fill:#009639
    style CF fill:#F38020
```

## Deployment Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant AI as VS Code AI Agent
    participant GCloud as gcloud CLI
    participant VM as GCP Mumbai VM
    participant Nginx as Nginx
    participant User as End User
    
    Dev->>AI: "Deploy to GCP Mumbai VM"
    AI->>GCloud: gcloud compute config-ssh
    GCloud->>VM: Configure SSH keys
    VM-->>GCloud: SSH ready
    
    AI->>Dev: SSH configured ✓
    
    Dev->>AI: "Upload code"
    AI->>VM: rsync (exclude node_modules)
    VM-->>AI: Upload complete
    
    AI->>VM: npm install --production
    AI->>VM: npx prisma db push
    AI->>VM: npm run build
    
    VM-->>AI: Build complete
    
    AI->>VM: pm2 start npm -- start
    VM-->>AI: App running on port 3000
    
    AI->>VM: Install & configure Nginx
    AI->>VM: Setup Let's Encrypt SSL
    
    VM-->>AI: SSL certificate installed
    
    User->>Nginx: https://hostamar.com
    Nginx->>VM: Proxy to localhost:3000
    VM-->>Nginx: Response
    Nginx-->>User: Secure Response
```

## Data Flow

```mermaid
flowchart LR
    A[User Request] --> B{Cloudflare}
    B --> C[Nginx :443]
    C --> D{SSL Termination}
    D --> E[Nginx Proxy]
    E --> F[Next.js :3000]
    F --> G{API Route?}
    G -->|Yes| H[API Handler]
    G -->|No| I[Page Component]
    H --> J[Prisma Client]
    I --> J
    J --> K[(SQLite DB)]
    K --> J
    J --> H
    J --> I
    H --> F
    I --> F
    F --> E
    E --> C
    C --> B
    B --> A
    
    style B fill:#F38020
    style C fill:#009639
    style F fill:#000000,color:#fff
    style K fill:#003B57,color:#fff
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (Next.js)
    participant A as NextAuth API
    participant P as Prisma
    participant D as Database
    
    U->>F: Visit /auth/signup
    F->>U: Show signup form
    U->>F: Submit (email, password, business)
    F->>A: POST /api/auth/signup
    A->>P: Check existing customer
    P->>D: SELECT * FROM Customer
    D-->>P: Not found
    P-->>A: User doesn't exist
    A->>A: Hash password (bcrypt)
    A->>P: Create Customer + Business
    P->>D: INSERT Customer, Business
    D-->>P: Success
    P-->>A: Customer created
    A->>A: Auto sign-in (NextAuth)
    A-->>F: Session + JWT token
    F-->>U: Redirect to /dashboard
```

## PM2 Process Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Stopped
    Stopped --> Starting: pm2 start
    Starting --> Online: Process launched
    Online --> Stopping: pm2 stop
    Stopping --> Stopped
    Online --> Errored: Crash detected
    Errored --> Starting: Auto-restart
    Online --> Reloading: pm2 reload
    Reloading --> Online: Zero-downtime
    
    note right of Online
        CPU: ~100-200%
        Memory: ~500MB
        Port: 3000
    end note
    
    note right of Errored
        PM2 triggers
        restart after 1s
    end note
```

## CI/CD Pipeline (Future)

```mermaid
flowchart TD
    A[Git Push] --> B{GitHub Actions}
    B --> C[Run Tests]
    C --> D{Tests Pass?}
    D -->|No| E[Notify Developer]
    D -->|Yes| F[Build Production]
    F --> G[Run eval/metrics.js]
    G --> H{Quality OK?}
    H -->|No| E
    H -->|Yes| I[Deploy to VM]
    I --> J[rsync to Mumbai VM]
    J --> K[pm2 reload hostamar]
    K --> L[Health Check]
    L --> M{Healthy?}
    M -->|No| N[Rollback]
    M -->|Yes| O[Deployment Success]
    N --> P[Restore Previous Version]
    P --> E
    
    style C fill:#2196F3
    style F fill:#4CAF50
    style K fill:#2B037A,color:#fff
    style O fill:#4CAF50
```

## Monitoring & Alerting (Future)

```mermaid
graph TB
    subgraph "Application Metrics"
        HEALTH[/api/health]
        PM2M[PM2 Metrics]
        LOGS[Application Logs]
    end
    
    subgraph "System Metrics"
        CPU[CPU Usage]
        MEM[Memory Usage]
        DISK[Disk Space]
        NET[Network Traffic]
    end
    
    subgraph "Monitoring Stack"
        PROM[Prometheus]
        GRAF[Grafana]
    end
    
    subgraph "Alerting"
        SLACK[Slack Webhook]
        EMAIL[Email Alerts]
    end
    
    HEALTH --> PROM
    PM2M --> PROM
    LOGS --> PROM
    CPU --> PROM
    MEM --> PROM
    DISK --> PROM
    NET --> PROM
    
    PROM --> GRAF
    GRAF --> SLACK
    GRAF --> EMAIL
    
    style PROM fill:#E6522C
    style GRAF fill:#F46800
```

## Security Layers

```mermaid
flowchart LR
    A[Internet] --> B[Cloudflare WAF]
    B --> C{DDoS Protection}
    C --> D[GCP Firewall]
    D --> E{Port Filtering}
    E -->|:80,:443,:22| F[Nginx]
    F --> G{Rate Limiting}
    G --> H[SSL/TLS]
    H --> I[Next.js App]
    I --> J{NextAuth}
    J -->|Authenticated| K[Protected Routes]
    J -->|Public| L[Public Routes]
    K --> M[Prisma]
    L --> M
    M --> N{Query Validation}
    N --> O[(Database)]
    
    style B fill:#F38020
    style D fill:#4285F4
    style H fill:#009639
    style J fill:#000000,color:#fff
```

## Deployment States

```mermaid
stateDiagram-v2
    [*] --> LocalDev: npm run dev
    LocalDev --> Committed: git commit
    Committed --> Pushed: git push
    Pushed --> Building: CI/CD triggered
    Building --> Testing: npm test
    Testing --> Deploying: rsync to VM
    Deploying --> Running: pm2 restart
    Running --> Monitoring: Health checks
    Monitoring --> Running: All OK
    Monitoring --> AlertTriggered: Issue detected
    AlertTriggered --> Investigating: Team notified
    Investigating --> Fixing: Deploy hotfix
    Fixing --> Running: Fixed
    Running --> [*]: Stable
```

---

## Legend

- **Green boxes**: Development/Success states
- **Blue boxes**: Processing/Active states
- **Purple boxes**: Process managers
- **Orange boxes**: CDN/Proxy layers
- **Black boxes**: Core application
- **Red/Orange boxes**: Monitoring/Alerting

---

*Generated for Hostamar Platform Deployment*  
*Last Updated: November 29, 2025*
