# PDF RAG Assistant

> A command-line Retrieval-Augmented Generation (RAG) assistant that turns a PDF into a searchable knowledge base and produces answers grounded in its content.

[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?logo=openai&logoColor=white)](https://platform.openai.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![LangChain](https://img.shields.io/badge/LangChain-Framework-1C3C3C)](https://www.langchain.com/)

## Overview

PDF RAG Assistant ingests a local PDF, splits it into overlapping chunks, creates OpenAI embeddings, and stores them in PostgreSQL with pgvector. At query time, it retrieves the ten most relevant chunks and uses them as the only context for the generated answer.

The result is a focused, reproducible command-line workflow for exploring document content without relying on external knowledge.

```mermaid
flowchart LR
    A[PDF document] --> B[Load and split into chunks]
    B --> C[OpenAI embeddings]
    C --> D[(PostgreSQL + pgvector)]
    E[User question] --> F[Semantic retrieval]
    D --> F
    F --> G[10 relevant chunks]
    G --> H[Grounded OpenAI answer]
```

## Highlights

- **Reproducible ingestion** — replaces the configured collection with the current PDF content.
- **Semantic retrieval** — uses vector similarity to retrieve exactly ten relevant chunks per question.
- **Grounded responses** — prompts the model to answer solely from retrieved document context.
- **Safe configuration** — validates required settings and avoids exposing API keys or connection strings in errors.
- **Simple local stack** — runs PostgreSQL and pgvector through Docker Compose.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python |
| Document processing | PyPDF / LangChain |
| Embeddings and chat | OpenAI API |
| Vector storage | PostgreSQL + pgvector |
| Orchestration | LangChain |
| Local infrastructure | Docker Compose |

## Getting Started

### Prerequisites

- Python with `pip`
- Docker and Docker Compose
- An OpenAI API key with access to the configured models
- A PDF file available locally (the default path is `document.pdf` at the repository root)

### 1. Create the Python environment

```bash
python -m venv .venv

# Linux/macOS
. .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
```

### 2. Configure local environment variables

Create your local configuration file:

```bash
# Linux/macOS
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

Then update `.env` with your local credentials and database connection. Never commit this file.

| Variable | Purpose | Required value / example |
| --- | --- | --- |
| `OPENAI_API_KEY` | Authenticates requests to OpenAI | Your local API key |
| `OPENAI_EMBEDDING_MODEL` | Embedding model used for ingestion and search | `text-embedding-3-small` |
| `OPENAI_CHAT_MODEL` | Chat model used to answer questions | `gpt-5.4-mini` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://postgres:postgres@localhost:5432/rag` |
| `PG_VECTOR_COLLECTION_NAME` | Target pgvector collection | A valid local collection name |
| `PDF_PATH` | Source document path | `document.pdf` |

### 3. Start PostgreSQL with pgvector

```bash
docker compose up -d
docker compose ps
```

Wait for `postgres` to become healthy and for `bootstrap_vector_ext` to finish successfully.

### 4. Ingest the PDF

```bash
python src/ingest.py
```

The ingestion step must complete before the chat can answer questions.

### 5. Start the assistant

```bash
python src/chat.py
```

## Usage

The terminal accepts one independent question at a time. Ask about information present in the ingested PDF:

```text
PERGUNTA: What information does the document provide about <topic>?
RESPOSTA: <answer based on the retrieved chunks>
```

Questions that cannot be supported by the retrieved context receive the fallback response:

```text
PERGUNTA: What is the capital of France?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.
```

To finish the session, enter `sair`, `exit`, or `quit`, or use `Ctrl+C` / EOF. An empty question requests a new input, and temporary service failures are handled safely so another question can be attempted.

## How It Works

1. The ingestion command loads the configured PDF and splits it into overlapping chunks.
2. Each chunk is transformed into a vector embedding and persisted in the selected pgvector collection.
3. For every question, the application performs similarity search and validates that ten chunks are available.
4. The chat model receives the question together with those chunks and is instructed not to use information outside them.

## Project Structure

```text
src/
├── ingest.py                  # Ingestion CLI entry point
├── ingestion_*.py             # Configuration, document, and storage workflow
├── chat.py                    # Interactive chat CLI
├── chat_config.py             # Chat configuration validation
└── search.py                  # Retrieval and grounded prompt construction

docker-compose.yml             # PostgreSQL + pgvector local stack
.env.example                   # Configuration template
```

## Validation

Run the automated test suite:

```bash
python -m pytest
```

Run the project coverage gate:

```bash
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90
```
