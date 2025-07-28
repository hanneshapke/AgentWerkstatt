# Langfuse Docker Compose Setup

This directory contains a complete Docker Compose configuration for running Langfuse locally.

## Quick Start

1. **Update Security Settings**: Before starting, you should change the default passwords and secrets in `docker-compose.yaml`. Look for lines marked with `# CHANGEME`:

   - `DATABASE_URL`: Change the postgres password
   - `SALT`: Use a secure random salt
   - `ENCRYPTION_KEY`: Generate with `openssl rand -hex 32`
   - `NEXTAUTH_SECRET`: Use a secure random secret
   - `CLICKHOUSE_PASSWORD`: Change the ClickHouse password
   - `REDIS_AUTH`: Change the Redis password
   - `MINIO_ROOT_PASSWORD`: Change the MinIO password
   - `POSTGRES_PASSWORD`: Change the PostgreSQL password

2. **Start Langfuse**:
   ```bash
   docker compose up
   ```

3. **Access the Application**:
   - Langfuse UI: http://localhost:3000
   - MinIO Console: http://localhost:9091

## Services Included

- **langfuse-web**: Main Langfuse application (port 3000)
- **langfuse-worker**: Background worker for processing
- **postgres**: PostgreSQL database
- **clickhouse**: ClickHouse for analytics
- **redis**: Redis for caching and queues
- **minio**: S3-compatible object storage

## Security Notes

- Most services are bound to localhost (127.0.0.1) for security
- Only langfuse-web (port 3000) and minio (port 9090) are exposed externally
- Change all default passwords before production use

## Data Persistence

Data is persisted in Docker volumes:
- `langfuse_postgres_data`
- `langfuse_clickhouse_data`
- `langfuse_clickhouse_logs`
- `langfuse_minio_data`

## Stopping the Services

```bash
docker compose down
```

To also remove volumes:
```bash
docker compose down -v
```

## Generating Secure Secrets

Generate a secure encryption key:
```bash
openssl rand -hex 32
```

Generate other secure passwords:
```bash
openssl rand -base64 32
```

## More Information

For detailed configuration options and production deployment guidance, visit:
https://langfuse.com/self-hosting/docker-compose
