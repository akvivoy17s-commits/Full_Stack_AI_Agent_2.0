# E-commerce / Shopping Website Engineering Playbook

## 1. How this document should be used
This is a domain playbook grounded in the supplied `shopping-main` reference source. It explains the reference's observed routes and stack, then gives safer, more deterministic engineering rules for generating a comparable store. It is not a claim that every observed implementation detail is a production best practice. The actual target repository, installed package versions, existing schema/rules, diagnostics, and tests always win. Do not copy project-specific credentials, host URLs, payment details, image assets, branding, or private configuration from a reference project.

Keep these categories separate:
- **Observed in reference**: a fact visible in the supplied source.
- **Recommended implementation**: a safer engineering pattern for a newly generated project.
- **Optional extension**: generate only when the user requests it or the selected stack can truly support it.

## 2. Reference stack and source structure (observed)
The reference is a React single-page application built with Vite. Its package manifest uses React 19, React DOM 19, React Router 7, Firebase 12, Lucide icons, and a set of build/deploy tools. The API server is Express 5. It also uses Firebase Admin, Cloudinary, Multer, Sharp, dotenv, and web-push. Cloudflare/Wrangler deployment files are present. Do not assume these exact versions will exist in another generated project; read that project's manifest and lockfile.

Relevant source areas:
- `src/App.jsx`: route composition with React Router.
- `src/pages/Home/Home.jsx`: product discovery, category selection, search, product paging.
- `src/pages/Products/ProductDetails.jsx`: product details, image selection/share, wishlist state, reviews, and a delivered-order check before a user may review.
- `src/pages/Cart/Cart.jsx`: signed-in cart under `users/{uid}/cart`, live Firestore updates, quantity changes and subtotal calculation.
- `src/pages/BuyNow/BuyNow.jsx`: Buy Now / cart checkout path, saved addresses under `users/{uid}/addresses`, address fields, payment method selection and a UPI reference/UTR field.
- `src/pages/Wishlist/Wishlist.jsx`: wishlist under `users/{uid}/wishlist` (the visible implementation contains commented older code; inspect active code before drawing behavior conclusions).
- `src/pages/Address/Address.jsx`: address book page.
- `src/pages/Orders/Orders.jsx`: user-filtered orders and normalized delivery timeline statuses.
- `src/pages/Addproduct/Addproducts.jsx`: admin product create/update UI; it sends a Firebase ID token to the API and supports up to four images in the form.
- `src/pages/Adminorder/Adminorder.jsx`, `src/pages/Admin/Admin.jsx`, `src/pages/SuperAdmin/SuperAdmin.jsx`: operational/admin screens.
- `backend/firebase.js`: browser Firebase initialization, Auth, Firestore and optional Firebase Messaging.
- `backend/firebaseAdmin.js`: server Firebase Admin initialization; requires server-side Firebase service-account environment variables.
- `backend/server.mjs`: Express routes, Firebase-token/admin middleware, product CRUD, Cloudinary uploads and profile-image transformation.

Observed React Router paths include `/`, `/login`, `/product/:id`, `/pro-details`, `/cate/:categoryName`, `/cart`, `/wish`, `/buy/:productId`, `/buy`, `/address`, `/orders`, `/profile`, `/admin`, `/add-pro`, `/ad-order`, and `/super-admin`. When generating a new app, use one canonical route per concept unless an explicit backwards-compatibility alias is required; avoid duplicate routes that render the same page without a reason.

The reference uses a hybrid data flow: browser Firebase SDK operations are used for some shopper data, while protected Express endpoints handle admin product operations and uploads. Preserve this design only when deliberately requested and when complete Firebase security rules and server authorization are implemented. Prefer a clearly documented single source of truth per resource; do not casually mix browser writes and backend writes to the same records.

## 3. Required feature map for a complete comparable store
Generate a coherent, connected experience, not isolated mock screens. For the exact scope requested, plan these capabilities:

### Public storefront
1. Home/storefront with clear navigation, category entry points, search, featured/new products, responsive product cards, and useful empty/loading/error states.
2. Catalog/category pages with search, category filter, sort, stock/availability filter only when supported, and pagination or infinite loading. Preserve query/filter state in URL parameters where practical.
3. Product details with image gallery, title, brand/SKU if present, current and compare-at price if supplied, stock/variant selection, quantity bounds, delivery information only when known, and related products if real relationships exist.
4. Accessible responsive layout for mobile, tablet and desktop, with keyboard focus, meaningful alt text, touch-friendly controls, and reduced-motion support.

