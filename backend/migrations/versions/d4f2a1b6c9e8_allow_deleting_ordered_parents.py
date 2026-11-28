"""allow deleting customers and products referenced by orders

Revision ID: d4f2a1b6c9e8
Revises: bcfb116290b8
Create Date: 2026-11-28

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd4f2a1b6c9e8'
down_revision: str | Sequence[str] | None = 'bcfb116290b8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Snapshot order parents, then let their deletion NULL the references."""
    op.add_column('orders', sa.Column('customer_name', sa.String(length=255), nullable=True))
    op.add_column('orders', sa.Column('customer_email', sa.String(length=255), nullable=True))
    op.add_column('orders', sa.Column('customer_phone', sa.String(length=50), nullable=True))
    op.add_column('orders', sa.Column('customer_address', sa.Text(), nullable=True))
    op.add_column('order_items', sa.Column('product_name', sa.String(length=255), nullable=True))
    op.add_column('order_items', sa.Column('product_description', sa.Text(), nullable=True))
    op.add_column('order_items', sa.Column('product_price', sa.Numeric(12, 2), nullable=True))
    op.add_column('order_items', sa.Column('product_stock_quantity', sa.Integer(), nullable=True))

    # Existing orders all have live parents under the old RESTRICT constraints.
    op.execute(
        """
        UPDATE orders AS o
        SET customer_name = c.name,
            customer_email = c.email,
            customer_phone = c.phone,
            customer_address = c.address
        FROM customers AS c
        WHERE o.customer_id = c.id
        """
    )
    op.execute(
        """
        UPDATE order_items AS oi
        SET product_name = p.name,
            product_description = p.description,
            product_price = p.price,
            product_stock_quantity = p.stock_quantity
        FROM products AS p
        WHERE oi.product_id = p.id
        """
    )

    op.alter_column('orders', 'customer_name', nullable=False)
    op.alter_column('order_items', 'product_name', nullable=False)
    op.alter_column('order_items', 'product_price', nullable=False)
    op.alter_column('order_items', 'product_stock_quantity', nullable=False)

    op.drop_constraint('orders_customer_id_fkey', 'orders', type_='foreignkey')
    op.drop_constraint('order_items_product_id_fkey', 'order_items', type_='foreignkey')
    op.create_foreign_key(
        None, 'orders', 'customers', ['customer_id'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        None, 'order_items', 'products', ['product_id'], ['id'], ondelete='SET NULL'
    )
    op.alter_column('orders', 'customer_id', existing_type=sa.Integer(), nullable=True)
    op.alter_column('order_items', 'product_id', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    """Restore RESTRICT references. NULL parent ids stop the downgrade."""
    op.drop_constraint('orders_customer_id_fkey', 'orders', type_='foreignkey')
    op.drop_constraint('order_items_product_id_fkey', 'order_items', type_='foreignkey')
    op.alter_column('orders', 'customer_id', existing_type=sa.Integer(), nullable=False)
    op.alter_column('order_items', 'product_id', existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key(
        None, 'orders', 'customers', ['customer_id'], ['id'], ondelete='RESTRICT'
    )
    op.create_foreign_key(
        None, 'order_items', 'products', ['product_id'], ['id'], ondelete='RESTRICT'
    )

    op.drop_column('order_items', 'product_stock_quantity')
    op.drop_column('order_items', 'product_price')
    op.drop_column('order_items', 'product_description')
    op.drop_column('order_items', 'product_name')
    op.drop_column('orders', 'customer_address')
    op.drop_column('orders', 'customer_phone')
    op.drop_column('orders', 'customer_email')
    op.drop_column('orders', 'customer_name')
