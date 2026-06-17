# POS + Inventory + Online Store Business Rules
## Production-Grade Enterprise Document — Single Store System

---

## 1. Product Management

### 1.1 Product Identification
- Every Product must have a unique SKU (Stock Keeping Unit).
- Every Product must have a unique Barcode (where applicable).
- Every Product must have a unique Slug for online store URL.
- Products can optionally have Serial Number tracking and Batch/Lot tracking.

### 1.2 Product Pricing
- Every Product has a Current Selling Price (Base Price).
- A Product may have multiple Purchase Costs across different batches, but the customer always sees one Selling Price.
- Selling Price is set by Admin and does not auto-change when purchase cost changes.
- **Selling Price Calculation**: If discount_value ≤ 0, selling_price = base_price. If discount_type is 'percentage', selling_price = base_price - (base_price × discount_value / 100). If discount_type is 'fixed', selling_price = max(base_price - discount_value, 0).
- **Discount Rules**: Percentage discount cannot exceed 100. Fixed discount cannot exceed base price.
- Discounts can be applied at Product level, Variant level, Campaign level, or Coupon level.
- **Coupon Group Stacking Rule**: Coupons in the same coupon_group (cashback, shipping, product_discount) cannot be combined. Coupons from different groups can be stacked. Stack priority determines which coupon applies first.

### 1.3 Product Stock Rule
- Product Stock cannot be edited directly. Stock changes only occur through authorized inventory transactions (Purchase, Sale, Return, Damage, Lost, Reservation, Adjustment).
- **Available Stock**: For non-variant products: max(base_stock - reserved_stock, 0). For variant products: sum of all active variants (stock - reserved_stock).
- **Stock Status**: If available_stock ≤ 0 → 'out_stock'. If available_stock ≤ low_stock_threshold → 'low_stock'. Otherwise → 'in_stock'.
- **Reserved Stock Constraint**: reserved_stock cannot exceed base_stock (for products) or stock (for variants).
- **Variant Product Stock Rule**: If has_variants = True, base_stock and reserved_stock must be 0. Variant stock becomes the source of truth.

### 1.4 Product Categories
- Products belong to Categories and Sub-Categories.
- **Self-Parent Prevention**: A category cannot be its own parent.
- **Circular Hierarchy Prevention**: Circular category references (A→B→C→A) are strictly prohibited.
- **Unique Name per Parent**: Category names must be unique within the same parent level.
- Products can be associated with Brands, Units, and Tags.

### 1.5 Product Variants
- Products may have Variants (e.g., Size, Color).
- **Default Variant Rule**: Only one default variant is allowed per product.
- **Attribute Signature**: Variant uniqueness is enforced via an auto-generated attribute signature (MD5 hash of sorted attribute IDs). This is system-managed and cannot be manually edited.
- **Unique Slug per Product**: Each variant slug must be unique within its product.
- Each variant has its own SKU, Barcode, Price, Stock, and Discount settings.
- **Variant Discount Rules**: Same as product discount: percentage max 100, fixed cannot exceed variant price.

### 1.6 Product Images & Videos
- **Primary Image Rule**: Only one primary image is allowed per product. If a primary image exists, no other image for the same product can be marked as primary.
- **Variant-Image Consistency**: Images linked to a variant must belong to the same product as the variant.
- **Video URL Validation**: YouTube URLs must contain 'youtube.com' or 'youtu.be'. Vimeo URLs must contain 'vimeo.com'.

### 1.7 Product Reviews
- **Rating Range**: Rating must be between 1 and 5 inclusive.
- **Verified Purchase**: A verified purchase review requires a linked order_item. The order_item must belong to the same user writing the review. The product in the review must match the order item product.
- **Delivery Requirement**: Only delivered orders can be reviewed.
- **One Review Per Order Item**: A user cannot submit more than one review for the same order item.
- **Moderation**: Reviews go through moderation (pending → approved/rejected).

---

## 2. Product Lifecycle Rules

### 2.1 Product Status Definitions

| Status | Description |
|--------|-------------|
| **Draft** | Product is being created; not visible to customers or usable in sales. |
| **Published** | Product is published and available for POS and Online Store sales. |
| **Archived** | Product is archived; not visible in store but data preserved. |

### 2.2 Approval Status
- Products require approval before publishing: **Pending → Approved → Published** or **Pending → Rejected**.
- When a product is approved, its status automatically transitions to Published.
- Approval is required before any product becomes active in the store.

### 2.3 Lifecycle Transitions
- **Draft → Published**: Product is reviewed and approved.
- **Published → Archived**: Admin archives product (e.g., seasonal, discontinued).
- **Archived → Published**: Product is re-enabled (rare; requires re-approval if configurable).
- **Soft Delete**: Products are soft-deleted (is_deleted flag). Deleted products are excluded from all active queries.
- All timestamps (published_at, deleted_at) are recorded for audit.

### 2.4 Reorder Level
- Each Product (or Variant) can have a **Reorder Level** quantity.
- When available stock falls below the Reorder Level, the system flags the product for reordering.
- Reorder level is configurable per product.

### 2.5 Low Stock Threshold
- Each Product (or Variant) can have a **Low Stock Threshold** quantity.
- When available stock falls below this threshold, a Low Stock Alert is triggered.
- Low Stock Threshold is typically set higher than Reorder Level to give early warning.
- **Stock Alert**: When stock alert is enabled, the system automatically sends notifications for low stock conditions.

