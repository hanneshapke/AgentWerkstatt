# Mem0 Memory System Setup

This document explains how to set up and use the mem0 memory management system with the AgentWerkstatt Docker Compose stack using the official mem0 server with PostgreSQL and Neo4j support.

## Overview

mem0 is an AI memory management system that provides persistent contextual memory for AI agents. It allows agents to:
- Remember previous conversations and context
- Learn from interactions over time
- Maintain user preferences and behavioral patterns
- Store and retrieve semantic memories

## Architecture

The mem0 setup includes three main containers:

1. **mem0**: The official mem0 server built from the [mem0ai/mem0 repository](https://github.com/mem0ai/mem0) with PostgreSQL support
2. **postgres**: PostgreSQL database with pgvector extension for vector storage (shared with Langfuse)
3. **neo4j**: Graph database for storing memory relationships

## Configuration

### Environment Variables

Set the following environment variable before starting the services:

```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

Or create a `.env` file in the `3rd_party` directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### Services

#### mem0 Service
- **Build**: Two-stage build process:
  1. `mem0-base`: Built from `https://github.com/mem0ai/mem0.git` using `server/dev.Dockerfile`
  2. `mem0`: Extends `mem0-base` with PostgreSQL support (psycopg2-binary) and SQLite database initialization
- **Port**: `8000` (accessible at `http://localhost:8000`)
- **Dependencies**: PostgreSQL and Neo4j
- **Environment Variables**:
  - `OPENAI_API_KEY`: Required for LLM and embedding operations
  - `HISTORY_DB_PATH`: SQLite database path (set to `/app/.mem0/history.db`)
- **Volumes**:
  - `mem0_data:/app/.mem0` for persistent storage
  - `./mem0-config.yaml:/app/config.yaml:ro` for configuration (note: environment variables take precedence)

#### PostgreSQL Service (Shared)
- **Image**: `pgvector/pgvector:pg17` (includes pgvector extension for vector storage)
- **Port**: `5432`
- **Database**: `postgres` with pgvector extension enabled

#### Neo4j Service
- **Image**: `neo4j:5.26.4`
- **Ports**: `8474` (HTTP), `8687` (Bolt)
- **Volumes**: `neo4j_data:/data` for persistent graph storage
- **Credentials**: `neo4j/mem0graph`

## Usage

### Starting the Services

```bash
cd 3rd_party
docker compose up -d mem0 neo4j postgres
```

Or from the project root:

```bash
docker compose -f 3rd_party/docker-compose.yaml up -d
```

### Building from Source

The first time you run this, Docker will:
1. Build `mem0-base` from the official mem0 repository
2. Build the final `mem0` image with PostgreSQL support and SQLite database initialization
3. Start the server with environment-based configuration

This process may take several minutes on the first run as it builds both images.

### Accessing mem0

The mem0 server provides a REST API at `http://localhost:8000` with endpoints:
- `POST /memories` - Add new memories
- `GET /memories` - List memories (requires query parameters)
- `POST /search` - Search memories
- `GET /memories/{memory_id}` - Get specific memory
- `DELETE /memories/{memory_id}` - Delete memory
- `GET /docs` - API documentation (Swagger UI)

## Memory Configuration

⚠️ **Important**: The mem0 server uses **environment variables** for configuration, not the `mem0-config.yaml` file. The config file is available for reference but environment variables take precedence.

### Actual Configuration (via Environment Variables)

The server configures itself using these environment variables:
- **Vector Store**: PostgreSQL with pgvector extension
- **Graph Store**: Neo4j for relationship storage
- **LLM**: OpenAI GPT-4o for memory processing
- **Embeddings**: OpenAI text-embedding-3-small for vector storage
- **History**: SQLite database at `/app/.mem0/history.db`

### Configuration File (Reference Only)

While a `mem0-config.yaml` is mounted, the actual configuration comes from environment variables defined in `main.py`. The config file serves as documentation of the expected structure.

## Integration with AgentWerkstatt

To use mem0 with your AgentWerkstatt agent:

1. Ensure the `memory` optional dependency is installed:
   ```bash
   pip install agentwerkstatt[memory]
   ```

2. Configure memory in `agent_config.yaml`:
   ```yaml
   memory:
     enabled: true
     model_name: "gpt-4o-mini"
     server_url: "http://localhost:8000"  # mem0 server endpoint
   ```

3. The agent will connect to the mem0 server API running on `localhost:8000`

## Data Persistence

Memory data is persisted in Docker volumes:
- `mem0_data`: Contains the SQLite history database and mem0 application data
- `neo4j_data`: Contains the Neo4j graph database
- `langfuse_postgres_data`: Contains PostgreSQL data (shared with Langfuse, includes vector embeddings)

## Troubleshooting

### Container Logs

Check the logs if services aren't starting properly:

```bash
docker compose -f 3rd_party/docker-compose.yaml logs mem0
docker compose -f 3rd_party/docker-compose.yaml logs neo4j
docker compose -f 3rd_party/docker-compose.yaml logs postgres
```

### Common Issues

1. **Missing OpenAI API Key**: Ensure `OPENAI_API_KEY` is set in environment or `.env` file
2. **psycopg2 Import Error**: Fixed automatically by Dockerfile.mem0 which installs psycopg2-binary
3. **pgvector Extension Error**: Fixed by using `pgvector/pgvector` PostgreSQL image
4. **SQLite Database Error**: Fixed by pre-creating database during image build and setting `HISTORY_DB_PATH`
5. **Neo4j Connection Error**: Fixed by ensuring mem0 container is on both default and mem0_network
6. **Configuration Validation Error**: Fixed by using correct field names (e.g., `dbname` instead of `database`)
7. **Port Conflicts**: Ensure ports 8474, 8687, 5432, and 8000 are available

### Health Checks

- **mem0**: `http://localhost:8000/` (redirects to docs) or `http://localhost:8000/docs`
- **Neo4j**: `http://localhost:8474` (Neo4j Browser)
- **PostgreSQL**: Use `psql` or any PostgreSQL client on port 5432

### API Testing

Test the mem0 API (note: no `/v1` prefix):

```bash
# Add a memory
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I like pizza"}
    ],
    "user_id": "test_user"
  }'

# Search memories
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "food preferences",
    "user_id": "test_user"
  }'

# View API documentation
curl http://localhost:8000/docs
```

### Expected API Response Format

Successful memory creation returns:
```json
{
  "results": [
    {
      "id": "uuid-here",
      "memory": "Extracted memory text",
      "event": "ADD"
    }
  ],
  "relations": {
    "deleted_entities": [],
    "added_entities": [[{
      "source": "user_id:_test_user",
      "relationship": "relationship_type",
      "target": "target_entity"
    }]]
  }
}
```

## Security Notes

- All services are bound to `127.0.0.1` (localhost) for security
- No external access is allowed without proper network configuration
- OpenAI API key should be kept secure and not committed to version control
- Neo4j default credentials are `neo4j/mem0graph` (change in production)
- PostgreSQL uses default credentials (shared with Langfuse setup)

## Advanced Configuration

### Environment Variables Override

To customize mem0 behavior, set these environment variables in docker-compose.yaml:

```yaml
environment:
  OPENAI_API_KEY: ${OPENAI_API_KEY}
  HISTORY_DB_PATH: /app/.mem0/history.db
  POSTGRES_HOST: postgres
  POSTGRES_PORT: 5432
  POSTGRES_DB: postgres
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres
  NEO4J_URI: bolt://neo4j:7687
  NEO4J_USERNAME: neo4j
  NEO4J_PASSWORD: mem0graph
```

### Using Different Vector Stores

If you prefer to use Qdrant instead of PostgreSQL, you would need to:
1. Add Qdrant service to docker-compose.yaml
2. Modify environment variables to point to Qdrant
3. Note: This requires changes to the mem0 server's main.py configuration

## Building Process

The Docker build process uses a two-stage approach:

1. **Stage 1 (`mem0-base`)**:
   - Clones `https://github.com/mem0ai/mem0.git`
   - Uses `server/dev.Dockerfile` from the repository
   - Creates the base mem0 server image

2. **Stage 2 (`mem0`)**:
   - Extends `mem0-base` using our custom `Dockerfile.mem0`
   - Adds PostgreSQL support (`psycopg2-binary`)
   - Pre-creates SQLite database directory and initialization
   - Ensures all dependencies are properly installed

This approach ensures you're using the latest official mem0 server code while adding the necessary dependencies and fixes to prevent common startup errors.

## Known Limitations

- The mem0 server prioritizes environment variables over mounted configuration files
- Health checks may show 307 redirects which are normal (root redirects to /docs)
- First startup may take longer due to vector database initialization
- API endpoints do not use `/v1` prefix despite some documentation suggesting otherwise
