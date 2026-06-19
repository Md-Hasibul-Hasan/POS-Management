"""
Tests for Loyalty Workflow.

Covers:
- LoyaltyPoints initialization for new customers
- Earning points from orders
- Redeeming points (success + insufficient balance)
- Points balance tracking
- Points expiry
- Loyalty transaction history
- CustomerProfile cache sync
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from POS.models import (
    LoyaltyPoints, LoyaltyTransaction, CustomerProfile,
    Order,
)
from POS.services import LoyaltyService

User = get_user_model()


class LoyaltyWorkflowTest(TestCase):
    """Test complete loyalty lifecycle: earn -> redeem -> expire."""

    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(
            name='Customer', email='cust@loy.test', password='testpass123',
        )
        cls.customer.role = 'customer'
        cls.customer.is_active = True
        cls.customer.save()

        # Initialize customer profile with loyalty
        cls.profile = CustomerProfile.objects.create(
            user=cls.customer, customer_id='CUST-LOY-001',
        )
        LoyaltyPoints.objects.create(user=cls.customer, balance=0)

    # =========================================================================
    #  INITIALIZATION
    # =========================================================================

    def test_loyalty_points_initialized_to_zero(self):
        lp = LoyaltyPoints.objects.get(user=self.customer)
        self.assertEqual(lp.balance, 0)
        self.assertEqual(lp.lifetime_earned, 0)
        self.assertEqual(lp.lifetime_redeemed, 0)

    def test_get_balance_returns_zero_for_new_user(self):
        new_user = User.objects.create_user(
            name='New', email='new@loy.test', password='testpass123',
        )
        balance = LoyaltyService.get_balance(new_user)
        self.assertEqual(balance, 0)

    # =========================================================================
    #  EARNING POINTS
    # =========================================================================

    def test_earn_points_from_order(self):
        lt = LoyaltyService.earn_points(
            user=self.customer,
            order_total=Decimal("1000.00"),
            reference='ORD-LOY-001',
            notes='Points from purchase',
        )
        self.assertEqual(lt.transaction_type, 'earned')
        self.assertGreater(lt.points, 0)

        # Verify balance
        lp = LoyaltyPoints.objects.get(user=self.customer)
        self.assertEqual(lp.balance, lt.points)
        self.assertEqual(lp.lifetime_earned, lt.points)

    def test_earn_points_minimum_one(self):
        lt = LoyaltyService.earn_points(
            user=self.customer,
            order_total=Decimal("1.00"),
            reference='ORD-MIN',
        )
        # Minimum 1 point per purchase
        self.assertGreaterEqual(lt.points, 1)

    def test_earn_points_syncs_customer_profile(self):
        LoyaltyService.earn_points(
            user=self.customer,
            order_total=Decimal("500.00"),
            reference='ORD-LOY-002',
        )
        self.profile.refresh_from_db()
        self.assertGreater(self.profile.loyalty_points, 0)

    def test_multiple_earn_accumulates_points(self):
        LoyaltyService.earn_points(
            user=self.customer, order_total=Decimal("1000.00"),
            reference='ORD-001',
        )
        first_balance = LoyaltyService.get_balance(self.customer)

        LoyaltyService.earn_points(
            user=self.customer, order_total=Decimal("2000.00"),
            reference='ORD-002',
        )
        second_balance = LoyaltyService.get_balance(self.customer)

        self.assertGreater(second_balance, first_balance)

    # =========================================================================
    #  REDEEMING POINTS
    # =========================================================================

    def test_redeem_points(self):
        # First earn some points
        LoyaltyService.earn_points(
            user=self.customer, order_total=Decimal("10000.00"),
            reference='ORD-EARN',
        )
        balance_before = LoyaltyService.get_balance(self.customer)
        self.assertGreater(balance_before, 0)

        # Redeem
        lt = LoyaltyService.redeem_points(
            user=self.customer, points=10,
            reference='ORD-DISC',
            notes='Redeemed for discount',
        )
        self.assertEqual(lt.transaction_type, 'redeemed')
        self.assertEqual(lt.points, 10)

        balance_after = LoyaltyService.get_balance(self.customer)
        self.assertEqual(balance_after, balance_before - 10)

    def test_redeem_insufficient_points_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            LoyaltyService.redeem_points(
                user=self.customer, points=999999,
                reference='ORD-FAIL',
            )
        self.assertIn('Insufficient', str(ctx.exception))

    def test_redeem_points_updates_lifetime_redeemed(self):
        LoyaltyService.earn_points(
            user=self.customer, order_total=Decimal("10000.00"),
            reference='ORD-EARN-2',
        )
        lp_before = LoyaltyPoints.objects.get(user=self.customer)

        LoyaltyService.redeem_points(
            user=self.customer, points=5, reference='ORD-RED',
        )
        lp_after = LoyaltyPoints.objects.get(user=self.customer)
        self.assertEqual(lp_after.lifetime_redeemed, lp_before.lifetime_redeemed + 5)

    def test_redeem_points_syncs_customer_profile(self):
        LoyaltyService.earn_points(
            user=self.customer, order_total=Decimal("5000.00"),
            reference='ORD-EARN-3',
        )
        profile_before = CustomerProfile.objects.get(user=self.customer)

        LoyaltyService.redeem_points(
            user=self.customer, points=3, reference='ORD-RED-2',
        )
        self.profile.refresh_from_db()
        self.assertLess(self.profile.loyalty_points, profile_before.loyalty_points)

    # =========================================================================
    #  POINTS VALUE
    # =========================================================================

    def test_get_points_value(self):
        value = LoyaltyService.get_points_value(100)
        self.assertEqual(value, Decimal("100"))

    # =========================================================================
    #  TRANSACTION HISTORY
    # =========================================================================

    def test_earn_creates_transaction_record(self):
        old_count = LoyaltyTransaction.objects.filter(user=self.customer).count()
        LoyaltyService.earn_points(
            user=self.customer, order_total=Decimal("1000.00"),
            reference='ORD-HIST',
        )
        new_count = LoyaltyTransaction.objects.filter(user=self.customer).count()
        self.assertEqual(new_count, old_count + 1)

    def test_redeem_creates_transaction_record(self):
        LoyaltyService.earn_points(
            user=self.customer, order_total=Decimal("10000.00"),
            reference='ORD-HIST-2',
        )
        old_count = LoyaltyTransaction.objects.filter(user=self.customer).count()

        LoyaltyService.redeem_points(
            user=self.customer, points=5, reference='ORD-HIST-3',
        )
        new_count = LoyaltyTransaction.objects.filter(user=self.customer).count()
        self.assertEqual(new_count, old_count + 1)

    # =========================================================================
    #  POINTS EXPIRY
    # =========================================================================

    def test_expire_old_points(self):
        # Create an expired earned transaction
        LoyaltyTransaction.objects.create(
            user=self.customer,
            transaction_type='earned',
            points=50,
            balance_before=0,
            balance_after=50,
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )
        lp = LoyaltyPoints.objects.get(user=self.customer)
        lp.balance = 50
        lp.lifetime_earned = 50
        lp.save()

        expired = LoyaltyService.expire_old_points(self.customer)
        self.assertEqual(expired, 50)

        lp.refresh_from_db()
        self.assertEqual(lp.balance, 0)