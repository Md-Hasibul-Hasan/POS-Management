from django.urls import path
from . import views

urlpatterns = [
    # =========================================================================
    #  CATALOG
    # =========================================================================
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('brands/', views.BrandListCreateView.as_view(), name='brand-list'),
    path('brands/<int:pk>/', views.BrandDetailView.as_view(), name='brand-detail'),
    path('units/', views.UnitListCreateView.as_view(), name='unit-list'),
    path('units/<int:pk>/', views.UnitDetailView.as_view(), name='unit-detail'),
    path('tags/', views.TagListCreateView.as_view(), name='tag-list'),
    path('tags/<int:pk>/', views.TagDetailView.as_view(), name='tag-detail'),
    path('attributes/', views.AttributeListCreateView.as_view(), name='attribute-list'),
    path('attributes/<int:pk>/', views.AttributeDetailView.as_view(), name='attribute-detail'),
    path('attribute-values/', views.AttributeValueListCreateView.as_view(), name='attribute-value-list'),
    path('attribute-values/<int:pk>/', views.AttributeValueDetailView.as_view(), name='attribute-value-detail'),
    path('faqs/', views.ProductFAQListCreateView.as_view(), name='faq-list'),
    path('faqs/<int:pk>/', views.ProductFAQDetailView.as_view(), name='faq-detail'),
    path('reviews/', views.ProductReviewListCreateView.as_view(), name='review-list'),
    path('reviews/<int:pk>/', views.ProductReviewDetailView.as_view(), name='review-detail'),

    # =========================================================================
    #  PRODUCTS
    # =========================================================================
    path('products/', views.ProductListCreateView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('variants/', views.ProductVariantListCreateView.as_view(), name='variant-list'),
    path('variants/<int:pk>/', views.ProductVariantDetailView.as_view(), name='variant-detail'),
    path('product-images/', views.ProductImageListCreateView.as_view(), name='product-image-list'),
    path('product-images/<int:pk>/', views.ProductImageDetailView.as_view(), name='product-image-detail'),
    path('product-videos/', views.ProductVideoListCreateView.as_view(), name='product-video-list'),
    path('product-videos/<int:pk>/', views.ProductVideoDetailView.as_view(), name='product-video-detail'),

    # =========================================================================
    #  CUSTOMERS
    # =========================================================================
    path('customer-profiles/', views.CustomerProfileListCreateView.as_view(), name='customer-profile-list'),
    path('customer-profiles/<int:pk>/', views.CustomerProfileDetailView.as_view(), name='customer-profile-detail'),
    path('customer-groups/', views.CustomerGroupListCreateView.as_view(), name='customer-group-list'),
    path('customer-groups/<int:pk>/', views.CustomerGroupDetailView.as_view(), name='customer-group-detail'),
    path('customer-ledger/', views.CustomerLedgerListCreateView.as_view(), name='customer-ledger-list'),
    path('addresses/', views.AddressListCreateView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    path('wallet-transactions/', views.WalletTransactionListCreateView.as_view(), name='wallet-transaction-list'),
    path('loyalty-points/<int:pk>/', views.LoyaltyPointsDetailView.as_view(), name='loyalty-points-detail'),
    path('loyalty-transactions/', views.LoyaltyTransactionListCreateView.as_view(), name='loyalty-transaction-list'),
    path('wishlist/', views.WishlistListCreateView.as_view(), name='wishlist-list'),
    path('wishlist/<int:pk>/', views.WishlistDetailView.as_view(), name='wishlist-detail'),
    path('compare-list/', views.CompareListListCreateView.as_view(), name='compare-list-list'),
    path('compare-list/<int:pk>/', views.CompareListDetailView.as_view(), name='compare-list-detail'),

    # =========================================================================
    #  ORDERS
    # =========================================================================
    path('orders/', views.OrderListCreateView.as_view(), name='order-list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('order-items/', views.OrderItemListCreateView.as_view(), name='order-item-list'),
    path('carts/', views.CartListCreateView.as_view(), name='cart-list'),
    path('carts/<int:pk>/', views.CartDetailView.as_view(), name='cart-detail'),
    path('cart-items/', views.CartItemListCreateView.as_view(), name='cart-item-list'),
    path('cart-items/<int:pk>/', views.CartItemDetailView.as_view(), name='cart-item-detail'),
    path('returns/', views.ReturnRecordListCreateView.as_view(), name='return-list'),
    path('returns/<int:pk>/', views.ReturnRecordDetailView.as_view(), name='return-detail'),
    path('exchanges/', views.ExchangeRequestListCreateView.as_view(), name='exchange-list'),
    path('exchanges/<int:pk>/', views.ExchangeRequestDetailView.as_view(), name='exchange-detail'),
    path('shipments/', views.ShipmentListCreateView.as_view(), name='shipment-list'),
    path('shipments/<int:pk>/', views.ShipmentDetailView.as_view(), name='shipment-detail'),

    # =========================================================================
    #  PAYMENTS
    # =========================================================================
    path('payment-gateways/', views.PaymentGatewayListCreateView.as_view(), name='payment-gateway-list'),
    path('payment-gateways/<int:pk>/', views.PaymentGatewayDetailView.as_view(), name='payment-gateway-detail'),
    path('payment-methods/', views.PaymentMethodListCreateView.as_view(), name='payment-method-list'),
    path('payment-methods/<int:pk>/', views.PaymentMethodDetailView.as_view(), name='payment-method-detail'),
    path('payment-sessions/', views.PaymentSessionListCreateView.as_view(), name='payment-session-list'),
    path('payment-sessions/<int:pk>/', views.PaymentSessionDetailView.as_view(), name='payment-session-detail'),
    path('payments/', views.PaymentListCreateView.as_view(), name='payment-list'),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('refunds/', views.RefundTransactionListCreateView.as_view(), name='refund-list'),
    path('payment-event-logs/', views.PaymentEventLogListCreateView.as_view(), name='payment-event-log-list'),

    # =========================================================================
    #  MARKETING
    # =========================================================================
    path('campaigns/', views.CampaignListCreateView.as_view(), name='campaign-list'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(), name='campaign-detail'),
    path('coupons/', views.CouponListCreateView.as_view(), name='coupon-list'),
    path('coupons/<int:pk>/', views.CouponDetailView.as_view(), name='coupon-detail'),
    path('coupon-usages/', views.CouponUsageListCreateView.as_view(), name='coupon-usage-list'),
    path('banners/', views.BannerListCreateView.as_view(), name='banner-list'),
    path('banners/<int:pk>/', views.BannerDetailView.as_view(), name='banner-detail'),
    path('store-settings/', views.StoreSettingsListCreateView.as_view(), name='store-settings-list'),
    path('store-settings/<int:pk>/', views.StoreSettingsDetailView.as_view(), name='store-settings-detail'),
    path('notifications/', views.NotificationListCreateView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('notification-templates/', views.NotificationTemplateListCreateView.as_view(), name='notification-template-list'),
    path('notification-templates/<int:pk>/', views.NotificationTemplateDetailView.as_view(), name='notification-template-detail'),

    # =========================================================================
    #  INVENTORY
    # =========================================================================
    path('suppliers/', views.SupplierListCreateView.as_view(), name='supplier-list'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier-detail'),
    path('supplier-ledger/', views.SupplierLedgerListCreateView.as_view(), name='supplier-ledger-list'),
    path('purchases/', views.PurchaseListCreateView.as_view(), name='purchase-list'),
    path('purchases/<int:pk>/', views.PurchaseDetailView.as_view(), name='purchase-detail'),
    path('purchase-items/', views.PurchaseItemListCreateView.as_view(), name='purchase-item-list'),
    path('purchase-payments/', views.PurchasePaymentListCreateView.as_view(), name='purchase-payment-list'),
    path('inventory-batches/', views.InventoryBatchListCreateView.as_view(), name='inventory-batch-list'),
    path('inventory-batches/<int:pk>/', views.InventoryBatchDetailView.as_view(), name='inventory-batch-detail'),
    path('inventory-transactions/', views.InventoryTransactionListCreateView.as_view(), name='inventory-transaction-list'),
    path('stock-reservations/', views.StockReservationListCreateView.as_view(), name='stock-reservation-list'),
    path('damage-reports/', views.DamageReportListCreateView.as_view(), name='damage-report-list'),
    path('lost-inventory/', views.LostInventoryListCreateView.as_view(), name='lost-inventory-list'),
    path('stock-adjustments/', views.StockAdjustmentListCreateView.as_view(), name='stock-adjustment-list'),
    path('supplier-returns/', views.SupplierReturnListCreateView.as_view(), name='supplier-return-list'),
    path('stock-audits/', views.StockAuditListCreateView.as_view(), name='stock-audit-list'),

    # =========================================================================
    #  GEO
    # =========================================================================
    path('countries/', views.CountryListCreateView.as_view(), name='country-list'),
    path('countries/<int:pk>/', views.CountryDetailView.as_view(), name='country-detail'),
    path('divisions/', views.DivisionListCreateView.as_view(), name='division-list'),
    path('divisions/<int:pk>/', views.DivisionDetailView.as_view(), name='division-detail'),
    path('districts/', views.DistrictListCreateView.as_view(), name='district-list'),
    path('districts/<int:pk>/', views.DistrictDetailView.as_view(), name='district-detail'),
    path('areas/', views.AreaListCreateView.as_view(), name='area-list'),
    path('areas/<int:pk>/', views.AreaDetailView.as_view(), name='area-detail'),
    path('courier-providers/', views.CourierProviderListCreateView.as_view(), name='courier-provider-list'),
    path('courier-providers/<int:pk>/', views.CourierProviderDetailView.as_view(), name='courier-provider-detail'),
    path('shipping-zones/', views.ShippingZoneListCreateView.as_view(), name='shipping-zone-list'),
    path('shipping-zones/<int:pk>/', views.ShippingZoneDetailView.as_view(), name='shipping-zone-detail'),
    path('shipping-rates/', views.ShippingRateListCreateView.as_view(), name='shipping-rate-list'),
    path('shipping-rates/<int:pk>/', views.ShippingRateDetailView.as_view(), name='shipping-rate-detail'),

    # =========================================================================
    #  ACCOUNTING
    # =========================================================================
    path('account-categories/', views.AccountCategoryListCreateView.as_view(), name='account-category-list'),
    path('account-categories/<int:pk>/', views.AccountCategoryDetailView.as_view(), name='account-category-detail'),
    path('account-transactions/', views.AccountTransactionListCreateView.as_view(), name='account-transaction-list'),
    path('account-transactions/<int:pk>/', views.AccountTransactionDetailView.as_view(), name='account-transaction-detail'),
    path('tax-configurations/', views.TaxConfigurationListCreateView.as_view(), name='tax-configuration-list'),
    path('tax-configurations/<int:pk>/', views.TaxConfigurationDetailView.as_view(), name='tax-configuration-detail'),
    path('fraud-rules/', views.FraudRuleListCreateView.as_view(), name='fraud-rule-list'),
    path('fraud-rules/<int:pk>/', views.FraudRuleDetailView.as_view(), name='fraud-rule-detail'),
    path('ip-blacklist/', views.IPBlacklistListCreateView.as_view(), name='ip-blacklist-list'),
    path('ip-blacklist/<int:pk>/', views.IPBlacklistDetailView.as_view(), name='ip-blacklist-detail'),
    path('audit-logs/', views.AuditLogListCreateView.as_view(), name='audit-log-list'),
    path('audit-logs/<int:pk>/', views.AuditLogDetailView.as_view(), name='audit-log-detail'),

    # =========================================================================
    #  POS OPERATIONS
    # =========================================================================
    path('pos/terminals/', views.POSTerminalListCreateView.as_view(), name='pos-terminal-list'),
    path('pos/terminals/<int:pk>/', views.POSTerminalDetailView.as_view(), name='pos-terminal-detail'),
    path('pos/shifts/', views.POSShiftListCreateView.as_view(), name='pos-shift-list'),
    path('pos/shifts/<int:pk>/', views.POSShiftDetailView.as_view(), name='pos-shift-detail'),
    path('pos/shifts/start/', views.POSShiftStartView.as_view(), name='pos-shift-start'),
    path('pos/shifts/end/', views.POSShiftEndView.as_view(), name='pos-shift-end'),
    path('pos/registers/', views.CashRegisterListCreateView.as_view(), name='pos-register-list'),
    path('pos/registers/<int:pk>/', views.CashRegisterDetailView.as_view(), name='pos-register-detail'),
    path('pos/registers/reconcile/', views.CashRegisterReconcileView.as_view(), name='pos-register-reconcile'),
    path('pos/cash-movements/', views.CashMovementListCreateView.as_view(), name='pos-cash-movement-list'),
    path('pos/cash-movements/<int:pk>/', views.CashMovementDetailView.as_view(), name='pos-cash-movement-detail'),
]