### 2.6 Product Visibility Rules
- Only **Published** and **Approved** products appear in POS and Online Store.
- **Draft** and **Archived** products are hidden from customers.
- **Soft-deleted** products show "Deleted" in admin panels.
- **Digital Products**: Digital products should not require shipping (requires_shipping = False).

### 2.7 Product Caching
- Product caches are maintained for performance: average rating, total reviews, total units sold, total revenue.
- Cached values are non-negative and updated periodically or on key events.

---

## 3. Supplier Management

- All Suppliers must be registered in the system.
- Every Purchase must be linked to a Supplier.
- Supplier-wise Purchase History is viewable.
- Supplier-wise Due and Payment Tracking is supported.
- Supplier Ledger maintains balance records.

---

## 4. Purchase Management

### 4.1 Purchase Entry
- Purchasing products from a Supplier creates a Purchase Entry.
- Every Purchase has a unique Purchase Invoice Number.
- The same Product can be purchased at different costs at different times.

### 4.2 Purchase to Batch
- Each Purchase Item creates a new Inventory Batch.
- Batch records: Cost Price, Quantity Received, Remaining Quantity.

**Example:**
```
Purchase-1: Mouse
  20 pcs @ 300 BDT
  → Batch-1: 20 pcs @ 300 BDT

Purchase-2: Mouse
  30 pcs @ 350 BDT
  → Batch-2: 30 pcs @ 350 BDT
```

### 4.3 Purchase Payments
- Purchase payments can be tracked against suppliers.
- Partial payments and due payments are supported.

---

## 5. Inventory Batch Rules

- Each Purchase Item creates a new Inventory Batch.
- Each Batch stores:
  - Product / Variant reference
  - Cost Price (FIFO cost basis)
  - Received Quantity
  - Remaining Quantity
  - Purchase Date
  - Expiry Date (if applicable)
  - Batch/Lot Number (if applicable)
- A Batch remains Active until its Remaining Quantity reaches zero.
- Historical Batch data is never deleted or overwritten.

---

## 6. Stock Management

### 6.1 Current Stock Calculation
```
Current Stock =
  + Purchase
  + Customer Return (Resellable)
  - POS Sale
  - Online Sale (Delivered)
  - Damage
  - Lost
  - Adjustment (Negative)
  + Adjustment (Positive)
```

### 6.2 Stock Validation Rules
- Stock can never go negative.
- Sales cannot proceed if available stock is insufficient.
- Available Stock = Total Stock - Reserved Stock - Damaged Stock - Blocked Stock.
- **Inventory Transaction Quantity Rule**: Transaction quantity cannot be zero. Every transaction must increase or decrease stock by a non-zero amount.
- **Stock Calculation Validation**: For Stock In transactions (purchase, return, release): new_stock = previous_stock + quantity. For Stock Out transactions (sale, reserve): new_stock = previous_stock - quantity. Both previous_stock and new_stock must be non-negative.

### 6.3 Inventory Status Types
| Status | Description |
|--------|-------------|
| **Available** | Can be sold via POS or Online Store. |
| **Reserved** | Locked for a Confirmed Online Order; not available for other sales. |
| **Damaged** | Cannot be sold; tracked separately. |
| **Returned** | Customer return pending inspection. |
| **Lost** | Missing inventory after audit. |
| **Blocked** | Administrative hold; not available for sale. |

---

## 7. POS Sale Rules

- POS Sales use **FIFO (First In, First Out)** method for cost deduction.
- Older Batch stock is deducted first.
- Stock is not deducted until Sale is Confirmed.
- A unique Sale Invoice is generated for each POS transaction.
- POS and Online Store use the same Selling Price.

**FIFO Deduction Example:**
```
Batch-1: 10 pcs @ 300 BDT
Batch-2: 20 pcs @ 400 BDT

Sale: 15 pcs

Deduction:
  10 pcs from Batch-1 @ 300 BDT
   5 pcs from Batch-2 @ 400 BDT

COGS = (10 × 300) + (5 × 400) = 5,000 BDT
Revenue = 15 × Selling Price
```

---

## 8. Online Order Rules

### 8.1 Order Status Flow
```
Pending → Confirmed → Processing → Shipped → Delivered
                                       ↓
                                 Cancelled

Delivered → Returned
```

### 8.2 Order Status Stock Rules
| Status | Stock Impact |
|--------|-------------|
| **Pending** | No stock change. |
| **Confirmed** | Stock is Reserved (locked). |
| **Processing** | Stock remains Reserved. |
| **Shipped** | Stock remains Reserved. |
| **Delivered** | Stock is deducted via FIFO; Reservation is Released. |
| **Cancelled** | Reserved Stock is Released back to Available. |
| **Returned** | Stock is added back after inspection (see Return Rules). |

### 8.3 Order Financial Validation
- Order total must equal: subtotal + shipping_cost + tax_amount + gift_wrap_charge - discount_amount.
- All financial fields (subtotal, shipping_cost, tax_amount, discount_amount, total_amount) must be non-negative.
- Gift orders require a gift message.
- Shipping and billing addresses must belong to the order's user.

