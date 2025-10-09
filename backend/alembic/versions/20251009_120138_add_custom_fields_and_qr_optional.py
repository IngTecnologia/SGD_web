"""add custom fields and qr optional tracking

Revision ID: 20251009_120138
Revises:
Create Date: 2025-10-09 12:01:38.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251009_120138'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add custom_fields column to document_types table
    op.add_column('document_types',
        sa.Column('custom_fields', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )

    # Add QR optional tracking columns to documents table
    op.add_column('documents',
        sa.Column('tiene_qr', sa.Boolean(), nullable=True, default=False)
    )
    op.add_column('documents',
        sa.Column('qr_extraction_success', sa.Boolean(), nullable=True, default=False)
    )

    # Set default values for existing rows
    op.execute("UPDATE document_types SET custom_fields = '[]' WHERE custom_fields IS NULL")
    op.execute("UPDATE documents SET tiene_qr = false WHERE tiene_qr IS NULL")
    op.execute("UPDATE documents SET qr_extraction_success = false WHERE qr_extraction_success IS NULL")

    # Make columns non-nullable after setting defaults
    op.alter_column('document_types', 'custom_fields', nullable=False)
    op.alter_column('documents', 'tiene_qr', nullable=False)
    op.alter_column('documents', 'qr_extraction_success', nullable=False)


def downgrade() -> None:
    # Remove columns added in upgrade
    op.drop_column('documents', 'qr_extraction_success')
    op.drop_column('documents', 'tiene_qr')
    op.drop_column('document_types', 'custom_fields')
