from app.services.analytics import get_analytics_summary
from app.services.auth import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    register_user,
)
from app.services.customer import (
    CustomerNotFoundError,
    create_customer,
    delete_customer,
    get_owned_customer,
    list_customers,
    update_customer,
)
from app.services.order import (
    InsufficientStockError,
    OrderCustomerNotFoundError,
    OrderNotFoundError,
    OrderProductNotFoundError,
    create_order,
    get_owned_order,
    list_orders,
    update_order_status,
)
from app.services.product import (
    ProductNotFoundError,
    create_product,
    delete_product,
    get_owned_product,
    list_products,
    update_product,
)

__all__ = [
    "CustomerNotFoundError",
    "EmailAlreadyRegisteredError",
    "InsufficientStockError",
    "OrderCustomerNotFoundError",
    "OrderNotFoundError",
    "OrderProductNotFoundError",
    "ProductNotFoundError",
    "authenticate_user",
    "create_customer",
    "create_order",
    "create_product",
    "delete_customer",
    "delete_product",
    "get_analytics_summary",
    "get_owned_customer",
    "get_owned_order",
    "get_owned_product",
    "list_customers",
    "list_orders",
    "list_products",
    "register_user",
    "update_customer",
    "update_order_status",
    "update_product",
]