### 8.4 Order Status Logging
- Every order status change is logged with: previous_status, new_status, changed_by, note, timestamp.
- **Same Status Prevention**: A status transition to the same status is not allowed (e.g., processing → processing is invalid).

### 8.5 Order Fraud Detection
- Each order tracks: IP address, device info, fraud score, risk level.
- Fraud score is non-negative. If fraud score exceeds threshold, the order is flagged.
- Risk levels: low, medium, high.

---

## 9. Selling Price Rules

- Every Product has one Active Selling Price at any time.
- POS and Online Store use the identical Selling Price.
- Admin can change Selling Price at any time.
- Changing Purchase Cost does not auto-update Selling Price.
- Discounts are applied on top of Selling Price.

**Example:**
```
Batch-1 Mouse Cost = 300 BDT
Batch-2 Mouse Cost = 400 BDT
Selling Price = 500 BDT (Customer always sees this)
```

### 9.1 Discount Priority Order
1. **Campaign Discount** (highest priority)
2. **Variant Discount** (if has_variants)
3. **Product Discount** (lowest priority)
- Only one discount applies at a time (the highest priority one).
- **Coupon Discount** is applied at the order level (not item level) after other discounts.

### 9.2 Campaign Discount Eligibility
All conditions must be true for campaign discount to apply:
- Campaign is active and not deleted.
- Current time is within campaign start and end dates.
- Product (or its category) is in campaign's applicable list.
- Current usage count < total usage limit.
- User's campaign usage count < max usage per user.

---

## 10. Inventory Valuation Rules (FIFO)

### 10.1 Valuation Method
- **FIFO (First In, First Out)** is the official and only inventory costing method.
- Each Batch stores its Cost Price permanently.
- COGS (Cost of Goods Sold) is calculated using FIFO.
- Historical Cost is never overwritten.

### 10.2 Profit Calculation
```
Gross Profit = Revenue - COGS

Revenue    = Quantity Sold × Selling Price
COGS       = FIFO-based deduction from oldest batches
Net Profit = Total Revenue - Total Expenses
```

**Example:**
```
Revenue = 15 pcs × 500 = 7,500 BDT
COGS   = 5,000 BDT (FIFO)
Profit = 2,500 BDT
```

### 10.3 Inventory Value
```
Inventory Value = Σ (Each Batch Remaining Qty × Batch Cost Price)
```
- Real-time inventory value is calculable from Batch data.
- Historical valuation reports are always reproducible.

---

## 11. Customer Return Rules

### 11.1 Eligibility
- Only Delivered Orders can be returned.
- Return Window is configurable (e.g., 7 days, 14 days, 30 days).
- Return Reason is mandatory.

### 11.2 Return Validation Rules
- **Order Ownership**: The return request user must own the order being returned.
- **Order Item Belonging**: The order item being returned must belong to the specified order.
- **Quantity Limit**: Return quantity cannot exceed the purchased quantity.
- **Full Return**: Full return type requires return_quantity to match the order item's quantity exactly.
- **Approval Quantity**: Approved quantity cannot exceed requested quantity. Approved quantity cannot be negative.
- **Refund Amount**: Refund amount must be non-negative.

### 11.3 Return Reasons
```
Item Damaged
Wrong Item Received
Not As Described
Quality Issue
Changed Mind
Other
```

### 11.4 Return Process
1. Customer initiates return request.
2. Return is reviewed and approved/rejected.
3. Returned items undergo inspection.
4. Based on inspection, stock is updated accordingly.

### 11.5 Exchange Request Rules
- Only Delivered Orders can be exchanged.
- **Same Product Only**: Exchange must be between variants of the same product.
- **Different Variant**: The new variant must be different from the old variant.
- **Variant Active**: The new variant must be active and not deleted.
- **Old Variant Intact**: The old variant must not be deleted.
- **Order Ownership**: Exchange user must own the order. Order item must belong to the order.
- Exchange quantity cannot exceed purchased quantity.

---

## 12. Return Inspection Rules

### 12.1 Inspection Outcomes
Every returned product is inspected and assigned one of three statuses:

| Status | Action |
|--------|--------|
| **Resellable** | Added back to Available Inventory at FIFO cost of original batch. |
| **Damaged** | Moved to Damage Inventory; Damage Report created. |
| **Rejected** | Returned to Customer; no stock change. |

### 12.2 Inspection Process
- Inspection must be performed by authorized staff.
- Inspection result is recorded with timestamp and inspector ID.
- Customer is notified of inspection outcome.

---

## 13. Supplier Return Rules

- Defective or incorrect products can be returned to the Supplier.
- Supplier Return deducts quantity from the specific Inventory Batch.
- A Supplier Credit Note can be generated.
- Supplier Return History is permanently preserved.

### 13.1 Supplier Return Reasons
```
Defective Product
Wrong Product
Expired Product
Damaged Product
Other
```

---

## 14. Damage Management Rules

### 14.1 Damage Tracking
- Damaged products are tracked separately from available inventory.
- Damage Entry requires a mandatory Reason.
- Damaged quantity is deducted from Available Stock.
- Damaged products cannot be sold.
- Damage History and Damage Reports are preserved.
- Damage deduction follows FIFO batch order.

### 14.2 Damage Reasons
```
Broken
Expired
Water Damage
Manufacturing Defect
Packaging Damage
Other
```

