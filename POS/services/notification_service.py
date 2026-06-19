# =============================================================================
# NOTIFICATION SERVICE
# =============================================================================
#
# Responsibilities:
# - Send email notifications via Django mail / Anymail
# - Create in-app Notification model records
# - Send order status updates
# - Send payment confirmations
# - Send low stock alerts
# - Send loyalty/coupon notifications
# - Send shipment tracking updates
# - Send POS shift/register alerts
#
# Dependencies:
# - Notification / NotificationTemplate models
# - django.core.mail (for email sending)
# =============================================================================

from django.db import transaction
from django.utils import timezone
from ..models.marketing import Notification, NotificationTemplate


class NotificationService:
    """Send notifications via email, SMS, or in-app."""

    @staticmethod
    @transaction.atomic
    def create_notification(
        user,
        notification_type: str,
        title: str,
        message: str,
        delivery_channel: str = 'in_app',
        template=None,
        created_by=None,
    ) -> Notification:
        """
        Create an in-app notification record.

        Args:
            user: Recipient user.
            notification_type: e.g., 'order_update', 'payment', 'stock_alert', 'promotion'.
            title: Notification title.
            message: Notification body.
            delivery_channel: 'in_app', 'email', 'sms', or 'all'.
            template: NotificationTemplate instance (optional).
            created_by: User who triggered this notification.

        Returns:
            Notification instance.
        """
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            delivery_channel=delivery_channel,
            delivery_status='sent' if delivery_channel == 'in_app' else 'pending',
        )

    @staticmethod
    def send_order_confirmation(order, user=None):
        """
        Send order confirmation notification.

        Args:
            order: Order that was confirmed.
            user: User to notify (defaults to order.user).
        """
        recipient = user or order.user
        if not recipient:
            return None

        return NotificationService.create_notification(
            user=recipient,
            notification_type='order_update',
            title=f'Order #{order.order_number} Confirmed',
            message=f'Your order of {order.total_amount} {order.currency} has been confirmed.',
            delivery_channel='in_app',
        )

    @staticmethod
    def send_payment_notification(payment, user=None):
        """
        Send payment confirmation notification.

        Args:
            payment: Payment that was captured.
            user: User to notify (defaults to payment.user).
        """
        recipient = user or payment.user
        if not recipient:
            return None

        return NotificationService.create_notification(
            user=recipient,
            notification_type='payment',
            title='Payment Received',
            message=f'Payment of {payment.amount} {payment.currency} via {payment.payment_method} was successful.',
            delivery_channel='in_app',
        )

    @staticmethod
    def send_shipment_update(shipment):
        """
        Send shipment status update to the order user.

        Args:
            shipment: Shipment that was updated.
        """
        user = shipment.order.user
        if not user:
            return None

        return NotificationService.create_notification(
            user=user,
            notification_type='shipment',
            title=f'Shipment #{shipment.tracking_number} Updated',
            message=f'Your shipment is now: {shipment.get_status_display()}.',
            delivery_channel='in_app',
        )

    @staticmethod
    def send_low_stock_alert(product, current_stock, threshold):
        """
        Send low stock alert to admin/manager users.

        Args:
            product: Product running low.
            current_stock: Current stock level.
            threshold: Low stock threshold.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        managers = User.objects.filter(
            role__in=('owner', 'manager', 'admin'),
            is_active=True,
        )

        notifications = []
        for manager in managers:
            n = NotificationService.create_notification(
                user=manager,
                notification_type='stock_alert',
                title=f'Low Stock: {product.name}',
                message=f'Stock is {current_stock} (threshold: {threshold}). Please reorder.',
                delivery_channel='in_app',
            )
            notifications.append(n)

        return notifications

    @staticmethod
    def send_email(
        subject: str,
        message: str,
        recipient_list: list,
        html_message: str = None,
    ):
        """
        Send an email notification.

        Args:
            subject: Email subject.
            message: Plain text body.
            recipient_list: List of recipient email addresses.
            html_message: HTML body (optional).
        """
        from django.core.mail import send_mail
        from django.conf import settings

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=True,
        )