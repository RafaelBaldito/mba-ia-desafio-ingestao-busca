"""Opt-in persistence contract test against an isolated pgVector service."""

from __future__ import annotations

import os
import socket
import subprocess
import time
import uuid
from math import cos, radians, sin
from pathlib import Path

import psycopg
import pytest
from langchain_core.documents import Document

from src.ingestion_config import APPROVED_EMBEDDING_MODEL, IngestionSettings
from src.ingestion_store import COLLECTION_METADATA, EMBEDDING_LENGTH, persist_chunks
from src.search import retrieve
from src.chat_config import APPROVED_CHAT_MODEL, ChatSettings


COMPOSE_FILE = Path(__file__).with_name("compose.yaml")
pytestmark = pytest.mark.pgvect_integration


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _docker_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, text=True, timeout=15
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


class DeterministicEmbeddings:
    """A local 1536-dimensional embedding implementation for database tests."""

    last_kwargs: dict[str, str] = {}

    def __init__(self, **kwargs):
        type(self).last_kwargs = kwargs

    def _vector(self, text: str) -> list[float]:
        if text == "find the closest integration documents":
            angle = 0.0
        else:
            rank = int(text.removeprefix("integration document "))
            angle = radians(rank)
        return [cos(angle), sin(angle)] + [0.0] * (EMBEDDING_LENGTH - 2)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


@pytest.fixture
def isolated_pgvector():
    if os.environ.get("RUN_PGVECTOR_INTEGRATION") != "1":
        pytest.skip("set RUN_PGVECTOR_INTEGRATION=1 to run the Docker integration test")
    if not _docker_available():
        pytest.skip("Docker daemon is unavailable")

    project = f"wave1-pgvector-{uuid.uuid4().hex[:12]}"
    database = f"wave1_{uuid.uuid4().hex[:12]}"
    port = _free_port()
    compose = ["docker", "compose", "-p", project, "-f", str(COMPOSE_FILE)]
    environment = os.environ.copy()
    environment.update(
        {
            "PGVECTOR_TEST_PORT": str(port),
            "PGVECTOR_TEST_DB": database,
            "PGVECTOR_TEST_USER": "wave1_test",
            "PGVECTOR_TEST_PASSWORD": "wave1_test_password",
        }
    )

    try:
        start = subprocess.run(
            [*compose, "up", "-d", "--wait", "postgres"],
            capture_output=True,
            text=True,
            env=environment,
            timeout=120,
        )
        if start.returncode != 0:
            pytest.fail(f"isolated PostgreSQL startup failed:\n{start.stderr}")

        bootstrap = subprocess.run(
            [*compose, "run", "--rm", "bootstrap_vector_ext"],
            capture_output=True,
            text=True,
            env=environment,
            timeout=120,
        )
        if bootstrap.returncode != 0:
            pytest.fail(f"pgVector extension bootstrap failed:\n{bootstrap.stderr}")

        url = (
            f"postgresql+psycopg://wave1_test:wave1_test_password@127.0.0.1:{port}/{database}"
        )
        psycopg_url = url.replace("postgresql+psycopg://", "postgresql://", 1)
        deadline = time.monotonic() + 30
        while True:
            try:
                with psycopg.connect(psycopg_url) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                        if cursor.fetchone() is not None:
                            break
            except psycopg.OperationalError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.5)

        yield IngestionSettings(
            openai_api_key="integration-test-key",
            openai_embedding_model=APPROVED_EMBEDDING_MODEL,
            database_url=url,
            collection_name=f"wave1_collection_{uuid.uuid4().hex[:8]}",
            pdf_path=Path("document.pdf"),
        )
    finally:
        subprocess.run(
            [*compose, "down", "--volumes", "--remove-orphans"],
            capture_output=True,
            text=True,
            env=environment,
            timeout=120,
        )


def test_pgvector_persists_retrievable_text_embeddings_and_collection(isolated_pgvector):
    settings = isolated_pgvector
    embedding = DeterministicEmbeddings()
    documents = [
        Document(
            page_content=f"integration document {index}",
            metadata={"source": "document.pdf", "chunk_index": index},
        )
        for index in range(12)
    ]

    count = persist_chunks(settings, documents, embedding)

    assert count == 12
    psycopg_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(psycopg_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT e.document, vector_dims(e.embedding), c.name
                FROM langchain_pg_embedding AS e
                JOIN langchain_pg_collection AS c ON c.uuid = e.collection_id
                """
            )
            rows = cursor.fetchall()

    assert len(rows) == 12
    assert {row[1] for row in rows} == {EMBEDDING_LENGTH}
    assert {row[2] for row in rows} == {settings.collection_name}
    assert COLLECTION_METADATA["embedding_model"] == APPROVED_EMBEDDING_MODEL

    chat_settings = ChatSettings(
        openai_api_key="integration-test-key",
        openai_embedding_model=APPROVED_EMBEDDING_MODEL,
        openai_chat_model=APPROVED_CHAT_MODEL,
        database_url=settings.database_url,
        collection_name=settings.collection_name,
    )
    retrieved = retrieve(
        "find the closest integration documents",
        chat_settings,
        embedding_factory=DeterministicEmbeddings,
    )

    assert len(retrieved) == 10
    assert [chunk.page_content for chunk in retrieved] == [
        f"integration document {index}" for index in range(10)
    ]
    assert [chunk.score for chunk in retrieved] == sorted(chunk.score for chunk in retrieved)
    assert DeterministicEmbeddings.last_kwargs == {
        "model": APPROVED_EMBEDDING_MODEL,
        "api_key": "integration-test-key",
    }