### 14.3 Damage Alert
- A Damage Alert is triggered when any Damage Entry is created.
- Admin and Inventory Staff are notified.

---

## 15. Lost / Missing Inventory Rules

### 15.1 Lost Inventory Detection
- When Physical Stock Count differs from System Stock, an investigation is required.
- Missing products are recorded as Lost Inventory.
- Lost Stock is deducted from Available Inventory.
- Lost Entry requires a mandatory Reason.
- Full Audit Trail is preserved.

### 15.2 Lost Reasons
```
Theft
Storage Error
Counting Error
Misplacement
Unknown
Other
```

> **Note:** "Storage Error" replaces any previous warehouse-specific terminology.

### 15.3 Lost Inventory Alert
- A Lost Inventory Alert is triggered when any Lost Entry is created.
- Admin and Inventory Staff are notified.

---

## 16. Stock Adjustment Rules

### 16.1 Adjustment Authorization
- Manual Stock Correction can only be performed by Authorized Users.
- All Adjustments are logged in the Audit Trail.
- Adjustment Reason is mandatory.
- Both Positive (increase) and Negative (decrease) Adjustments are supported.
- **Negative Stock Prevention**: Adjusted stock cannot be negative.

### 16.2 Adjustment Reasons
```
Physical Count Correction
Lost Product
Damaged Product
System Error
Initial Balance Correction
Other
```

---

## 17. Stock Audit Rules

### 17.1 Physical Count Process
- Periodic Physical Inventory Counts are scheduled.
- System Stock and Physical Stock are compared.
- Variance is recorded and, if needed, an Adjustment Entry is created.
- Audit History is permanently preserved.
- Audit Reports can be generated.

### 17.2 Audit Status
```
Scheduled → In Progress → Completed → Approved
```

---

## 18. Inventory Reservation Rules

### 18.1 Reservation Creation
- Only Confirmed Online Orders can create Stock Reservations.
- Reservation locks stock from Available pool.
- Reserved Stock is excluded from POS Sale availability.
- **Reservation Ownership**: The reservation user must match the cart owner.

### 18.2 Reservation Lifecycle
```
Active → ConvertedToSale (on Delivery)
Active → Released (on Cancel)
Active → Expired (auto-release after TTL)
```

### 18.3 Reservation Rules
- Order Cancel → Reservation Released, stock returns to Available.
- Order Delivered → FIFO deduction, Reservation marked ConvertedToSale.
- Expired Reservations are automatically released.
- Reservation History is permanently preserved.
- Reservation has an expiry TTL (configurable).
- Reserved quantity must be positive.

---

## 19. Approval Workflow Rules

### 19.1 Operations Requiring Approval
The following operations may require approval (configurable):
- Purchase Order
- Stock Adjustment
- Supplier Return
- Customer Refund
- Damage Entry
- Lost Entry

### 19.2 Approval Status
```
Pending → Approved → Completed
Pending → Rejected
Approved → Cancelled
```

---

## 20. Inventory Transaction Rules

### 20.1 Transaction Types
All Stock Movements are recorded as Inventory Transactions.

| Transaction Type | Description |
|-----------------|-------------|
| **PURCHASE** | Stock received from Supplier. |
| **POS_SALE** | Stock sold via POS. |
| **ONLINE_SALE** | Stock sold via Online Store (on Delivery). |
| **CUSTOMER_RETURN** | Stock returned by Customer (after inspection). |
| **SUPPLIER_RETURN** | Stock returned to Supplier. |
| **DAMAGE** | Stock marked as damaged. |
| **LOST** | Stock marked as missing. |
| **ADJUSTMENT** | Manual stock correction. |
| **RESERVATION** | Stock reserved for an order. |
| **RESERVATION_RELEASE** | Stock released from reservation. |
| **REFUND** | Financial refund transaction. |

### 20.2 Transaction Rules
- Every Transaction is linked to an Inventory Batch.
- Every Transaction has a Source Document reference (Invoice, Order, etc.).
- **Variant Consistency**: If a product_variant is specified in the transaction, it must belong to the specified product.
- Transactions can be reversed (Reverse Transaction supported).
- Transactions can never be permanently deleted.
- Historical Transactions can never be modified.
- **Source Types**: Manual (admin entry), Order (from sales order), Return (from return), System (auto-generated).

---

## 21. Inventory KPIs and Monitoring Rules

### 21.1 Stock Value
- Total Inventory Value = Σ (Remaining Qty per Batch × FIFO Cost per Batch)
- Real-time and historical stock value reporting.

### 21.2 Dead Stock
- Products with zero sales over a configurable period (e.g., 90 days).
- Dead Stock Report identifies products tying up capital.

### 21.3 Fast Moving Products
- Products with highest sales velocity over a defined period.
- Ranked by quantity sold per unit of time.

### 21.4 Slow Moving Products
- Products with low sales velocity relative to stock level.
- Helps identify overstocked items.

### 21.5 Top Selling Products
- Products ranked by total revenue or quantity sold.
- Configurable time range (daily, weekly, monthly, yearly).

### 21.6 Inventory Turnover
```
Inventory Turnover Ratio = COGS / Average Inventory Value
```
- Measures how efficiently inventory is being managed.
- Higher turnover indicates better inventory management.

