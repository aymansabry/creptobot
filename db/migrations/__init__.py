from alembic import op
import sqlalchemy as sa

def create_tables():
    op.create_table(
        'trades',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('user_id', sa.String),
        sa.Column('pair', sa.String),
        sa.Column('amount', sa.Float),
        sa.Column('profit', sa.Float),
        sa.Column('timestamp', sa.DateTime)
    )
