"""
Tests for Coupon Workflow.

Covers:
- Coupon creation with discount types
- Coupon validation (expiry, usage limits)
- Coupon application to orders
- Coupon usage tracking
- Coupon service validate/apply/record flow
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from POS.models.marketing import Coupon, CouponUsage
from POS.models import Order
from POS.services import CouponService

User = get_user_model()


class CouponWorkflowTest(TestCase):
    """Test coupon lifecycle: create → validate → apply → track usage."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            name='Customer', email='cust@cpn.test', password='testpass123',
        )
        cls.user.role = 'customer'
        cls.user.is_active = True
        cls.user.save()

        cls.employee = User.objects.create_user(
            name='Employee', email='emp@cpn.test', password='testpass123',
        )
        cls.employee.role = 'manager'
        cls.employee.is_active = True
        cls.employee.save()

        cls.order = Order.objects.create(
            order_number='ORD-CPN-001', user=cls.user,
            subtotal=Decimal("1000.00"), total_amount=Decimal("1000.00"),
            created_by=cls.employee,
        )

    def test_create_percentage_coupon(self):
        coupon = Coupon.objects.create(
            code='PERCENT10',
            title='10% Off',
            discount_type='percentage',
            discount_value=Decimal("10.00"),
            is_active=True,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        self.assertTrue(coupon.is_active)
        self.assertFalse(coupon.is_expired)

    def test_create_fixed_coupon(self):
        coupon = Coupon.objects.create(
            code='FLAT500',
            title='500 Off',
            discount_type='fixed',
            discount_value=Decimal("500.00"),
            max_discount_amount=Decimal("500.00"),
            is_active=True,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        self.assertEqual(coupon.discount_type, 'fixed')
        self.assertEqual(coupon.discount_value, Decimal("500.00"))

    def test_validate_valid_coupon(self):
        coupon = Coupon.objects.create(
            code='VALID10',
            title='10 Off',
            discount_type='fixed',
            discount_value=Decimal("10.00"),
            is_active=True,
            usage_limit=100,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        result = CouponService.validate_coupon(coupon, user=self.user)
        self.assertTrue(result['valid'])
        self.assertIsNone(result['reason'])

    def test_validate_expired_coupon(self):
        coupon = Coupon.objects.create(
            code='EXPIRED',
            title='Expired',
            discount_type='fixed',
            discount_value=Decimal("10.00"),
            is_active=True,
            start_date=timezone.now() - timezone.timedelta(days=60),
            end_date=timezone.now() - timezone.timedelta(days=1),
        )
        result = CouponService.validate_coupon(coupon)
        self.assertFalse(result['valid'])
        self.assertIsNotNone(result['reason'])

    def test_validate_inactive_coupon(self):
        coupon = Coupon.objects.create(
            code='INACTIVE',
            title='Inactive',
            discount_type='fixed',
            discount_value=Decimal("10.00"),
            is_active=False,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        result = CouponService.validate_coupon(coupon)
        self.assertFalse(result['valid'])
        self.assertIn('not active', result['reason'].lower())

    def test_validate_usage_limit_reached(self):
        coupon = Coupon.objects.create(
            code='LIMITED',
            title='Limited Use',
            discount_type='fixed',
            discount_value=Decimal("10.00"),
            is_active=True,
            usage_limit=1,
            current_usage=1,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        result = CouponService.validate_coupon(coupon)
        self.assertFalse(result['valid'])

    def test_validate_minimum_order_amount(self):
        coupon = Coupon.objects.create(
            code='MINORDER',
            title='Min 500',
            discount_type='fixed',
            discount_value=Decimal("50.00"),
            min_order_amount=Decimal("500.00"),
            is_active=True,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        # Subtotal below minimum
        result = CouponService.validate_coupon(
            coupon, order_subtotal=Decimal("100.00"),
        )
        self.assertFalse(result['valid'])

        # Subtotal meets minimum
        result = CouponService.validate_coupon(
            coupon, order_subtotal=Decimal("500.00"),
        )
        self.assertTrue(result['valid'])

    def test_apply_percentage_coupon(self):
        coupon = Coupon.objects.create(
            code='PCT20',
            title='20% Off',
            discount_type='percentage',
            discount_value=Decimal("20.00"),
            is_active=True,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        result = CouponService.apply_coupon(
            coupon=coupon, order_subtotal=Decimal("1000.00"),
        )
        self.assertTrue(result['valid'])
        self.assertEqual(result['coupon_discount'], Decimal("200.00"))
        self.assertEqual(result['final_price'], Decimal("800.00"))

    def test_apply_fixed_coupon(self):
        coupon = Coupon.objects.create(
            code='FIX300',
            title='300 Off',
            discount_type='fixed',
            discount_value=Decimal("300.00"),
            is_active=True,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        result = CouponService.apply_coupon(
            coupon=coupon, order_subtotal=Decimal("1000.00"),
        )
        self.assertEqual(result['coupon_discount'], Decimal("300.00"))
        self.assertEqual(result['final_price'], Decimal("700.00"))

    def test_record_coupon_usage(self):
        coupon = Coupon.objects.create(
            code='TRACKME',
            title='Track Usage',
            discount_type='fixed',
            discount_value=Decimal("50.00"),
            is_active=True,
            current_usage=0,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        usage = CouponService.record_coupon_usage(
            coupon=coupon, user=self.user,
            order=self.order, discount_applied=Decimal("50.00"),
        )
        self.assertEqual(usage.discount_applied, Decimal("50.00"))
        coupon.refresh_from_db()
        self.assertEqual(coupon.current_usage, 1)

    def test_get_applicable_coupons(self):
        Coupon.objects.create(
            code='APP01', title='Applicable 1',
            discount_type='fixed', discount_value=Decimal("10.00"),
            is_active=True,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        Coupon.objects.create(
            code='APP02', title='Applicable 2',
            discount_type='percentage', discount_value=Decimal("5.00"),
            is_active=True,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        # Expired coupon
        Coupon.objects.create(
            code='EXP', title='Expired',
            discount_type='fixed', discount_value=Decimal("10.00"),
            is_active=True,
            start_date=timezone.now() - timezone.timedelta(days=60),
            end_date=timezone.now() - timezone.timedelta(days=1),
        )
        applicable = CouponService.get_applicable_coupons()
        self.assertEqual(len(applicable), 2)