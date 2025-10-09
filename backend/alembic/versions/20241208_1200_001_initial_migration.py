"""Initial migration - Create all tables

Revision ID: 001
Revises: 
Create Date: 2024-12-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types (checkfirst=True prevents duplicates)
    user_role_enum = postgresql.ENUM('admin', 'operator', 'viewer', name='userrole', create_type=False)
    user_role_enum.create(op.get_bind(), checkfirst=True)

    document_status_enum = postgresql.ENUM('active', 'archived', 'deleted', name='documentstatus', create_type=False)
    document_status_enum.create(op.get_bind(), checkfirst=True)

    priority_enum = postgresql.ENUM('low', 'medium', 'high', name='priority', create_type=False)
    priority_enum.create(op.get_bind(), checkfirst=True)

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('microsoft_id', sa.String(length=255), nullable=True),
        sa.Column('role', user_role_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('profile_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_microsoft_id'), 'users', ['microsoft_id'], unique=True)

    # Create document_types table
    op.create_table('document_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_extensions', sa.JSON(), nullable=True),
        sa.Column('max_file_size', sa.Integer(), nullable=True),
        sa.Column('template_path', sa.String(length=500), nullable=True),
        sa.Column('qr_position', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_types_id'), 'document_types', ['id'], unique=False)
    op.create_index(op.f('ix_document_types_name'), 'document_types', ['name'], unique=True)

    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('original_file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('document_type_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('status', document_status_enum, nullable=False),
        sa.Column('priority', priority_enum, nullable=False),
        sa.Column('onedrive_file_id', sa.String(length=255), nullable=True),
        sa.Column('onedrive_path', sa.String(length=500), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_type_id'], ['document_types.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_document_type_id'), 'documents', ['document_type_id'], unique=False)
    op.create_index(op.f('ix_documents_file_name'), 'documents', ['file_name'], unique=True)
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)
    op.create_index(op.f('ix_documents_title'), 'documents', ['title'], unique=False)
    op.create_index(op.f('ix_documents_uploaded_by'), 'documents', ['uploaded_by'], unique=False)

    # Create qr_codes table
    op.create_table('qr_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('qr_data', sa.Text(), nullable=False),
        sa.Column('qr_image_path', sa.String(length=500), nullable=True),
        sa.Column('qr_code', sa.String(length=100), nullable=False),
        sa.Column('position_data', sa.JSON(), nullable=True),
        sa.Column('generated_by', sa.Integer(), nullable=False),
        sa.Column('scan_count', sa.Integer(), nullable=True),
        sa.Column('last_scanned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['generated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_qr_codes_document_id'), 'qr_codes', ['document_id'], unique=False)
    op.create_index(op.f('ix_qr_codes_id'), 'qr_codes', ['id'], unique=False)
    op.create_index(op.f('ix_qr_codes_qr_code'), 'qr_codes', ['qr_code'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_qr_codes_qr_code'), table_name='qr_codes')
    op.drop_index(op.f('ix_qr_codes_id'), table_name='qr_codes')
    op.drop_index(op.f('ix_qr_codes_document_id'), table_name='qr_codes')
    op.drop_table('qr_codes')
    
    op.drop_index(op.f('ix_documents_uploaded_by'), table_name='documents')
    op.drop_index(op.f('ix_documents_title'), table_name='documents')
    op.drop_index(op.f('ix_documents_status'), table_name='documents')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_file_name'), table_name='documents')
    op.drop_index(op.f('ix_documents_document_type_id'), table_name='documents')
    op.drop_table('documents')
    
    op.drop_index(op.f('ix_document_types_name'), table_name='document_types')
    op.drop_index(op.f('ix_document_types_id'), table_name='document_types')
    op.drop_table('document_types')
    
    op.drop_index(op.f('ix_users_microsoft_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop ENUM types
    priority_enum = postgresql.ENUM('low', 'medium', 'high', name='priority')
    priority_enum.drop(op.get_bind())
    
    document_status_enum = postgresql.ENUM('active', 'archived', 'deleted', name='documentstatus')
    document_status_enum.drop(op.get_bind())
    
    user_role_enum = postgresql.ENUM('admin', 'operator', 'viewer', name='userrole')
    user_role_enum.drop(op.get_bind())