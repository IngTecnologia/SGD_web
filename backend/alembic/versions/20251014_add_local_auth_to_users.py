"""add local auth to users

Revision ID: 20251014_local_auth
Revises: 20251009_120138_add_custom_fields_and_qr_optional
Create Date: 2025-10-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251014_local_auth'
down_revision = '20251009_120138'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar campos para autenticación local
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('is_local_user', sa.Boolean(), nullable=True, server_default='false'))

    # Modificar azure_id para permitir NULL (usuarios locales no tienen Azure ID)
    op.alter_column('users', 'azure_id',
                    existing_type=sa.String(length=255),
                    nullable=True)


def downgrade():
    # Revertir cambios
    op.alter_column('users', 'azure_id',
                    existing_type=sa.String(length=255),
                    nullable=False)

    op.drop_column('users', 'is_local_user')
    op.drop_column('users', 'password_hash')