---

## 22. Notification & Alert Rules

### 22.1 Low Stock Alert
- Triggered when Available Stock falls below the Low Stock Threshold.
- Notified: Admin, Inventory Staff.
- Channel: In-app notification + email (configurable).

### 22.2 Out Of Stock Alert
- Triggered when Available Stock reaches zero.
- Product is marked as "Out of Stock" in Online Store.
- Notified: Admin, Inventory Staff.
- Auto-disable purchase option for that product (configurable).

### 22.3 Damage Alert
- Triggered when a Damage Entry is created.
- Notified: Admin, Inventory Staff.

### 22.4 Lost Inventory Alert
- Triggered when a Lost Entry is created.
- Notified: Admin, Inventory Staff.

### 22.5 New Order Alert
- Triggered when a new Online Order is placed.
- Notified: Admin, Order Staff.

### 22.6 Return Request Alert
- Triggered when a Customer initiates a Return Request.
- Notified: Admin, Support Staff.

### 22.7 Notification Rules
- **Read Status Validation**: If a notification is marked as read, a read timestamp must be provided. Conversely, an unread notification cannot have a read timestamp.
- Notifications track: user, type, title, message, delivery channel, delivery status, sent_at, read_at.

---

## 23. Customer Management Rules

### 23.1 Customer Profile
- Every customer has a profile with: Name, Phone, Email, Address, Registration Date.
- Customer ID is unique and indexed.
- Customer Groups (Regular, Premium, Gold) supported.
- **Self-Referral Prevention**: A customer cannot refer themselves.
- **Address Ownership**: Default address must belong to the customer.
- All cached counters (total_orders, total_spent) must be non-negative.
- Wallet balance and loyalty points must be non-negative.

### 23.2 Customer Purchase History
- Full purchase history is viewable per customer.
- Includes POS and Online Store purchases.
- Cached total orders and total spent for quick display.

### 23.3 Customer Return History
- Full return history is viewable per customer.
- Includes return reasons, statuses, and refund amounts.

### 23.4 Customer Due Tracking
- Customer due (credit) amounts are tracked.
- Due payments are recorded against customer ledger.
- Customer-wise due report is available.

### 23.5 Customer Loyalty Program (Optional)
- Loyalty points earned on purchases.
- Points can be redeemed against future purchases.
- **Balance Calculation**: Earned points add to balance (balance_after = balance_before + points). Redeemed/expired points subtract from balance (balance_after = balance_before - points). Insufficient points prevent redemption.
- **Points Expiry**: Points can have an expiry date; expiry time must be in the future.
- Loyalty transaction history is preserved.

### 23.6 Wallet Balance
- Wallet supports credit and debit transactions.
- **Credit Validation**: balance_after = balance_before + amount.
- **Debit Validation**: balance_after = balance_before - amount. Insufficient balance prevents debit.
- Wallet balance cannot go negative.
- Wallet transactions can be: completed, pending, failed, reversed.

### 23.7 Address Validation
- **Geographic Hierarchy**: Division must belong to selected Country. District must belong to selected Division. Area must belong to selected District.
- **Latitude Range**: Must be between -90 and 90.
- **Longitude Range**: Must be between -180 and 180.

---

## 24. Payment Management Rules

### 24.1 Supported Payment Methods

| Method | POS | Online Store |
|--------|-----|-------------|
| **Cash** | Yes | No |
| **Card** (Credit/Debit) | Yes | Yes |
| **Mobile Banking** (bKash, Nagad, Rocket) | Yes | Yes |
| **Bank Transfer** | Yes | Yes |
| **Payment Gateway** (SSLCommerz, etc.) | No | Yes |

### 24.2 Payment Types

#### Cash
- Physical cash received at POS.
- Cash amount recorded and reconciled daily.

#### Card
- Card payments processed via POS terminal or payment gateway.
- Card type, brand, issuer masked for security.
- Card number and CVV are never stored.

#### Mobile Banking
- Supported gateways: bKash, Nagad, Rocket.
- Transaction ID from mobile banking is recorded.
- Payment verification supported.

#### Bank Transfer
- Bank transaction ID recorded.
- Manual verification process.

### 24.3 Payment Gateway & Method Validation
- **Method-Gateway Consistency**: A payment method must belong to the specified gateway.
- **Session-Order Consistency**: A payment session must belong to the specified order.
- **Currency Validation**: All currency codes must be valid ISO 3-letter codes.
- **Amount Validation**: Payment amounts must be positive.

### 24.4 COD (Cash on Delivery) Rules
- COD transactions must use the COD payment channel.
- If COD is collected, a collection timestamp is mandatory.

### 24.5 EMI Rules
- If EMI is enabled, EMI months and EMI amount are required.
- EMI bank can be specified for tracking.

### 24.6 Payment Fraud Detection
- Each payment tracks: risk level, risk title, fraud score.
- Fraud score is non-negative and cannot exceed 100.
- Payments can be flagged for manual review.

### 24.7 Payment Status Flow
```
Initiated → Processing → Authorized → Captured (Completed)
                            ↓
                         Failed
                         
Completed → Refunded (via RefundTransaction)
```

### 24.8 Partial Payment
- A single sale can have multiple partial payments (e.g., 50% Cash + 50% Card).
- Each partial payment is recorded as a separate transaction.
- Partial payments are supported for both POS and Online Store.

