# =============================================================================
# SHIPMENT SERVICE
# =============================================================================
#
# Responsibilities:
# - Create shipments
# - Assign couriers
# - Track deliveries
# - Update shipment status
# - Mark orders delivered
#
# Dependencies:
# - Shipment model
# - Order model
# =============================================================================

from django.db import transaction
from django.utils import timezone
from ..models import Shipment, Order


class ShipmentService:
    """Manages shipment lifecycle — create, track, update."""

    @staticmethod
    @transaction.atomic
    def create_shipment(
        order: Order,
        courier_name: str,
        tracking_number: str = None,
        created_by=None,
        notes: str = "",
    ) -> Shipment:
        """
        Create a new shipment for an order.

        Args:
            order: Order to ship.
            courier_name: Name of the courier company.
            tracking_number: Tracking number (auto-generated if not provided).
            created_by: User creating the shipment.
            notes: Shipment notes.

        Returns:
            Shipment instance.
        """
        import uuid
        tracking_number = tracking_number or f"TRK-{uuid.uuid4().hex[:12].upper()}"

        shipment = Shipment.objects.create(
            order=order,
            tracking_number=tracking_number,
            courier_name=courier_name,
            status=Shipment.Status.PENDING,
            notes=notes,
            created_by=created_by,
        )

        return shipment

    @staticmethod
    @transaction.atomic
    def assign_courier(
        shipment: Shipment,
        courier_name: str,
        tracking_number: str = None,
    ) -> Shipment:
        """
        Assign or update courier for a shipment.

        Args:
            shipment: Shipment to update.
            courier_name: Courier company name.
            tracking_number: Updated tracking number.

        Returns:
            Updated Shipment instance.
        """
        shipment.courier_name = courier_name
        if tracking_number:
            shipment.tracking_number = tracking_number
        shipment.save(update_fields=['courier_name', 'tracking_number'])
        return shipment

    @staticmethod
    @transaction.atomic
    def update_shipment_status(
        shipment: Shipment,
        new_status: str,
    ) -> Shipment:
        """
        Update shipment status and record timestamp.

        Args:
            shipment: Shipment to update.
            new_status: Target status value.

        Returns:
            Updated Shipment instance.
        """
        now = timezone.now()

        status_timestamp_map = {
            Shipment.Status.PICKUP_REQUESTED: 'pickup_requested_at',
            Shipment.Status.PICKED_UP: 'picked_up_at',
            Shipment.Status.IN_TRANSIT: 'in_transit_at',
            Shipment.Status.DELIVERED: 'delivered_at',
            Shipment.Status.FAILED: 'failed_at',
            Shipment.Status.RETURNED: 'returned_at',
        }

        timestamp_field = status_timestamp_map.get(new_status)
        if timestamp_field:
            setattr(shipment, timestamp_field, now)

        shipment.status = new_status
        shipment.save()

        # Send notification on status change
        from .notification_service import NotificationService
        NotificationService.send_shipment_update(shipment)

        # If delivered, update the order
        if new_status == Shipment.Status.DELIVERED:
            from .order_service import OrderService
            OrderService.complete_order(
                order=shipment.order,
                changed_by=shipment.created_by,
            )

        return shipment