### Shopper account and saved data
5. Login/register/sign-out and stable auth-loading states. Redirect unauthenticated shoppers to the intended destination and return them there after login.
6. Persistent cart with add/remove/update quantity, clear-cart when appropriate, empty state, and cross-refresh persistence. A guest cart in local storage is optional; merge it deliberately on sign-in and do not duplicate items.
7. Wishlist save/remove, scoped to the current account. Never trust a client-supplied user ID; derive identity from verified auth.
8. Address book with add/edit/delete/select-default validation and ownership checks. Avoid exposing another customer's address.
9. Profile data and order history. Order detail must be accessible only to its owner and authorized admins.
10. Checkout that supports both Buy Now and cart flows through one shared domain service rather than duplicating business rules.

### Order, inventory and operations
11. Admin product/category management, validation, images, active/inactive status, inventory and a clear result after save.
12. Admin order queue, order details, status transition actions, filtering and traceable changes. A shopper must never be able to change price, payment status, owner, or admin-only fulfillment state.
13. Product reviews only when requested/supported. Verify eligible purchase server-side, allow one review per qualifying purchased product if that is the policy, validate rating/body, and expose only approved reviews publicly. Do not trust client `verifiedPurchase`, `status`, `role`, or `userId` fields.
14. Payment, email, push notifications, coupons, shipping provider, analytics and refunds are separate integrations. Do not claim these features work until provider configuration, API calls, webhook/signature verification, error handling and tests are in place.

The reference has separate admin and super-admin pages. For a new app, define role permissions explicitly. Add a super-admin role only if the user needs cross-store/system administration; do not create a second privileged role with no clear capability boundary.

## 4. Recommended canonical data model
Adapt physical names to the selected database, but keep field meanings stable across the UI, API and persistence layer.

- **User**: id, normalized email, display name, auth-provider identifier, role (`customer`/`admin`, plus `super_admin` only if justified), created/updated timestamps. Passwords must never be stored in plaintext; with Firebase Auth, do not invent a second password store.
- **Category**: id, name, slug (unique), status, sort order, timestamps.
- **Product**: id, name/title, slug/SKU where useful, description, brand, categoryId, price in integer minor units where currency rules require it (or a precise Decimal type), currency, compareAtPrice when supplied, image URLs/asset IDs, stock/availability, active status, timestamps.
- **Cart / CartItem**: derived owner/user id, productId, quantity, selected variant if needed, timestamps. Store product identity/quantity; re-read current price and stock before checkout. Cart data is not an authoritative price quote.
- **WishlistItem**: owner/user id, productId, createdAt. Enforce a per-user uniqueness constraint for the same product.
- **Address**: owner/user id, recipient, phone, address lines, city, region/state, postal code, country, default flag, timestamps. Snapshot the chosen address onto the order when purchased so later address edits do not rewrite history.
- **Order**: id, userId, immutable item/price snapshots, address snapshot, subtotal, shipping/tax/discount totals where applicable, grand total, currency, order status, payment status, timestamps and status history.
- **OrderItem**: orderId, productId reference plus product name/SKU snapshot, unit price snapshot, quantity, line total, selected variant. Usually create only through checkout; do not expose unrestricted generic CRUD for items.
- **Payment** (only when an actual payment integration exists): provider, provider transaction/reference, internal order, amount/currency, pending/succeeded/failed/refunded state, idempotency key and verified timestamps. Never store card data or payment secrets.
- **Review** (only when review workflow is supported): productId, userId, rating 1–5, text, moderation status, timestamps. Purchase eligibility is calculated/verified server-side; public queries return approved records only.
- **FileAsset** (for uploads when needed): owner or target resource, validated content type, byte size, storage key, URL strategy, timestamps. Avoid exposing private objects through a public bucket by default.

Use foreign keys/indexes or Firestore document/rules/indexes appropriate to the selected database. Enforce uniqueness and ownership in the database/rules/service layer where possible; frontend checks are convenience only. For SQL stores, use migrations. For Firestore, design collection paths and security rules together with the query shapes.

## 5. Critical shopper flows (implement and verify end-to-end)

### Product discovery
- Read active/public products only.
- Use stable ordering and cursor-based pagination for large catalogs; do not fetch the entire collection for every page.
- Debounce search if it triggers network calls. Reset cursor when search/category/sort changes.
- Handle product image fallback, malformed optional fields, sold-out items, and missing product IDs.
- Use a canonical field contract (`name`, `price`, `images`, `categoryId`, `stock`, `createdAt`) or a deliberate migration adapter. Do not scatter fallbacks for `image`, `imageUrl`, `imageUrls`, `images`, `price`, `sellingPrice`, and `salePrice` throughout every component without a normalization boundary.