### 24.9 Due Payment
- Sales can be made on due (credit).
- Due amount is tracked in Customer Ledger.
- Due payment collected later is recorded against the original sale.
- Customer Due report is available.

### 24.10 Refund Payment
- Refunds can be processed against returned orders.
- Refund method can differ from original payment method (e.g., paid by card, refunded as cash).
- Full refund and partial refund are supported.
- Refund transaction is recorded in RefundTransaction table.
- Refund reason is mandatory.
- **Refund Overflow Prevention**: Total refunded amount cannot exceed the original payment amount.
- **Gateway Consistency**: The refund gateway must match the original payment gateway.
- **Status Validation**: Completed refunds require a refunded_at timestamp. Failed refunds require a failure_reason.

### 24.11 Payment Security Rules
- Sensitive payloads must be encrypted/masked.
- Never store raw card numbers.
- Never store CVV.
- All payment events are logged for audit (PaymentEventLog).
- Webhooks are verified, logged, and processed with idempotency keys.

---

## 25. Financial Control Rules

### 25.1 Revenue Tracking
- Revenue is recorded per sale (POS and Online).
- Revenue categorized by: Product Sales, Shipping Income, Other Income.
- Auto-generated accounting entries on Order Delivery.

### 25.2 Expense Tracking
- All business expenses are recorded.
- Expense categories: Product Purchase, Shipping Cost, Marketing Expense, Staff Salary, Platform Fee, Other Expense.

### 25.3 Profit Calculation
```
Gross Profit = Product Sales Revenue - COGS (FIFO)
Net Profit   = Total Revenue - Total Expenses
```
- Profit calculation is available daily, weekly, monthly, yearly.
- Real-time profit dashboard.

### 25.4 Account Category Management
- Predefined categories: Product Sales, Shipping Income, Refund Issued, Product Purchase, Shipping Cost, Marketing Expense, Staff Salary, Platform Fee, Other Income, Other Expense.
- **System Categories**: Predefined categories are marked as system categories and protected from deletion.
- **Category Consistency**: The transaction type (income/expense) must match the category's category_type.

### 25.5 Account Transaction Rules
- **Amount Rule**: All account transaction amounts must be positive.
- **Currency Validation**: ISO 3-letter currency code required.
- **Date Tracking**: Transactions have a transaction_date (for reporting) distinct from created_at.
- **Auto-Generated Entries**: When an order is delivered, auto-generated entries are created:
  - Income: Product Sales = order total
  - Income: Shipping Income = shipping cost
  - Expense: Product Purchase = Σ(item qty × purchase price)
- **Refund Entry**: When a refund is processed, an expense entry is created (Refund Issued category).

### 25.6 Refund Tracking
- Refund amounts are tracked per order and per customer.
- Refund is recorded as an expense (Refund Issued category).
- Refund reports are available.

### 25.7 Supplier Due Tracking
- Supplier due amounts are tracked per supplier.
- Payments to suppliers are recorded.
- Supplier-wise ledger is maintained.

### 25.8 Customer Due Tracking
- Customer due amounts are tracked per customer.
- Due collections are recorded.
- Customer-wise ledger is maintained.

---

## 26. Reporting Rules

### 26.1 Sales Reports
- Daily Sales Report
- Monthly Sales Report
- Product-wise Sales Report
- Category-wise Sales Report
- Brand-wise Sales Report
- Top Selling Products Report
- Customer Sales Report

### 26.2 Purchase Reports
- Purchase Report (by date, supplier)
- Product Purchase Report
- Supplier Report
- Top Suppliers Report

### 26.3 Inventory Reports
- Inventory Valuation Report
- Stock Report (current stock levels)
- Stock Adjustment Report
- Dead Stock Report
- Low Stock Report
- Stock Movement Report
- Batch Report
- Expiry Report
- Stock Aging Report

### 26.4 Financial Reports
- Profit & Loss Report
- Balance Sheet
- Cash Flow Statement
- Expense Report
- Tax Report
- Refund Report

### 26.5 Customer Reports
- Customer Ledger
- Customer Due Report
- Customer Purchase History
- Customer Return History

---

## 27. Audit & Compliance Rules

### 27.1 Stock Movement Traceability
- Every stock movement is recorded as an Inventory Transaction.
- Every transaction links to: Product, Batch, Source Document, Performing User, Timestamp.
- Full audit trail is available for any stock change.

### 27.2 Immutable Historical Records
- Historical inventory data can never be modified.
- Batch cost prices can never be overwritten.
- Inventory Transactions can never be edited.
- Deletion is strictly prohibited (soft delete only if required by law, with full audit log).

### 27.3 Transaction Immutability
- Transactions cannot be permanently deleted.
- If a correction is needed, a Reverse Transaction must be created.
- The original transaction remains in the system forever.

### 27.4 Reverse Transactions
- Any Inventory Transaction can be reversed.
- A reverse transaction creates a new transaction record with reference to the original.
- Reason for reversal is mandatory.
- Example: If a sale was made in error, a reverse sale transaction is created rather than deleting the original.

### 27.5 User Activity Logging
- All user actions are logged: create, update, delete, approve, reject, reverse.
- Log includes: User, Action Type, Module, Timestamp, IP Address, User Agent.
- Old and new data snapshots are preserved for update actions.
- Audit Logs are read-only and tamper-proof.

