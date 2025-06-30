"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def index_exists(index_name: str, table_name: str) -> bool:
    """Check if an index exists on a table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def safe_create_table(table_name: str, *args, **kwargs):
    """Create table only if it doesn't exist."""
    if not table_exists(table_name):
        return op.create_table(table_name, *args, **kwargs)
    else:
        print(f"Table '{table_name}' already exists, skipping creation.")


def safe_drop_table(table_name: str):
    """Drop table only if it exists."""
    if table_exists(table_name):
        return op.drop_table(table_name)
    else:
        print(f"Table '{table_name}' does not exist, skipping drop.")


def safe_create_index(index_name: str, table_name: str, *args, **kwargs):
    """Create index only if it doesn't exist."""
    if not index_exists(index_name, table_name):
        return op.create_index(index_name, table_name, *args, **kwargs)
    else:
        print(f"Index '{index_name}' already exists on table '{table_name}', skipping creation.")


def safe_drop_index(index_name: str, table_name: str):
    """Drop index only if it exists."""
    if index_exists(index_name, table_name):
        return op.drop_index(index_name, table_name=table_name)
    else:
        print(f"Index '{index_name}' does not exist on table '{table_name}', skipping drop.")


def upgrade() -> None:
    """Upgrade schema."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade schema."""
    ${downgrades if downgrades else "pass"}
