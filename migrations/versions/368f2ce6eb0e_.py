"""empty message

Revision ID: 368f2ce6eb0e
Revises: 782fa2a525ac
Create Date: 2019-06-11 02:27:45.153456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '368f2ce6eb0e'
down_revision = '782fa2a525ac'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('uploaded_content', schema=None) as batch_op:
        batch_op.add_column(sa.Column('coordinates', sa.String(length=500), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('uploaded_content', schema=None) as batch_op:
        batch_op.drop_column('coordinates')

    # ### end Alembic commands ###
