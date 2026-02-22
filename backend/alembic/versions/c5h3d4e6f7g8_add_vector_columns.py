"""Add vector embedding columns and HNSW indexes for RAG.

Revision ID: c5h3d4e6f7g8
Revises: b4g2c3d5e7f8
Create Date: 2026-02-20 00:00:02.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c5h3d4e6f7g8"
down_revision = "b4g2c3d5e7f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgvector extension is available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding columns (1536-dim for text-embedding-3-small)
    op.execute("ALTER TABLE response_library ADD COLUMN embedding vector(1536)")
    op.execute("ALTER TABLE procedures ADD COLUMN embedding vector(1536)")
    op.execute("ALTER TABLE medical_terms ADD COLUMN embedding vector(1536)")

    # Create HNSW indexes for cosine distance search
    op.execute(
        "CREATE INDEX ix_response_library_embedding "
        "ON response_library USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_procedures_embedding "
        "ON procedures USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_medical_terms_embedding "
        "ON medical_terms USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_index("ix_medical_terms_embedding", "medical_terms")
    op.drop_index("ix_procedures_embedding", "procedures")
    op.drop_index("ix_response_library_embedding", "response_library")

    op.execute("ALTER TABLE medical_terms DROP COLUMN embedding")
    op.execute("ALTER TABLE procedures DROP COLUMN embedding")
    op.execute("ALTER TABLE response_library DROP COLUMN embedding")
