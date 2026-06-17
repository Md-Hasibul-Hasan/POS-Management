# E-Commerce POS & Inventory Management System

![Django](https://img.shields.io/badge/Django-6.0-green)
![DRF](https://img.shields.io/badge/Django_REST_Framework-3.17-red)
![SimpleJWT](https://img.shields.io/badge/Auth-SimpleJWT-blue)
![Swagger](https://img.shields.io/badge/API_Docs-Swagger-success)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)

A full-featured e-commerce backend with offline POS support, inventory management, and a comprehensive authentication system built with Django REST Framework.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Complete Workflow](#complete-workflow)
  - [1. Authentication & Account Lifecycle](#1-authentication--account-lifecycle)
  - [2. Product & Catalog Management](#2-product--catalog-management)
  - [3. Customer Management](#3-customer-management)
  - [4. Shopping Cart & Orders](#4-shopping-cart--orders)
  - [5. Payments & Refunds](#5-payments--refunds)
  - [6. Inventory & Supply Chain](#6-inventory--supply-chain)
  - [7. Marketing & Promotions](#7-marketing--promotions)
  - [8. Shipping & Logistics](#8-shipping--logistics)
  - [9. Accounting & Fraud Protection](#9-accounting--fraud-protection)
- [API Endpoints](#api-endpoints)
- [Role-Based Permissions](#role-based-permissions)
- [Pricing Engine](#pricing-engine)
- [Security Features](#security-features)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)

---

## Overview

This system is a complete **omni-channel e-commerce platform** that serves:

- **Online Store** — Full-featured web/mobile e-commerce APIs
- **Offline POS** — Point-of-sale system for physical retail stores
- **Inventory Management** — Real-time stock tracking across warehouses and storefronts
- **Supply Chain** — Supplier management, purchase orders, batch tracking

### Core Capabilities

| Capability | Description |
|---|---|
| **Multi-Role Access** | Admin, Owner, Manager, Salesman, Customer — each with granular permissions |
| **Omni-Channel Orders** | Orders from POS, online store, mobile app, admin panel, or API |
| **Real-Time Inventory** | FIFO batch tracking, stock reservations, audit trails |
| **Discount Engine** | Campaign → Variant → Product → Coupon priority-based stacking |
| **Multi-Payment Gateway** | Card, wallet, bank transfer, COD, EMI with fraud scoring |
| **2FA & Account Security** | OTP verification, device tracking, login history, account lockout |

---

## System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                            CLIENT LAYER                                  │
│         (Web App / Mobile App / POS Terminal / Third-Party APIs)          │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          AUTHENTICATION LAYER                            │
│                                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────┐   │
│  │ JWT Auth    │  │ Session      │  │ 2FA OTP    │  │ OAuth2       │   │
│  │ + Rotation  │  │ Tracking     │  │ Verification│  │ (Google)     │   │
│  └─────────────┘  └──────────────┘  └────────────┘  └──────────────┘   │
│                                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────┐   │
│  │ Rate Limit  │  │ Account      │  │ Login      │  │ Token        │   │
│  │ & Throttle  │  │ Lockout      │  │ History    │  │ Blacklist    │   │
│  └─────────────┘  └──────────────┘  └────────────┘  └──────────────┘   │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           POS LAYER                                      │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Catalog  │  │ Products │  │ Customers│  │ Orders   │  │ Payments │  │
│  │ Mgmt     │  │ & Variants│  │ & Groups │  │ & Carts  │  │ & Refunds│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Inventory │  │ Marketing│  │ Shipping │  │Accounting│  │ Pricing  │  │
│  │ Mgmt     │  │ Campaigns│  │ & Geo    │  │ & Fraud  │  │ Engine   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Complete Workflow

### 1. Authentication & Account Lifecycle

```
Registration → Email Verification → Login → [2FA if enabled] → JWT Issued
     │                                                              │
     │                                                              ├─ Access Token (short-lived)
     │                                                              └─ Refresh Token (rotated)
     │
     ├── Profile Management (name, image, password change)
     ├── Email Change (OTP verified)
     ├── Multi-Device Session Management
     ├── Login History & Audit Trail
     └── Account Deletion (secure permanent removal)
```

**Role Hierarchy:**

| Role | Access Level |
|---|---|
| **Admin** (superuser) | Full system access |
| **Owner** | Full business access, accounting, fraud rules |
| **Manager** | Operations management, campaigns, customer groups |
| **Salesman** | POS operations, orders, customer profiles |
| **Customer** | Browse products, manage own cart/wishlist/orders |

---

### 2. Product & Catalog Management

```
Category / Brand / Unit / Tag ──┐
                                 ├──→ Product ──→ Product Variants (size, color, etc.)
Attribute / Attribute Value ────┘       │
                                         ├── Product Images (multiple, primary)
                                         ├── Product Videos (YouTube/Vimeo)
                                         ├── Product FAQs
                                         └── Product Reviews (moderated, verified purchase)
```

- **Hierarchical Categories** — Nested categories with parent-child relationships and circular reference detection
- **Product Variants** — Multi-attribute variants (size, color, etc.) with unique attribute signatures
- **SEO Fields** — Meta title, description, keywords per product
- **Discount Support** — Percentage or fixed discounts at product and variant level
- **Stock Status** — Auto-computed from available stock (in stock / low stock / out of stock)
- **Approval Workflow** — Products go through draft → pending → approved → published lifecycle

---

### 3. Customer Management

```
User Registration
       │
       ▼
Customer Profile ──→ Customer Group (discount tiers)
       │
       ├── Addresses (multiple, type: home/work/other, default)
       ├── Wallet (credit/debit transactions, balance tracking)
       ├── Loyalty Points (earn/redeem/expire, lifetime tracking)
       ├── Customer Ledger (sale/payment/return/refund/adjustment)
       ├── Wishlist
       └── Compare List
```

- **Referral System** — Referral codes and referred-by tracking
- **Customer Groups** — Group-based discount percentages for tiered pricing
- **Wallet System** — Full balance tracking with transaction history
- **Loyalty Program** — Earn/redeem points with expiration dates

---

### 4. Shopping Cart & Orders

```
Cart ──→ Cart Items ──→ Checkout ──→ Order
                                    │
                                    ├── Order Items (price snapshot at purchase time)
                                    ├── Coupon Application
                                    ├── Shipping Address (snapshot)
                                    ├── Billing Address (snapshot)
                                    ├── Tax Calculation
                                    │
                                    ├── Status Flow:
                                    │   Pending → Confirmed → Processing → Shipped → Delivered
                                    │                                                      │
                                    │   Cancelled ←──────────────────────────────────────────┘
                                    │   Returned ←──────────────────────────────────────────┘
                                    │
                                    ├── Return Records (full/partial return, inspection workflow)
                                    ├── Exchange Requests (variant-to-variant exchange)
                                    └── Shipments (courier tracking, pickup→delivery lifecycle)
```

**Cart Pricing (Powered by PricingEngine):**
1. Each cart item's `unit_price` is computed via `PricingEngine` — campaign discount checked first, then variant discount, then product discount
2. Cart totals are auto-recalculated after every item mutation
3. Coupons are validated at order level

**Order Pricing:**
- Order items store price snapshots (product, variant, campaign, tax) at time of purchase
- Coupon discounts are applied at order level after item prices are finalized
- Total = subtotal + shipping + tax + gift wrap - discount

---

### 5. Payments & Refunds

```
Payment Gateway (Card/Wallet/Bank/BNPL)
       │
       ▼
Payment Method (Debit Card/Credit Card/Wallet/UPI/Bank Transfer)
       │
       ▼
Payment Session (Created → Initiated → Awaiting Response → Completed/Failed/Expired)
       │
       ▼
Payment Record
       │
       ├── Status: Initiated → Processing → Authorized → Captured → Refunded
       │         └── Failed (any stage)
       │
       ├── Fraud Scoring (0-100 score, risk level, flagging)
       ├── EMI Support (bank, months, amount tracking)
       ├── COD Support (with collection timestamp)
       │
       └── RefundTransaction (pending → completed/failed, gateway integration)
            └── Refund Types: Full or partial, with failure handling
```

**Payment Features:**
- Multi-gateway support with sandbox/live configuration
- Card details tracking (brand, issuer, last four digits)
- Mobile banking transaction ID support
- Webhook-ready architecture
- Payment event logging for audit

---

### 6. Inventory & Supply Chain

```
Supplier ──→ Purchase Order ──→ Purchase Items
                                     │
                                     ▼
                            Inventory Batch (FIFO)
                            (cost_price, received_quantity,
                             remaining_quantity, expiry_date)
                                     │
                                     ▼
                     InventoryTransaction (SINGLE SOURCE OF TRUTH)
                     ┌──────────────┬──────────────┬────────────────┐
                     │  Purchase    │ POS Sale     │ Online Sale    │
                     ├──────────────┼──────────────┼────────────────┤
                     │Return (Cust) │Return (Supp) │ Damage Report  │
                     ├──────────────┼──────────────┼────────────────┤
                     │ Lost Report  │ Adjustments  │ Reservation    │
                     └──────────────┴──────────────┴────────────────┘
                                     │
                                     ▼
                  Stock Reservation (Cart → Checkout → Convert to Sale / Release)
                                     │
                                     ▼
                         Stock Audit Cycle
                  (Scheduled → In Progress → Completed → Approved)
                  (system_stock vs physical_stock → variance)
```

**Key Principles:**
- `InventoryTransaction` is the **single source of truth** for all stock mutations
- Product/Variant stock fields are **cached summaries only** — never use directly for real-time calculations
- **FIFO costing** via `InventoryBatch` — each batch tracks cost price for COGS calculation
- **Stock Reservation** prevents overselling during checkout
- **Audit Trail** — every transaction records previous/new stock, performer, source document

---

### 7. Marketing & Promotions

```
Campaign Management
  ├── Types: Flash Sale, Seasonal, Clearance, Custom
  ├── Discount: Percentage or Fixed (with max cap)
  ├── Scope: Applicable products and/or categories
  ├── Schedule: Start/end dates with active/running status
  └── Usage Limits: Global and per-user caps

Coupon System
  ├── Categories: Welcome, Flash Sale, Seasonal, Referral
  ├── Groups: Cashback, Free Shipping, Product Discount
  ├── Conditions: Min order amount, applicable products/categories/users
  ├── First-order-only option
  └── Stack Priority

Banner Management
  ├── Link Types: Product, Category, Campaign, URL, None
  ├── Mobile-specific image support
  └── Scheduled display with sort ordering

Store Settings
  ├── Brand info (logo, favicon, social links)
  ├── Support contact (email, phone, WhatsApp)
  ├── SEO metadata
  └── Maintenance mode

Notification System
  ├── Types: Low Stock, Out of Stock, Damage, Lost, New Order, Return Request
  ├── Channels: In-App, Email, Both
  └── Templates with variable substitution
```

---

### 8. Shipping & Logistics

```
Country → Division → District → Area (hierarchical geography)
                                    │
                                    ▼
Shipping Zone (group of districts/areas)
                                    │
                                    ▼
Courier Provider ──→ Shipping Rate
                     ├── Weight-based pricing (base + per kg)
                     ├── COD fee
                     ├── Free shipping threshold
                     └── Estimated delivery days

Shipment Lifecycle:
Pending → Pickup Requested → Picked Up → In Transit → Delivered
                                                         │
              Failed ←────────────────────────────────────┘
              Returned ←──────────────────────────────────┘
```

---

### 9. Accounting & Fraud Protection

```
Account Category (Income/Expense)
       │
       ▼
Account Transaction (date, category, amount, reference)
       │
       ▼
Tax Configuration (VAT/GST/Sales Tax — location-based, priority-ordered)

Fraud Prevention
  ├── Fraud Rules (IP/Device/Order/Payment — configurable scoring)
  ├── IP Blacklist (temporary/permanent blocks)
  └── Audit Logging (action_type, module, old/new data, IP, user agent)
```

---

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/register/` | Register a new user |
| POST | `/login/` | Log in with email and password |
| POST | `/google-login/` | Google OAuth login or registration |
| POST | `/logout/` | Log out from the current device |
| POST | `/logout-all/` | Log out from all devices |
| POST | `/verify-email/<uid>/<token>/` | Verify account via activation link |
| POST | `/verify-otp/` | Verify account via OTP |
| POST | `/resend-verification/` | Resend verification email |
| POST | `/2fa/setup/` | Start 2FA setup |
| POST | `/2fa/enable/` | Enable 2FA |
| POST | `/2fa/verify/` | Complete 2FA login |
| POST | `/2fa/disable/` | Disable 2FA |
| GET | `/2fa/status/` | Check 2FA status |
| GET | `/profile/` | Get profile |
| PATCH | `/profile/` | Update profile |
| POST | `/change-email/request/` | Request email change OTP |
| POST | `/change-email/confirm/` | Confirm email change |
| POST | `/change-password/` | Change password |
| POST | `/reset-password/request/` | Request password reset |
| POST | `/reset-password/by-link/` | Reset via link |
| POST | `/reset-password/by-otp/` | Reset via OTP |
| GET | `/active-sessions/` | List active sessions |
| DELETE | `/delete-session/<id>/` | Logout specific session |
| GET | `/login-history/` | View login history |
| DELETE | `/delete-account/` | Delete account |
| POST | `/token/refresh/` | Refresh access token |
| POST | `/token/verify/` | Verify token |

### POS — Catalog (`/api/pos/`)

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/categories/` | List/create categories |
| GET/PUT/DELETE | `/categories/<id>/` | Retrieve/update/delete category |
| GET/POST | `/brands/` | List/create brands |
| GET/PUT/DELETE | `/brands/<id>/` | Retrieve/update/delete brand |
| GET/POST | `/units/` | List/create units |
| GET/PUT/DELETE | `/units/<id>/` | Retrieve/update/delete unit |
| GET/POST | `/tags/` | List/create tags |
| GET/PUT/DELETE | `/tags/<id>/` | Retrieve/update/delete tag |
| GET/POST | `/attributes/` | List/create attributes |
| GET/PUT/DELETE | `/attributes/<id>/` | Retrieve/update/delete attribute |
| GET/POST | `/attribute-values/` | List/create attribute values |
| GET/PUT/DELETE | `/attribute-values/<id>/` | Retrieve/update/delete attribute value |
| GET/POST | `/faqs/` | List/create FAQs |
| GET/PUT/DELETE | `/faqs/<id>/` | Retrieve/update/delete FAQ |
| GET/POST | `/reviews/` | List/create reviews |
| GET/PUT/DELETE | `/reviews/<id>/` | Retrieve/update/delete review |

### POS — Products (`/api/pos/`)

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/products/` | List/create products |
| GET/PUT/DELETE | `/products/<id>/` | Retrieve/update/delete product |
| GET/POST | `/variants/` | List/create variants |
| GET/PUT/DELETE | `/variants/<id>/` | Retrieve/update/delete variant |
| GET/POST | `/product-images/` | List/create product images |
| GET/PUT/DELETE | `/product-images/<id>/` | Retrieve/update/delete image |
| GET/POST | `/product-videos/` | List/create product videos |
| GET/PUT/DELETE | `/product-videos/<id>/` | Retrieve/update/delete video |

### POS — Customers (`/api/pos/`)

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/customer-profiles/` | List/create customer profiles |
| GET/PUT/DELETE | `/customer-profiles/<id>/` | Retrieve/update/delete customer |
| GET/POST | `/customer-groups/` | List/create customer groups |
| GET/PUT/DELETE | `/customer-groups/<id>/` | Retrieve/update/delete group |
| GET/POST | `/customer-ledger/` | List ledger entries |
| GET/POST | `/addresses/` | List/create addresses |
| GET/PUT/DELETE | `/addresses/<id>/` | Retrieve/update/delete address |
| GET/POST | `/wallet-transactions/` | List wallet transactions |
| GET/PUT/DELETE | `/loyalty-points/<id>/` | Retrieve loyalty points |
| GET/POST | `/loyalty-transactions/` | List loyalty transactions |
| GET/POST | `/wishlist/` | List/create wishlist items |
| GET/PUT/DELETE | `/wishlist/<id>/` | Retrieve/update/delete wishlist item |
| GET/POST | `/compare-list/` | List/create compare list items |
| GET/PUT/DELETE | `/compare-list/<id>/` | Retrieve/update/delete compare item |

### POS — Orders & Carts (`/api/pos/`)

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/orders/` | List/create orders |
| GET/PUT/DELETE | `/orders/<id>/` | Retrieve/update/delete order |
| GET/POST | `/order-items/` | List/create order items |
| GET/POST | `/carts/` | List/create carts |
| GET/PUT/DELETE | `/carts/<id>/` | Retrieve/update/delete cart |
| GET/POST | `/cart-items/` | List/create cart items |
| GET/PUT/DELETE | `/cart-items/<id>/` | Retrieve/update/delete cart item |
| GET/POST | `/returns/` | List/create return records |
| GET/PUT/DELETE | `/returns/<id>/` | Retrieve/update/delete return |
| GET/POST | `/exchanges/` | List/create exchange requests |
| GET/PUT/DELETE | `/exchanges/<id>/` | Retrieve/update/delete exchange |
| GET/POST | `/shipments/` | List/create shipments |
| GET/PUT/DELETE | `/shipments/<id>/` | Retrieve/update/delete shipment |

### POS — Payments (`/api/pos/`)

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/payment-gateways/` | List/create gateways |
| GET/PUT/DELETE | `/payment-gateways/<id>/` | Retrieve/update/delete gateway |
| GET/POST | `/payment-methods/` | List/create payment methods |
| GET/PUT/DELETE | `/payment-methods/<id>/` | Retrieve/update/delete method |
| GET/POST | `/payment-sessions/` | List/create payment sessions |
| GET/PUT/DELETE | `/payment-sessions/<id>/` | Retrieve/update/delete session |
| GET/POST | `/payments/` | List/create payments |
| GET/PUT/DELETE | `/payments/<id>/` | Retrieve/update/delete payment |
| GET/POST | `/refunds/` | List/create refunds |
| GET/POST | `/payment-event-logs/` | List payment event logs |

### POS — Marketing (`/api/pos/`)

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/campaigns/` | List/create campaigns |
| GET/PUT/DELETE | `/campaigns/<id>/` | Retrieve/update/delete campaign |
| GET/POST | `/coupons/` | List/create coupons |
| GET/PUT/DELETE | `/coupons/<id>/` | Retrieve/update/delete coupon |
| GET/POST | `/coupon-usages/` | List coupon usages |
| GET/POST | `/banners/` | List/create banners |
| GET/PUT/DELETE | `/banners/<id>/` | Retrieve/update/delete banner |
| GET/POST | `/store-settings/` | List/create store settings |
| GET/PUT/DELETE | `/store-settings/<id>/` | Retrieve/update/delete setting |
| GET/POST | `/notifications/` | List/create notifications |
| GET/PUT/DELETE | `/notifications/<id>/` | Retrieve/update/delete notification |
| GET/POST | `/notification-templates/` | List/create templates |
| GET/PUT/DELETE | `/notification-templates/<id>/` | Retrieve/update/delete template |

### POS — Inventory (`/api/pos/`)

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/suppliers/` | List/create suppliers |
| GET/PUT/DELETE | `/suppliers/<id>/` | Retrieve/update/delete supplier |
| GET/POST | `/supplier-ledger/` | List supplier ledger |
| GET/POST | `/purchases/` | List/create purchases |
| GET/PUT/DELETE | `/purchases/<id>/` | Retrieve/update/delete purchase |
| GET/POST | `/purchase-items/` | List/create purchase items |
| GET/POST | `/purchase-payments/` | List/create purchase payments |
| GET/POST | `/inventory-batches/` | List/create inventory batches |
| GET/PUT/DELETE | `/inventory-batches/<id>/` | Retrieve/update/delete batch |
| GET/POST | `/inventory-transactions/` | List inventory transactions |
| GET/POST | `/stock-reservations/` | List stock reservations |
| GET/POST | `/damage-reports/` | List/create damage reports |
| GET/POST | `/lost-inventory/` | List/create lost inventory |
| GET/POST | `/stock-adjustments/` | List/create stock adjustments |
| GET/POST | `/supplier-returns/` | List/create supplier returns |
| GET/POST | `/stock-audits/` | List/create stock audits |

### POS — Geography & Shipping (`/api/pos/`)

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/countries/` | List/create countries |
| GET/PUT/DELETE | `/countries/<id>/` | Retrieve/update/delete country |
| GET/POST | `/divisions/` | List/create divisions |
| GET/PUT/DELETE | `/divisions/<id>/` | Retrieve/update/delete division |
| GET/POST | `/districts/` | List/create districts |
| GET/PUT/DELETE | `/districts/<id>/` | Retrieve/update/delete district |
| GET/POST | `/areas/` | List/create areas |
| GET/PUT/DELETE | `/areas/<id>/` | Retrieve/update/delete area |
| GET/POST | `/courier-providers/` | List/create courier providers |
| GET/PUT/DELETE | `/courier-providers/<id>/` | Retrieve/update/delete provider |
| GET/POST | `/shipping-zones/` | List/create shipping zones |
| GET/PUT/DELETE | `/shipping-zones/<id>/` | Retrieve/update/delete zone |
| GET/POST | `/shipping-rates/` | List/create shipping rates |
| GET/PUT/DELETE | `/shipping-rates/<id>/` | Retrieve/update/delete rate |

### POS — Accounting (`/api/pos/`)

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/account-categories/` | List/create account categories |
| GET/PUT/DELETE | `/account-categories/<id>/` | Retrieve/update/delete category |
| GET/POST | `/account-transactions/` | List/create account transactions |
| GET/PUT/DELETE | `/account-transactions/<id>/` | Retrieve/update/delete transaction |
| GET/POST | `/tax-configurations/` | List/create tax configs |
| GET/PUT/DELETE | `/tax-configurations/<id>/` | Retrieve/update/delete tax config |
| GET/POST | `/fraud-rules/` | List/create fraud rules |
| GET/PUT/DELETE | `/fraud-rules/<id>/` | Retrieve/update/delete fraud rule |
| GET/POST | `/ip-blacklist/` | List/create IP blacklist entries |
| GET/PUT/DELETE | `/ip-blacklist/<id>/` | Retrieve/update/delete IP entry |
| GET | `/audit-logs/` | List audit logs |
| GET | `/audit-logs/<id>/` | Retrieve audit log detail |

---

## Role-Based Permissions

The system implements **granular role-based access control** across all POS endpoints.

| Permission Class | Read Access | Write Access |
|---|---|---|
| `IsOwner` | — | Owner, Admin only |
| `IsOwnerOrManager` | — | Owner, Manager, Admin |
| `IsEmployee` | — | Any employee (Owner, Manager, Salesman) |
| `IsEmployeeOrReadOnly` | Any authenticated user | Owner, Manager, Salesman |
| `IsOwnerOrManagerOrReadOnly` | Any authenticated user | Owner, Manager |
| `IsOwnerOrReadOnly` | Any authenticated user | Owner only |

**Permission Mapping by Module:**

| Module | Guests | Customers | Salesman | Manager | Owner/Admin |
|---|---|---|---|---|---|
| Catalog | Read only | Read only | Full CRUD | Full CRUD | Full CRUD |
| Products | Read only | Read only | Full CRUD | Full CRUD | Full CRUD |
| Customers | — | Own profile | Read/Write | Full CRUD | Full CRUD |
| Customer Groups | — | — | Read only | Full CRUD | Full CRUD |
| Customer Ledger | — | — | — | Full CRUD | Full CRUD |
| Wallet/Loyalty | — | — | Read only | Full CRUD | Full CRUD |
| Orders | — | Own orders | Full CRUD | Full CRUD | Full CRUD |
| Carts | — | — | Read/Write | Read/Write | Full CRUD |
| Payments | — | — | Full CRUD | Full CRUD | Full CRUD |
| Refunds | — | — | — | Full CRUD | Full CRUD |
| Payment Config | — | — | Read only | Read/Write | Read/Write |
| Campaigns/Coupons | — | — | Read only | Read/Write | Read/Write |
| Store Settings | — | — | — | Full CRUD | Full CRUD |
| Inventory | — | — | Full CRUD | Full CRUD | Full CRUD |
| Supplier Ledger | — | — | — | Full CRUD | Full CRUD |
| Shipping/Geo | Read only | Read only | Read/Write | Read/Write | Read/Write |
| Accounting | — | — | Read only | Read/Write | Read/Write |
| Audit Logs | — | — | Read only | Read only | Read only |
| Fraud Rules | — | — | — | — | Full CRUD |

---

## Pricing Engine

The `PricingEngine` class (`POS/services.py`) implements a **priority-based discount engine** that determines the final selling price for every product.

### Discount Priority (highest wins):

```
1. CAMPAIGN DISCOUNT   — Applied at product/variant via active Campaign
2. VARIANT DISCOUNT    — ProductVariant.discount_value
3. PRODUCT DISCOUNT    — Product.discount_value
4. COUPON DISCOUNT     — Applied at order level (stacks after product price)
```

### Key Methods:

- **`calculate_product_price(product, campaign_discount)`** — Computes final price for non-variant products with campaign awareness
- **`calculate_variant_price(variant, campaign_discount)`** — Computes final price for variants (campaign → variant → parent product discount)
- **`apply_coupon_discount(price, coupon)`** — Applies coupon discount at order level with max cap
- **`find_best_campaign_for_product(product)`** — Finds the best active campaign applicable to a product (by product or category)

### Integration Points:

- **Product Serializers** — `final_price` field in API responses computes live pricing with campaign discounts
- **Cart Serializers** — Cart item unit prices and totals are computed via PricingEngine for accurate checkout pricing
- **Order Serializers** — Coupon validation uses PricingEngine to verify discount amounts

---

## Security Features

### Account Protection
- **Rate Limiting** — Login and registration throttled to prevent brute force
- **Account Lockout** — Progressive lockout after failed login attempts (configurable)
- **OTP Brute Force Protection** — OTP attempt locking after max wrong attempts
- **Account Lock Duration** — Configurable lockout timeout

### Token & Session Security
- **JWT with Rotation** — Refresh tokens rotated on each use
- **Token Blacklisting** — Tokens invalidated on logout/password change
- **Session Tracking** — Every login creates a tracked session with device fingerprint
- **Logout All Devices** — Invalidate all sessions at once
- **Password Change Auto-Logout** — All existing sessions revoked on password change

### Audit & Monitoring
- **Login History** — Complete record of all login attempts (success/failure, IP, user agent)
- **2FA Audit Logs** — Track 2FA setup, enable, disable, verification events
- **Account-Level Audit Logs** — Track sensitive operations across all modules
- **Device Fingerprinting** — Track browser, OS, device type, IP, and location

### Additional Security
- **IP Blacklisting** — Block malicious IPs temporarily or permanently
- **Fraud Scoring** — Rule-based fraud detection (0-100 score, risk levels)
- **Payment Flagging** — Flag suspicious payment transactions
- **Soft Delete** — All records support soft deletion for data safety

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/pos-management.git
cd pos-management
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv .venv
```
Windows:
```bash
.venv\Scripts\activate
```
Linux/macOS:
```bash
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create a Superuser
```bash
python manage.py createsuperuser
```

### 6. Run the Development Server
```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/` with Swagger docs at `/api/schema/swagger-ui/`.

---

## Environment Variables

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
FRONTEND_URL=http://localhost:3000

# Email (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com

# OTP & Security
OTP_EXPIRE_TIMEOUT=600
MAX_WRONG_OTP_ATTEMPTS=5
OTP_LOCKED_UNTIL=600
PASSWORD_RESET_TIMEOUT=600
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION=600

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id

# Data Retention
LOGIN_HISTORY_RETENTION_DAYS=90
INACTIVE_SESSION_RETENTION_DAYS=30
TWO_FA_LOG_RETENTION_DAYS=30
```

---

## Project Structure

```text
Backend/
├── manage.py
├── requirements.txt
├── README.md
│
├── config/                          # Django project configuration
│   └── settings.py, urls.py, wsgi.py, asgi.py
│
├── Authentication/                  # Authentication & User Management
│   ├── authentication.py            # Session-aware JWT authentication
│   ├── models.py                    # User, UserSession, LoginHistory, 2FA
│   ├── serializers.py               # Registration, login, profile serializers
│   ├── permissions.py               # Role-based: IsOwner, IsEmployee, etc.
│   ├── renderers.py                 # Custom JSON renderer
│   ├── utils.py                     # Email utility, session management
│   ├── urls.py                      # Auth route definitions
│   ├── views/
│   │   ├── auth_views.py            # Register, Login, Logout, Delete Account
│   │   ├── password_views.py        # Change/reset password
│   │   ├── profile_views.py         # Profile CRUD, email change
│   │   ├── session_views.py         # Active sessions, login history
│   │   ├── token_views.py           # Token refresh/verify
│   │   ├── twofa_views.py           # 2FA setup/enable/disable/verify
│   │   ├── verification_views.py    # Email verify, OTP verify
│   │   ├── social_views.py          # Google OAuth
│   │   ├── employee_views.py        # Employee invitation/management
│   │   ├── permission_views.py      # Permission checks
│   │   ├── helpers.py               # Token generation, device tracking
│   │   └── throttles.py             # Rate limiting classes
│   └── management/commands/
│       └── cleanup_auth_tables.py   # Old data cleanup
│
└── POS/                             # Point of Sale & Inventory Management
    ├── services.py                  # PricingEngine (discount priority engine)
    ├── urls.py                      # All POS route definitions
    │
    ├── models/
    │   ├── common.py                # BaseModel, SoftDeleteManager
    │   ├── catalog.py               # Category, Brand, Unit, Tag, Attributes, Media, Reviews
    │   ├── product.py               # Product, ProductVariant
    │   ├── customer.py              # CustomerProfile, Group, Ledger, Address, Wallet, Loyalty
    │   ├── order.py                 # Order, OrderItem, Cart, CartItem, Returns, Shipments
    │   ├── payment.py               # PaymentGateway, Method, Session, Payment, Refund
    │   ├── marketing.py             # Campaign, Coupon, Banner, Store Settings, Notifications
    │   ├── inventory.py             # Supplier, Purchase, Batch, Transaction, Adjustments, Audit
    │   ├── geo.py                   # Country, Division, District, Area, Shipping
    │   └── accounting.py            # AccountCategory, Transaction, Tax, Fraud, IPBlacklist, Audit
    │
    ├── serializers/
    │   ├── catalog_serializers.py
    │   ├── product_serializers.py   # PricingEngine integrated (final_price)
    │   ├── customer_serializers.py
    │   ├── order_serializers.py     # PricingEngine integrated (cart/order pricing)
    │   ├── payment_serializers.py
    │   ├── marketing_serializers.py
    │   ├── inventory_serializers.py
    │   ├── geo_serializers.py
    │   └── accounting_serializers.py
    │
    └── views/
        ├── catalog_views.py         # Category, Brand, Unit, Tag, Attributes, FAQs, Reviews
        ├── product_views.py         # Product, Variant, Images, Videos
        ├── customer_views.py        # Profiles, Groups, Ledger, Address, Wallet, Wishlist
        ├── order_views.py           # Orders, Carts, Returns, Exchanges, Shipments
        ├── payment_views.py         # Gateways, Methods, Sessions, Payments, Refunds
        ├── marketing_views.py       # Campaigns, Coupons, Banners, Store Settings, Notifications
        ├── inventory_views.py       # Suppliers, Purchases, Batches, Transactions, Adjustments
        ├── geo_views.py             # Countries, Divisions, Districts, Areas, Shipping
        └── accounting_views.py      # Account Categories, Transactions, Tax, Fraud, Audit
```

---

## Author

Md Hasibul Hasan  
Backend Developer — Django & Django REST Framework

## License

MIT License