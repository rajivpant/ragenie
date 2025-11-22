"""Add ragbot-data and embedding queue tables

Revision ID: 002
Revises: 001
Create Date: 2025-11-22 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ragbot_documents table for ragbot-data source files
    op.create_table(
        'ragbot_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),  # Relative to /data/ragbot-data
        sa.Column('content_hash', sa.String(length=64), nullable=False),  # SHA-256
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('modified_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('indexed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('embedding_status', sa.String(length=20), nullable=False, server_default='pending'),  # pending, indexed, failed
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),  # Extracted frontmatter, tags, category, etc.
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_path')
    )
    op.create_index(op.f('ix_ragbot_documents_id'), 'ragbot_documents', ['id'], unique=False)
    op.create_index(op.f('ix_ragbot_documents_file_path'), 'ragbot_documents', ['file_path'], unique=True)
    op.create_index(op.f('ix_ragbot_documents_embedding_status'), 'ragbot_documents', ['embedding_status'], unique=False)
    op.create_index(op.f('ix_ragbot_documents_content_hash'), 'ragbot_documents', ['content_hash'], unique=False)

    # Create GIN index for full-text search on file_path
    op.execute("""
        CREATE INDEX ix_ragbot_documents_file_path_fts
        ON ragbot_documents
        USING gin(to_tsvector('english', file_path))
    """)

    # Rename existing documents table to user_uploads for clarity
    op.rename_table('documents', 'user_uploads')

    # Update indexes for renamed table
    op.execute("ALTER INDEX ix_documents_id RENAME TO ix_user_uploads_id")
    op.execute("ALTER INDEX ix_documents_user_id RENAME TO ix_user_uploads_user_id")
    op.execute("ALTER INDEX ix_documents_profile_id RENAME TO ix_user_uploads_profile_id")

    # Create embedding_queue table for async processing
    op.create_table(
        'embedding_queue',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
        sa.Column('document_type', sa.String(length=20), nullable=False),  # 'ragbot' or 'user_upload'
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),  # 1-10, higher = more urgent
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),  # pending, processing, completed, failed
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_embedding_queue_id'), 'embedding_queue', ['id'], unique=False)
    op.create_index(op.f('ix_embedding_queue_status'), 'embedding_queue', ['status'], unique=False)
    op.create_index(op.f('ix_embedding_queue_document_type'), 'embedding_queue', ['document_type'], unique=False)
    op.create_index(op.f('ix_embedding_queue_document_id'), 'embedding_queue', ['document_id'], unique=False)

    # Create composite index for efficient queue processing (status + priority DESC)
    op.create_index(
        'ix_embedding_queue_status_priority',
        'embedding_queue',
        ['status', sa.text('priority DESC')],
        unique=False
    )

    # Add embedding_status column to user_uploads table (renamed from documents)
    op.add_column('user_uploads', sa.Column('embedding_status', sa.String(length=20), nullable=False, server_default='pending'))
    op.add_column('user_uploads', sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('user_uploads', sa.Column('indexed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_uploads', sa.Column('error_message', sa.Text(), nullable=True))

    # Create index for embedding_status on user_uploads
    op.create_index(op.f('ix_user_uploads_embedding_status'), 'user_uploads', ['embedding_status'], unique=False)

    # Add state column to conversations for LangGraph integration
    op.add_column('conversations', sa.Column('state', sa.JSON(), nullable=True))
    op.execute("COMMENT ON COLUMN conversations.state IS 'LangGraph workflow state persistence'")


def downgrade() -> None:
    # Remove state column from conversations
    op.drop_column('conversations', 'state')

    # Remove columns from user_uploads
    op.drop_index(op.f('ix_user_uploads_embedding_status'), table_name='user_uploads')
    op.drop_column('user_uploads', 'error_message')
    op.drop_column('user_uploads', 'indexed_at')
    op.drop_column('user_uploads', 'chunk_count')
    op.drop_column('user_uploads', 'embedding_status')

    # Drop embedding_queue table
    op.drop_index('ix_embedding_queue_status_priority', table_name='embedding_queue')
    op.drop_index(op.f('ix_embedding_queue_document_id'), table_name='embedding_queue')
    op.drop_index(op.f('ix_embedding_queue_document_type'), table_name='embedding_queue')
    op.drop_index(op.f('ix_embedding_queue_status'), table_name='embedding_queue')
    op.drop_index(op.f('ix_embedding_queue_id'), table_name='embedding_queue')
    op.drop_table('embedding_queue')

    # Rename user_uploads back to documents
    op.execute("ALTER INDEX ix_user_uploads_id RENAME TO ix_documents_id")
    op.execute("ALTER INDEX ix_user_uploads_user_id RENAME TO ix_documents_user_id")
    op.execute("ALTER INDEX ix_user_uploads_profile_id RENAME TO ix_documents_profile_id")
    op.rename_table('user_uploads', 'documents')

    # Drop ragbot_documents table
    op.execute("DROP INDEX ix_ragbot_documents_file_path_fts")
    op.drop_index(op.f('ix_ragbot_documents_content_hash'), table_name='ragbot_documents')
    op.drop_index(op.f('ix_ragbot_documents_embedding_status'), table_name='ragbot_documents')
    op.drop_index(op.f('ix_ragbot_documents_file_path'), table_name='ragbot_documents')
    op.drop_index(op.f('ix_ragbot_documents_id'), table_name='ragbot_documents')
    op.drop_table('ragbot_documents')