### Cart and price integrity
- Validate quantity as a positive integer and not above available stock.
- Compute display subtotal consistently from normalized item data; format currency with the selected locale/currency.
- Treat displayed totals as estimates until checkout.
- At checkout the server must reload product price/availability, verify requested quantities, calculate all line totals/tax/shipping/discounts, and persist the immutable order snapshots.
- Prevent overselling with a database transaction/conditional stock update. If stock changed, return a specific conflict and keep the cart contents visible for correction.
- Make checkout idempotent. A double-click, refresh, retry or provider callback must not create duplicate orders/charges.
- Never accept grand total, unit price, userId, payment status or role as trusted values from the browser.

### Checkout/payment
- Validate recipient/address fields on both client and server. Never log full address/payment references unnecessarily.
- Create a pending order and payment intent in a well-defined transaction/workflow; do not mark paid because the browser returned to a success page.
- Payment state becomes successful only after a verified provider response/webhook, with signature verification, amount/currency/order matching, replay protection and idempotent processing.
- If using manual UPI/UTR reference, describe it honestly as a manual verification workflow: validate format, keep order pending, restrict proof/review to authorized staff, and do not claim automatic bank verification. The reference contains a UPI method/UTR UI, which by itself does not prove payment integration.
- Support cancellation/refund rules only when their state transitions and payment-provider behavior exist. Preserve an audit trail.

### Auth and authorization
- Verify Firebase ID tokens on every protected API request if Firebase Auth is selected. On other stacks use the chosen server session/token verification.
- Load the trusted role from server-side storage/claims. Never infer admin status from a route, hidden button, email string in client code, or request body.
- Enforce customer ownership for cart, wishlist, addresses, orders and payment details on every read/write. Unauthorized cross-user access should not reveal record existence.
- Protect admin product mutation and order status transition endpoints server-side. Frontend route guards are additional UX only.
- If using the Firebase browser SDK for direct reads/writes, write and test Firestore rules for each collection/subcollection, including nested `users/{uid}/cart`, `users/{uid}/wishlist` and `users/{uid}/addresses`. Admin operations should be protected by rules and/or trusted backend checks. Admin SDK bypasses client security rules, so server authorization remains mandatory.

### Uploads and media
- Verify auth/role before accepting protected product uploads.
- Set explicit file-count, file-size, decoded-pixel limits, accepted image types, extension/MIME/signature checks, and safe error responses. Never trust the browser `Content-Type` alone.
- If image processing uses Sharp, apply pixel/dimension limits and convert to a safe web format. Use random/immutable storage names and remove abandoned assets when product changes/deletes.
- Keep Cloudinary API secrets or storage service credentials server-side only. Do not hardcode production API hosts or credentials in source; use a documented environment variable with a local-safe default only when appropriate.

## 6. Reference-specific implementation lessons and cautions
Observed patterns that can inform feature requirements:
- Home uses categories, newest-first product fetching and cursor pagination.
- Cart uses a user-specific Firestore subcollection and listens for updates.
- Address data is stored under the authenticated user's address subcollection.
- The product page contains review state and checks whether the current user's order includes a delivered product before enabling review.
- The Express service verifies a Firebase token and checks the user's server-side Firestore role before admin product CRUD. Product images are uploaded through Cloudinary, and profile images are resized/converted with Sharp.
- The Orders UI recognizes status spellings such as placed, confirmed, packed, shipped, out-for-delivery, delivered and cancelled. A new implementation should define one canonical enum and migrate/normalize legacy states at an explicit boundary.

Cautions:
- The project has both browser Firestore access and Express API paths. Do not reproduce this split without corresponding Firestore rules and consistency tests.
- Source components tolerate several alternative product image/price field names and order status aliases. For a new implementation, define one canonical schema and normalize older data once in an adapter.
- The frontend admin product form has an environment-based API URL and a hard-coded fallback host. Generated projects should prefer the selected project's documented environment contract and must never inherit a reference host by accident.
- Do not reuse Firebase project configuration, service-account material, Cloudinary values, public asset paths, brand names or deployed URLs from the reference. Generate safe `.env.example` placeholders, never copy live secrets.
- The repository's README is generic Vite boilerplate; derive behavior from source/manifests/tests rather than treating that README as the app specification.

