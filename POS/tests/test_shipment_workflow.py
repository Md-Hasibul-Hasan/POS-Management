"""
Tests for Shipment Workflow.

Covers:
- Shipment creation with tracking number
- Courier assignment
- Shipment status updates (with timestamp recording)
- Shipment delivered -> order completed integration
- Notification on shipment status change
- Tracking number auto-generation
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from POS.models import (
    Shipment, Order, OrderItem, Product, Category, Unit,
)
from POS.services import ShipmentService

User = get_user_model()


class ShipmentWorkflowTest(TestCase):
    """Test complete shipment lifecycle: create -> assign -> track -> deliver."""

    @classmethod
    def setUpTestData(cls):
        cls.employee = User.objects.create_user(
            name='Employee', email='emp@ship.test', password='testpass123',
        )
        cls.employee.role = 'salesman'
        cls.employee.is_active = True
        cls.employee.save()

        cls.customer = User.objects.create_user(
            name='Customer', email='cust@ship.test', password='testpass123',
        )
        cls.customer.role = 'customer'
        cls.customer.is_active = True
        cls.customer.save()

        cls.category = Category.objects.create(name='Ship Cat', slug='ship-cat')
        cls.unit = Unit.objects.create(name='Unit', short_name='u', unit_type='unit')

        cls.product = Product.objects.create(
            name='Ship Product', slug='ship-prod', sku='SHIP-PROD-001',
            category=cls.category, unit=cls.unit,
            base_price=Decimal("100.00"), selling_price=Decimal("100.00"),
            created_by=cls.employee,
        )

    def setUp(self):
        """Create a fresh order for each test."""
        self.order = Order.objects.create(
            order_number=f'ORD-SHIP-{timezone.now().timestamp():.0f}',
            user=self.customer,
            subtotal=Decimal("500.00"),
            total_amount=Decimal("500.00"),
            status='confirmed',
            payment_status='paid',
            created_by=self.employee,
        )

    # =========================================================================
    #  SHIPMENT CREATION
    # =========================================================================

    def test_create_shipment(self):
        shipment = ShipmentService.create_shipment(
            order=self.order,
            courier_name='Test Courier',
            created_by=self.employee,
            notes='Handle with care',
        )
        self.assertIsNotNone(shipment.tracking_number)
        self.assertEqual(shipment.courier_name, 'Test Courier')
        self.assertEqual(shipment.status, 'pending')
        self.assertEqual(shipment.notes, 'Handle with care')

    def test_create_shipment_auto_generates_tracking(self):
        shipment = ShipmentService.create_shipment(
            order=self.order,
            courier_name='Fast Ship',
            created_by=self.employee,
        )
        self.assertTrue(shipment.tracking_number.startswith('TRK-'))

    def test_create_shipment_with_custom_tracking(self):
        shipment = ShipmentService.create_shipment(
            order=self.order,
            courier_name='Manual',
            tracking_number='MANUAL-TRK-001',
            created_by=self.employee,
        )
        self.assertEqual(shipment.tracking_number, 'MANUAL-TRK-001')

    # =========================================================================
    #  COURIER ASSIGNMENT
    # =========================================================================

    def test_assign_courier(self):
        shipment = ShipmentService.create_shipment(
            order=self.order, courier_name='Initial',
            created_by=self.employee,
        )
        updated = ShipmentService.assign_courier(
            shipment=shipment,
            courier_name='Updated Courier',
            tracking_number='NEW-TRK-001',
        )
        self.assertEqual(updated.courier_name, 'Updated Courier')
        self.assertEqual(updated.tracking_number, 'NEW-TRK-001')

    # =========================================================================
    #  STATUS UPDATES
    # =========================================================================

    def test_update_status_pickup_requested(self):
        shipment = ShipmentService.create_shipment(
            order=self.order, courier_name='Test',
            created_by=self.employee,
        )
        updated = ShipmentService.update_shipment_status(
            shipment, 'pickup_requested',
        )
        self.assertEqual(updated.status, 'pickup_requested')
        self.assertIsNotNone(updated.pickup_requested_at)

    def test_update_status_in_transit(self):
        shipment = ShipmentService.create_shipment(
            order=self.order, courier_name='Test',
            created_by=self.employee,
        )
        ShipmentService.update_shipment_status(shipment, 'picked_up')
        updated = ShipmentService.update_shipment_status(shipment, 'in_transit')
        self.assertEqual(updated.status, 'in_transit')
        self.assertIsNotNone(updated.in_transit_at)

    def test_update_status_records_timestamp(self):
        """Each status update must record the corresponding timestamp."""
        status_field_map = {
            'pickup_requested': 'pickup_requested_at',
            'picked_up': 'picked_up_at',
            'in_transit': 'in_transit_at',
            'delivered': 'delivered_at',
            'failed': 'failed_at',
            'returned': 'returned_at',
        }
        shipment = ShipmentService.create_shipment(
            order=self.order, courier_name='Test',
            created_by=self.employee,
        )
        for status, field in status_field_map.items():
            updated = ShipmentService.update_shipment_status(shipment, status)
            ts = getattr(updated, field)
            self.assertIsNotNone(ts, f'{field} should be set for status {status}')

    def test_delivered_updates_order_status(self):
        self.order = Order.objects.create(
            order_number=f'ORD-SHIP-DEL-{timezone.now().timestamp():.0f}',
            user=self.customer,
            subtotal=Decimal("300.00"),
            total_amount=Decimal("300.00"),
            status='confirmed',
            fulfillment_status='shipped',
            created_by=self.employee,
        )
        shipment = ShipmentService.create_shipment(
            order=self.order, courier_name='Test',
            created_by=self.employee,
        )
        # Move through required statuses
        ShipmentService.update_shipment_status(shipment, 'pickup_requested')
        ShipmentService.update_shipment_status(shipment, 'picked_up')
        ShipmentService.update_shipment_status(shipment, 'in_transit')
        ShipmentService.update_shipment_status(shipment, 'delivered')

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'delivered')

    # =========================================================================
    #  UNIQUE TRACKING
    # =========================================================================

    def test_tracking_number_unique(self):
        shipment1 = ShipmentService.create_shipment(
            order=self.order, courier_name='A',
            created_by=self.employee,
        )
        order2 = Order.objects.create(
            order_number=f'ORD-SHIP-2-{timezone.now().timestamp():.0f}',
            user=self.customer,
            subtotal=Decimal("100.00"),
            total_amount=Decimal("100.00"),
            created_by=self.employee,
        )
        shipment2 = ShipmentService.create_shipment(
            order=order2, courier_name='B',
            created_by=self.employee,
        )
        self.assertNotEqual(
            shipment1.tracking_number, shipment2.tracking_number,
        )

    # =========================================================================
    #  EDGE CASES
    # =========================================================================

    def test_shipment_str_representation(self):
        shipment = ShipmentService.create_shipment(
            order=self.order, courier_name='Test',
            tracking_number='TRK-STR-TEST',
            created_by=self.employee,
        )
        self.assertIn('TRK-STR-TEST', str(shipment))
        self.assertIn('pending', str(shipment))