### 27.6 Compliance Rules Summary
| Rule | Enforcement |
|------|-------------|
| All stock movements traceable | Every transaction has full linkage |
| Historical records immutable | No update/delete on historical data |
| No permanent deletion | Soft delete + audit log |
| Reverse transactions supported | Dedicated reverse transaction type |
| User activity logging | Complete audit trail for all actions |

---

## 28. Staff Roles & Permissions

### 28.1 Role Definitions
| Role | Description |
|------|-------------|
| **Store Superuser** | Full system access with all permissions. |
| **Store Admin** | Full access except cannot manage other staff. |
| **Store Manager** | View products, orders, inventory, customers, sales reports. |
| **Inventory Staff** | View and adjust inventory; view shipments. |
| **Order Staff** | View, edit, cancel orders; manage orders; view customers. |
| **Support Staff** | View orders and customers (read-only). |
| **Marketing Staff** | Manage campaigns, coupons, banners; view reports. |
| **Accounts Staff** | View accounts, add/edit transactions, view reports. |

### 28.2 Permission Auto-Assignment
- When a staff role is set, permissions are automatically synced.
- **Permission Reset**: Before applying new role permissions, all existing permissions are reset to False to prevent privilege leakage.
- Permission granularity includes: products (view, add, edit, delete, approve), orders (view, edit, cancel, manage, process_refunds), inventory (view, adjust), shipments (view, manage), customers (view, edit), marketing (campaigns, coupons, banners), reports (sales, financial, export, transactions), accounts (view, add, edit), fraud management, payment logs, settings, staff management, audit logs.

---

## 29. Fraud Prevention Rules

### 29.1 Fraud Rule Types
| Type | Description |
|------|-------------|
| **IP** | Block or flag orders from specific IPs. |
| **Device** | Flag known fraudulent devices. |
| **Order** | Flag orders matching suspicious patterns (e.g., high value, multiple attempts). |
| **Payment** | Flag payment anomalies. |
| **Custom** | User-defined custom rules. |

### 29.2 Risk Scoring
- Each fraud rule has a risk score (0-100).
- Risk scores are cumulative across matching rules.
- Orders and payments exceeding configurable risk thresholds are flagged for manual review.

### 29.3 IP Blacklist
- Blocked IPs are tracked with reason and expiry.
- Expired IP blocks are automatically detected (blocked_until < now).
- Active blacklist entries prevent order placement from those IPs.

---

## 30. Courier & Shipment Rules

### 30.1 Shipment Status Flow
```
Pending → Pickup Requested → Picked Up → In Transit → Delivered
                                                     → Failed
                                                     → Returned
```

### 30.2 Shipment Validation
- **Delivered**: Requires delivered_at timestamp.
- **Failed**: Requires failed_at timestamp.
- **Returned**: Requires returned_at timestamp.
- **In Transit**: Requires in_transit_at timestamp.
- Tracking numbers are unique and indexed.
- Shipment responses from courier APIs are stored in JSON.

---

## 31. Tax Rules

### 31.1 Tax Configuration
- Tax can be configured per country, division, or district.
- **Default Tax**: Only one default tax configuration per country.
- **Tax Priority**: Tax configurations have priority; highest priority applies.
- **Tax Types**: VAT, GST, Sales Tax, Custom.
- **Tax Percentage**: Must be between 0 and 100.
- **Applicability**: Tax can apply to products, shipping, or digital products independently.
- **Geographic Validation**: Division must belong to selected Country. District must belong to selected Division.

---

## 32. Campaign & Promotion Rules

### 32.1 Campaign Validation
- **Date Validation**: Campaign end time must be after start time.
- **Percentage Discount**: Cannot exceed 100.
- **Maximum Discount**: If set, cannot be negative.
- **Usage Limit**: Current usage count cannot exceed total usage limit.
- Campaign can target specific products and/or categories.

### 32.2 Campaign Status
```
Active (is_active=True, not deleted, within date range) → Running
Inactive (outside date range or is_active=False)
```

### 32.3 Banner Rules
- **Link Type Consistency**: Banner link_type must match the linked object:
  - 'product' requires a linked_product.
  - 'category' requires a linked_category.
  - 'campaign' requires a linked_campaign.
  - 'url' requires a button_url.
  - 'none' requires no linked object.
- **Single Link Rule**: A banner can only link to one object type (product OR category OR campaign, not multiple).
- **Date Validation**: Banner end time must be after start time (if both provided).

---

## 33. Cart & Checkout Rules

### 33.1 Cart Validation
- **Financial Consistency**: Cart total must equal subtotal + tax_amount - discount_amount.
- All financial fields (subtotal, tax_amount, discount_amount, total_amount) must be non-negative.
- Cart has an optional expiry; expired carts should be cleaned up.

### 33.2 Cart Item Rules
- **Unique Product**: A product can only appear once in a cart (for non-variant products).
- **Unique Variant**: A product variant can only appear once in a cart.
- **Variant-Consistency**: Cart item variant must belong to the selected product.
- **Discount Validation**: Applied discount cannot exceed the payable amount (subtotal + tax).
- **Quantity**: Must be positive.
- **Price Snapshot**: Prices are snapshotted at the time of adding to cart for consistency.

