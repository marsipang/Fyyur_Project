"""empty message

Revision ID: b58316b1b0a2
Revises: 644c532f7890
Create Date: 2020-03-01 23:34:54.939336

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b58316b1b0a2'
down_revision = '644c532f7890'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'Genre', ['name'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'Genre', type_='unique')
    # ### end Alembic commands ###
