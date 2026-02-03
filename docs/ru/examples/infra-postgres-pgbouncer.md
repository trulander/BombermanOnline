# Схема подключения PostgreSQL через PgBouncer

Диаграмма показывает, как PgBouncer располагается между сервисами приложений и PostgreSQL.

```mermaid
sequenceDiagram
    participant GameService
    participant AuthService
    participant PgBouncer
    participant PostgreSQL
    GameService->>PgBouncer: SQL queries
    AuthService->>PgBouncer: SQL queries
    PgBouncer->>PostgreSQL: Pooled connection
    PostgreSQL-->>PgBouncer: Results
    PgBouncer-->>GameService: Results
    PgBouncer-->>AuthService: Results
```

