"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-04-17 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create admins table
    op.create_table(
        'admins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('ix_admins_email', 'admins', ['email'], unique=False)
    op.create_index('ix_admins_id', 'admins', ['id'], unique=False)
    op.create_index('ix_admins_username', 'admins', ['username'], unique=False)

    # Create admin_invite_codes table
    op.create_table(
        'admin_invite_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('used_by', sa.Integer(), nullable=True),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_used', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['admins.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_admin_invite_codes_code', 'admin_invite_codes', ['code'], unique=False)
    op.create_index('ix_admin_invite_codes_id', 'admin_invite_codes', ['id'], unique=False)

    # Create app_settings table
    op.create_table(
        'app_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(length=20), nullable=True),
        sa.Column('fullscreen', sa.Boolean(), nullable=True),
        sa.Column('camera_resolution', sa.String(length=20), nullable=True),
        sa.Column('camera_fps', sa.Integer(), nullable=True),
        sa.Column('sound_notifications', sa.Boolean(), nullable=True),
        sa.Column('access_notifications', sa.Boolean(), nullable=True),
        sa.Column('match_threshold', sa.Float(), nullable=True),
        sa.Column('two_factor_enabled', sa.Boolean(), nullable=True),
        sa.Column('auto_backup', sa.Boolean(), nullable=True),
        sa.Column('backend_url', sa.String(length=255), nullable=True),
        sa.Column('connection_timeout', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_app_settings_id', 'app_settings', ['id'], unique=False)

    # Create employees table
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.String(length=50), nullable=True),
        sa.Column('username', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('position', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('hire_date', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('access_enabled', sa.Boolean(), nullable=False),
        sa.Column('photo_path', sa.String(length=255), nullable=True),
        sa.Column('embedding', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_employees_employee_id', 'employees', ['employee_id'], unique=False)
    op.create_index('ix_employees_id', 'employees', ['id'], unique=False)
    op.create_index('ix_employees_username', 'employees', ['username'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_employees_username', table_name='employees')
    op.drop_index('ix_employees_id', table_name='employees')
    op.drop_index('ix_employees_employee_id', table_name='employees')
    op.drop_table('employees')
    
    op.drop_index('ix_app_settings_id', table_name='app_settings')
    op.drop_table('app_settings')
    
    op.drop_index('ix_admin_invite_codes_id', table_name='admin_invite_codes')
    op.drop_index('ix_admin_invite_codes_code', table_name='admin_invite_codes')
    op.drop_table('admin_invite_codes')
    
    op.drop_index('ix_admins_username', table_name='admins')
    op.drop_index('ix_admins_id', table_name='admins')
    op.drop_index('ix_admins_email', table_name='admins')
    op.drop_table('admins')
