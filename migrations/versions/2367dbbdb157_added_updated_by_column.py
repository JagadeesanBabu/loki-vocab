from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# Revision identifiers, used by Alembic.
revision = '2367dbbdb157'
down_revision = 'e432a856cb40'
branch_labels = None
depends_on = None


def upgrade():
    # Get the current connection
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Check if the 'updated_by' column already exists
    columns = [col['name'] for col in inspector.get_columns('word_counts')]
    if 'updated_by' not in columns:
        with op.batch_alter_table('word_counts', schema=None) as batch_op:
            batch_op.add_column(sa.Column('updated_by', sa.String(length=150), nullable=True))

    # Check if the 'incorrect_count' column already exists
    if 'incorrect_count' not in columns:
        with op.batch_alter_table('word_counts', schema=None) as batch_op:
            batch_op.add_column(sa.Column('incorrect_count', sa.Integer, nullable=False, server_default='0'))

    # Update the `updated_by` column for all rows
    op.execute("UPDATE word_counts SET updated_by = 'loke'")

    # Rename the existing `word_counts` table
    op.rename_table('word_counts', 'word_counts_old')

    # Create the new `word_counts` table with `id` as the primary key
    op.create_table(
        'word_counts',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('word', sa.String(length=150), nullable=False),
        sa.Column('count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('incorrect_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('updated_by', sa.String(length=150), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint('word', 'updated_by', name='unique_word_user') 
    )

    # Copy data from the old table to the new table
    op.execute("""
        INSERT INTO word_counts (word, count, incorrect_count, updated_by, created_at, updated_at)
        SELECT word, count, 0, updated_by, created_at, updated_at FROM word_counts_old
    """)


    # Drop the old table
    op.drop_table('word_counts_old')


def downgrade():
    # Rename the current `word_counts` table to `word_counts_new`
    op.rename_table('word_counts', 'word_counts_new')

    # Recreate the original `word_counts` table
    op.create_table(
        'word_counts',
        sa.Column('word', sa.String(length=150), primary_key=True),
        sa.Column('count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('updated_by', sa.String(length=150), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Copy data back from the new table to the original schema
    op.execute("""
        INSERT INTO word_counts (word, count, updated_by, created_at, updated_at)
        SELECT word, count, updated_by, created_at, updated_at FROM word_counts_new
    """)

    # Drop the renamed table
    op.drop_table('word_counts_new')
