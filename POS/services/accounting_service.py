# =============================================================================
# ACCOUNTING SERVICE
# =============================================================================
#
# Responsibilities:
# - Create accounting transactions
# - Record sales entries (POS + Online)
# - Record expense entries
# - Record tax entries
# - Generate financial reports
# - Maintain audit records
# - Record refunds
# - Record inventory adjustments
# - Generate profit/loss reports
# - Generate daily sales reports
#
# Dependencies:
# - AccountTransaction model
# - AccountCategory model
# - Order model
# - InventoryTransaction model
# =============================================================================

from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.utils import timezone
from ..models import AccountTransaction, AccountCategory, Order


class AccountingService:
    """Manages all financial/accounting entries."""

    # ─────────────────────────────────────────────────────────────────
    #  CREATE TRANSACTION (low-level)
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_transaction(
        category: AccountCategory,
        amount: Decimal,
        transaction_date=None,
        currency: str = "BDT",
        description: str = "",
        reference_type: str = "",
        reference_id: int = None,
        created_by=None,
    ) -> AccountTransaction:
        """
        Create a single accounting transaction entry.

        Args:
            category: AccountCategory (income/expense).
            amount: Transaction amount (must be positive).
            transaction_date: Date of the transaction.
            currency: Currency code (default BDT).
            description: Description of the transaction.
            reference_type: Type of reference (e.g., 'order', 'payment', 'refund').
            reference_id: ID of the referenced object.
            created_by: User who created this entry.

        Returns:
            AccountTransaction instance.

        Raises:
            ValueError: If amount is not positive.
        """
        if amount <= 0:
            raise ValueError("Transaction amount must be positive.")

        return AccountTransaction.objects.create(
            transaction_date=transaction_date or timezone.now().date(),
            category=category,
            amount=amount,
            currency=currency,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=created_by,
        )

    # ─────────────────────────────────────────────────────────────────
    #  RECORD SALE (POS + Online)
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def record_sale(
        order: Order,
        created_by=None,
    ) -> list:
        """
        Record accounting entries for a completed sale.

        Creates up to 3 entries:
        1. INCOME entry for subtotal (Sales Revenue)
        2. INCOME entry for tax (Sales Tax Collected)
        3. INCOME entry for shipping (Shipping Revenue)

        Idempotent: skips if entries already exist for this order.

        Args:
            order: The completed Order.
            created_by: User who processed the sale.

        Returns:
            List of AccountTransaction instances created.
        """
        transactions = []

        # Get or create income category for sales
        income_category, _ = AccountCategory.objects.get_or_create(
            name="Sales Revenue",
            defaults={
                'category_type': AccountCategory.CategoryType.INCOME,
                'is_system': True,
                'description': 'Revenue from sales (POS + Online)',
            }
        )

        # Idempotency check — skip if already recorded for this order
        if AccountTransaction.objects.filter(
            reference_type='order',
            reference_id=order.id,
            category=income_category,
        ).exists():
            return []  # Already recorded

        # Record the sale amount (subtotal)
        sale_tx = AccountingService.create_transaction(
            category=income_category,
            amount=order.subtotal,
            transaction_date=order.created_at.date(),
            currency=order.currency,
            description=f"Sale - {order.source.upper()} Order #{order.order_number}",
            reference_type='order',
            reference_id=order.id,
            created_by=created_by,
        )
        transactions.append(sale_tx)

        # Record tax if applicable
        if order.tax_amount > 0:
            tax_category, _ = AccountCategory.objects.get_or_create(
                name="Sales Tax Collected",
                defaults={
                    'category_type': AccountCategory.CategoryType.INCOME,
                    'is_system': True,
                    'description': 'Tax collected on sales',
                }
            )
            tax_tx = AccountingService.create_transaction(
                category=tax_category,
                amount=order.tax_amount,
                transaction_date=order.created_at.date(),
                currency=order.currency,
                description=f"Tax - {order.source.upper()} Order #{order.order_number}",
                reference_type='order',
                reference_id=order.id,
                created_by=created_by,
            )
            transactions.append(tax_tx)

        # Record shipping income if applicable
        if order.shipping_cost > 0:
            shipping_category, _ = AccountCategory.objects.get_or_create(
                name="Shipping Revenue",
                defaults={
                    'category_type': AccountCategory.CategoryType.INCOME,
                    'is_system': True,
                    'description': 'Revenue from shipping charges',
                }
            )
            shipping_tx = AccountingService.create_transaction(
                category=shipping_category,
                amount=order.shipping_cost,
                transaction_date=order.created_at.date(),
                currency=order.currency,
                description=f"Shipping - {order.source.upper()} Order #{order.order_number}",
                reference_type='order',
                reference_id=order.id,
                created_by=created_by,
            )
            transactions.append(shipping_tx)

        return transactions

    # ─────────────────────────────────────────────────────────────────
    #  RECORD EXPENSE
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def record_expense(
        amount: Decimal,
        description: str,
        category_name: str = "General Expense",
        transaction_date=None,
        currency: str = "BDT",
        reference_type: str = "",
        reference_id: int = None,
        created_by=None,
    ) -> AccountTransaction:
        """
        Record an expense entry.

        Args:
            amount: Expense amount.
            description: Description of the expense.
            category_name: Expense category name (created if not exists).
            transaction_date: Date of expense.
            currency: Currency code.
            reference_type: Type of reference.
            reference_id: ID of the referenced object.
            created_by: User who recorded the expense.

        Returns:
            AccountTransaction instance.
        """
        category, _ = AccountCategory.objects.get_or_create(
            name=category_name,
            defaults={
                'category_type': AccountCategory.CategoryType.EXPENSE,
                'is_system': False,
                'description': f'Expenses categorized as {category_name}',
            }
        )

        return AccountingService.create_transaction(
            category=category,
            amount=amount,
            transaction_date=transaction_date,
            currency=currency,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=created_by,
        )

    # ─────────────────────────────────────────────────────────────────
    #  RECORD REFUND
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def record_refund(
        order: Order,
        refund_amount: Decimal,
        refund_reason: str = "",
        created_by=None,
    ) -> AccountTransaction:
        """
        Record a refund/return accounting entry (negative income).

        Args:
            order: The original Order being refunded.
            refund_amount: Amount being refunded.
            refund_reason: Reason for the refund.
            created_by: User processing the refund.

        Returns:
            AccountTransaction instance.
        """
        # Use the same income category
        income_category, _ = AccountCategory.objects.get_or_create(
            name="Sales Revenue",
            defaults={
                'category_type': AccountCategory.CategoryType.INCOME,
                'is_system': True,
            }
        )

        return AccountingService.create_transaction(
            category=income_category,
            amount=refund_amount,
            transaction_date=timezone.now().date(),
            currency=order.currency,
            description=f"Refund - Order #{order.order_number}: {refund_reason}",
            reference_type='order',
            reference_id=order.id,
            created_by=created_by,
        )

    # ─────────────────────────────────────────────────────────────────
    #  RECORD INVENTORY ADJUSTMENT
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def record_inventory_adjustment(
        amount: Decimal,
        description: str,
        reference_type: str = "inventory_adjustment",
        reference_id: int = None,
        created_by=None,
    ) -> AccountTransaction:
        """
        Record an inventory adjustment (damage, loss) as an expense.

        Args:
            amount: Cost value of the adjustment.
            description: Description of the adjustment.
            reference_type: Type of reference.
            reference_id: ID of the referenced object.
            created_by: User recording the adjustment.

        Returns:
            AccountTransaction instance.
        """
        category, _ = AccountCategory.objects.get_or_create(
            name="Inventory Adjustments",
            defaults={
                'category_type': AccountCategory.CategoryType.EXPENSE,
                'is_system': True,
                'description': 'Cost of inventory adjustments (damage, loss, etc.)',
            }
        )

        return AccountingService.create_transaction(
            category=category,
            amount=amount,
            transaction_date=timezone.now().date(),
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=created_by,
        )

    # ─────────────────────────────────────────────────────────────────
    #  DAILY SALES REPORT
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_daily_sales_report(date=None):
        """
        Generate a daily sales summary report.

        Args:
            date: Date to report on (defaults to today).

        Returns:
            dict with keys: total_sales, total_tax, total_shipping,
                            order_count, average_order_value.
        """
        from django.db.models import Sum, Count, Avg
        from ..models import Order

        report_date = date or timezone.now().date()

        orders = Order.objects.filter(
            created_at__date=report_date,
            status__in=['delivered', 'completed', 'confirmed'],
            payment_status='paid',
        )

        aggregation = orders.aggregate(
            total_sales=Sum('total_amount'),
            total_tax=Sum('tax_amount'),
            total_shipping=Sum('shipping_cost'),
            order_count=Count('id'),
            avg_order_value=Avg('total_amount'),
        )

        return {
            'date': report_date,
            'total_sales': aggregation['total_sales'] or Decimal("0"),
            'total_tax': aggregation['total_tax'] or Decimal("0"),
            'total_shipping': aggregation['total_shipping'] or Decimal("0"),
            'order_count': aggregation['order_count'] or 0,
            'average_order_value': aggregation['avg_order_value'] or Decimal("0"),
        }

    @staticmethod
    def get_pos_sales_report(shift=None, terminal=None, date=None):
        """
        Generate POS-specific sales summary.

        Args:
            shift: POSShift to report on.
            terminal: POSTerminal to report on.
            date: Date to report on.

        Returns:
            dict with sales summary filtered by the given criteria.
        """
        from django.db.models import Sum, Count
        from ..models import Order

        filters = {'source__in': ['pos']}
        if shift:
            filters['shift'] = shift
        if terminal:
            filters['terminal'] = terminal
        if date:
            filters['created_at__date'] = date

        orders = Order.objects.filter(**filters, payment_status='paid')

        aggregation = orders.aggregate(
            total_sales=Sum('total_amount'),
            order_count=Count('id'),
            total_items=Sum('items__quantity'),
        )

        return {
            'total_sales': aggregation['total_sales'] or Decimal("0"),
            'order_count': aggregation['order_count'] or 0,
            'total_items': aggregation['total_items'] or 0,
            'shift': shift.id if shift else None,
            'terminal': terminal.id if terminal else None,
            'date': date,
        }