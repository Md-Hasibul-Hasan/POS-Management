# =============================================================================
#  POS Models Package — 11  modules
# =============================================================================

from .common import SoftDeleteManager, AllObjectsManager, BaseModel
from .catalog import Category, Brand, Unit, Tag, Attribute, AttributeValue, VariantAttribute, generate_attribute_signature, ProductImage, ProductVideo, ReviewImage, ProductFAQ, ProductReview
from .product import Product, ProductVariant
from .customer import CustomerProfile, CustomerGroup, CustomerLedger, Address, WalletTransaction, LoyaltyPoints, LoyaltyTransaction, Wishlist, CompareList
from .order import Order, OrderItem, OrderStatusLog, OrderCoupon, Cart, CartItem, ReturnRecord, ReturnItem, ReturnInspection, ExchangeRequest, Shipment
from .payment import PaymentGateway, PaymentMethod, PaymentSession, Payment, RefundTransaction, PaymentEventLog
from .marketing import Campaign, Coupon, CouponGroup, CouponCategory, CouponUsage, Banner, StoreSettings, NotificationTemplate, Notification
from .inventory import Supplier, SupplierLedger, Purchase, PurchaseItem, PurchasePayment, InventoryBatch, InventoryTransaction, StockReservation, DamageReport, LostInventory, StockAdjustment, SupplierReturn, StockAudit
from .pos_operations import POSTerminal, POSShift, CashRegister, CashMovement
from .geo import Country, Division, District, Area, CourierProvider, ShippingZone, ShippingRate
from .accounting import AccountCategory, AccountTransaction, TaxConfiguration, FraudRule, IPBlacklist, AuditLog