## 7. Responsive design and interaction quality
Use a consistent spacing/type/color token system. Store cards should maintain image aspect ratio and aligned price/action placement. On mobile, collapse navigation safely, keep search/category filters reachable, use a single-column or compact grid based on width, and prevent sticky cart/checkout controls from covering content. Provide visible focus rings, semantic button/link elements, labels/errors tied to inputs, keyboard operability, sufficient contrast and `prefers-reduced-motion` support. Avoid using `div` click handlers for primary actions. Use real route destinations and preserve browser back/forward behavior.

Every control must be wired: search changes results, filters actually filter, sort changes order, pagination loads a distinct next page, cart quantity updates persist, remove buttons remove items, checkout validates and submits, address saves, wishlist toggles, product forms save through the real API, and admin order status changes persist through an authorized endpoint. Use loading, no-results, empty, success, recoverable error and retry states. Do not use `alert()` as the only interaction pattern for a polished store.

## 8. Test matrix before claiming completion

### Static/build
- Check package scripts/lockfile and run the selected install/build/lint/typecheck/test commands.
- Validate route imports, module resolution, missing assets, broken links, JSX/TSX syntax and environment contract.
- Confirm every page is reachable through navigation and direct URL refresh works under the chosen hosting rewrite configuration.

### Unit/integration
- Product normalization, currency rounding/formatting, price totals and quantity bounds.
- Search/filter/sort/pagination and changes that reset the cursor.
- Invalid product, sold-out product, unavailable product and malformed API response.
- User scoping for cart, wishlist, address, order and payment reads/writes.
- Customer cannot create/update/delete products, promote roles, set prices, mark orders paid, or alter order status.
- Checkout checks current price/stock server-side; concurrent purchase cannot oversell; duplicate requests are idempotent.
- Payment webhook rejects invalid signatures, mismatched amount/currency, unknown orders and replayed event IDs.
- Upload rejects too-large, wrong MIME/signature, too many files and unauthorized upload; failures clean up temporary buffers/assets.
- Review requires qualifying delivered purchase if that is the policy; client cannot self-assert verification or approval.

### Browser end-to-end (Playwright or the project's supported browser tool)
1. Anonymous visitor browses category, searches/sorts, opens a product and handles an unavailable item.
2. Shopper signs in, adds items, changes quantity, refreshes and confirms cart persistence.
3. Shopper saves an address, checks out, sees a pending/payment state accurately, then sees an order with correct snapshot totals.
4. Shopper cannot open another user's cart/order/address or admin screens.
5. Admin adds/edits/deactivates a product with images and updates an order through allowed transitions.
6. Empty catalog, API failure, invalid form, expired auth and out-of-stock conflict display recoverable messages.

### Completion contract
Report each required feature/check as `passed`, `failed`, `blocked`, or `not run`. `Complete` is allowed only when every mandatory feature is implemented and its required automated checks passed. If payment credentials, Firebase rules, a database service, browser automation or deployment access is unavailable, mark that integration unverified and say exactly what is missing; do not substitute a fake success state.

## 9. Stack adaptation and scaffold compatibility
- **Important current-scaffold constraint**: the bundled generic checkout/payment scaffolds for several generated SQL backends use `Order.status = pending` and later set it to `paid` after verified payment. Keep `paid` as a supported value for that contract. A cleaner production domain model separates fulfillment status and payment status, but do not add that separation to the generated schema alone: migrate the checkout service, payment webhooks, serializers, admin transitions and tests together, or the integration will fail at runtime. Treat this as an explicit future architecture upgrade, not a cosmetic field rename.
- **React + Firebase/Firestore**: React Router pages, shared product/cart/address/order services, Auth state subscription cleanup, Firestore rules, composite indexes as needed, and batched/transactional writes where supported. Avoid uncancelled listeners and duplicate subscriptions.
- **React/Vue/Angular/Svelte + SQL backend**: frontend API client with typed DTOs, backend validators, ownership-aware services, migrations/foreign keys, indexes and SQL transactions. Order and payment mutations belong on server.
- **Express/NestJS/FastAPI/Django/Spring**: apply the same auth, validation, ownership, checkout and state-transition contracts through the selected framework's idioms. Do not add a second framework or change the selected stack just because the reference uses Express/Firebase.
- **No backend / frontend-only mode**: clearly label cart/checkout as demo/local-only, don't advertise secure multi-user persistence or real payment acceptance, and list gaps. A production checkout with trusted inventory, orders and payment confirmation requires a trusted backend or a properly configured managed backend.
