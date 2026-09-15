ORDER_STATUS_LABELS = {
    "pending_payment": "Ожидает оплаты",
    "paid": "Оплачен",
    "payment_failed": "Оплата не прошла",
    "processing": "В обработке",
    "shipped": "Отправлен",
    "delivered": "Доставлен",
    "cancelled": "Отменён",
}


ORDER_STATUS_CLASSES = {
    "pending_payment": "order-status-pending",
    "paid": "order-status-paid",
    "payment_failed": "order-status-failed",
    "processing": "order-status-processing",
    "shipped": "order-status-shipped",
    "delivered": "order-status-delivered",
    "cancelled": "order-status-cancelled",
}


def order_status_label(status):
    return ORDER_STATUS_LABELS.get(
        status,
        status,
    )


def order_status_class(status):
    return ORDER_STATUS_CLASSES.get(
        status,
        "order-status-default",
    )