### 33.3 Coupon Application Rules
- **Unique Coupon Per Order**: A specific coupon can only be used once per order.
- **Coupon Ownership**: Coupon usage user must match order user.
- **Same Group Restriction**: Coupons in the same coupon_group cannot be combined.
- **Different Group**: Coupons from different groups can be combined.
- **Usage Limits**: Enforced per-coupon (total usage) and per-user (max_usage_per_user).

---

## 34. Core Inventory Tables (Single Source of Truth)

### 34.1 Core Tables
The following tables form the foundation of the inventory system:

| Table | Purpose |
|-------|---------|
| **InventoryBatch** | Stores each purchase batch with cost price, received qty, remaining qty. |
| **InventoryTransaction** | Records every stock movement with type, quantity, batch reference. |
| **StockReservation** | Manages stock locks for confirmed online orders. |
| **StockAudit** | Tracks physical vs system stock comparison and audit history. |
| **StockAdjustment** | Records manual stock corrections with reason and authorization. |
| **DamageReport** | Tracks damaged inventory with reason and quantity. |
| **ReturnRecord** | Records return inspection outcomes and stock disposition. |

### 34.2 Core Rules
1. The **Product Table** displays summary stock data only (derived from batches).
2. Actual stock is always determined from **InventoryBatch** and **InventoryTransaction**.
3. Historical cost is never overwritten.
4. Profit calculation is always based on FIFO cost from batches.
5. Product stock can never be updated directly.
6. Stock changes **only** through these seven channels:

```
Purchase  →  Stock Increases
Sale      →  Stock Decreases
Return    →  Stock Increases (Resellable)
Damage    →  Stock Decreases
Lost      →  Stock Decreases
Reservation → Stock Locks (temporary)
Adjustment → Stock Correction (+/-)
```

7. **InventoryBatch + InventoryTransaction** are the ultimate Single Source of Truth.

---

## 35. Enterprise Inventory Flow

```
Supplier
    ↓
Purchase
    ↓
Inventory Batch
    ↓
Available Stock
    ↓
  ┌─────────────────┬──────────────────┐
  │                                   │
POS Sale                        Online Order
  │                                   │
  ↓                                   ↓
Transaction                     Reservation
  │                                   │
  └──────────────┬────────────────────┘
                 │
              Return
                 │
          ┌──────┴───────┐
          │              │
      Resellable      Damaged
          │              │
          ↓              ↓
      Available     Damage Report
          
                 ↓
        Inventory Transaction
                 ↓
      Reports & Profit Analytics
```

### 35.1 Data Flow Rules
```
Supplier → Purchase → InventoryBatch (Cost + Qty)
    ↓
InventoryBatch → POS Sale → FIFO Deduction → InventoryTransaction
    ↓
InventoryBatch → Online Order → Reservation → Delivery → FIFO Deduction → InventoryTransaction
    ↓
Customer Return → Inspection:
    → Resellable → Available Stock (via Transaction)
    → Damaged → DamageReport
    → Rejected → Return to Customer
    ↓
Lost/Theft → Lost Entry → Stock Deduction → InventoryTransaction
    ↓
Audit → Variance Found → StockAdjustment → InventoryTransaction
```

---

## 36. System Architecture Principles

### 36.1 Single Store Design
- This system is designed for a **Single Store** with POS + Inventory + Online Store.
- No Warehouse Transfer, Transfer Status, In Transit, or multi-warehouse concepts.
- All inventory resides in one physical location (the store).

### 36.2 Soft Delete Pattern
- All major entities (products, brands, categories, campaigns) support soft delete.
- **ActiveManager**: Provides a default queryset that filters out soft-deleted records (is_deleted=False).
- **AllObjectsManager**: Provides access to all records including deleted ones.
- Soft delete preserves referential integrity and audit history.

### 36.3 Production Grade Principles
| Principle | Implementation |
|-----------|---------------|
| **Single Source of Truth** | InventoryBatch + InventoryTransaction |
| **Immutability** | Historical data never modified or deleted |
| **Traceability** | Every stock change traceable to user, time, and source document |
| **FIFO Costing** | Mandatory, system-wide |
| **No Direct Stock Edit** | All changes through authorized channels only |
| **Audit Readiness** | Complete audit trail for compliance |
| **Data Integrity** | Database constraints enforce business rules at DB level |

### 36.4 Inventory Change Channels (Summary)
All inventory changes must occur exclusively through one of these seven channels:

| # | Channel | Direction | System Impact |
|---|---------|-----------|--------------|
| 1 | **Purchase** | Stock In (+) | Creates InventoryBatch |
| 2 | **Sale** | Stock Out (-) | FIFO deduction from batches |
| 3 | **Return** | Stock In (+) | Resellable items back to batches |
| 4 | **Damage** | Stock Out (-) | Deduction + DamageReport |
| 5 | **Lost** | Stock Out (-) | Deduction + Lost Record |
| 6 | **Reservation** | Lock (temporary) | StockReservation created |
| 7 | **Adjustment** | +/- | Manual correction with reason |

---

*Document Version: 2.1 — Enterprise Edition (with Model-Level Logic)*
*Last Updated: June 2026*
*System Type: Single Store POS + Inventory + Online Store*