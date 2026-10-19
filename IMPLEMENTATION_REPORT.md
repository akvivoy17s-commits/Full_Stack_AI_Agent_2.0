# E-commerce Reference Knowledge & Generation Update

## Scope
This is a **changed-files-only patch** for the supplied `fullstack_ai_agent(1).zip`. The supplied `shopping-main.zip` was inspected as a read-only reference. The patch translates features and implementation lessons visible in that source into retrievable knowledge, better planner/UI hints, and a fuller e-commerce project specification. It does not copy the reference site's credentials, Firebase config, deployed endpoint, brand assets, or production URLs.

## What changed

### 1. New reference-grounded engineering guide
Added `backend/knowledge/guides/ecommerce_shopping_reference_guide.md`. It contains:
- Observed source stack and routes (React/Vite, React Router, Firebase Auth/Firestore, Express, Firebase Admin, Cloudinary, Multer, Sharp).
- Observed feature paths for product discovery, product details, wishlist, saved addresses, cart, checkout/Buy Now, orders, admin product management and admin order screens.
- A recommended canonical data model and end-to-end flow specifications.
- Security notes for owner-scoped user data, admin authorization, inventory and price integrity, transactions/idempotency, payment webhooks, image uploads and Firestore rules.
- A concrete automated test/browser-E2E checklist and a truthful completion contract.
- Explicit differences between source-observed behavior and production recommendations. The guide notes that the reference UI's UPI/UTR input is not proof of an automatically verified payment integration.

### 2. Knowledge is actually injected into model tasks
Updated `backend/knowledge/guide_retriever.py` to detect e-commerce/shopping/cart/checkout/wishlist/order/admin/inventory terms and allow the guide in frontend section and repair tasks. Retrieval remains bounded by the existing context budget; it does not inject the whole guide into every prompt.

### 3. Better planning and page-level instructions
Updated `backend/agent/prompts.py` with e-commerce-aware planning constraints and per-page hints for catalog, product detail, cart, wishlist, address book, checkout, order history, and admin product/order tasks. These hints require actual interactions, loading/error/empty states, server-trusted price/stock, access control, and honest payment status.

### 4. More complete e-commerce spec defaults
Updated `backend/spec/templates.py` so e-commerce specs include category browsing, wishlist, address book, profile, admin product/inventory and admin order management, as well as a broader end-to-end feature checklist. Added owner-scoped `CartItem`, `WishlistItem` and `Address` entities when authentication is enabled. For unauthenticated storefronts, those personal-data entities are omitted instead of being accidentally converted to public records.

Generic order mutation is admin-only in the spec. Customer checkout remains the dedicated `/api/checkout` workflow; customers should not be able to modify their own order total, role, payment result, or fulfillment state through generic CRUD.

`SPEC_VERSION` was incremented so persisted specs are rebuilt against the new defaults.

### 5. Extra service-level protection
The generated Python CRUD service template now re-checks admin-only writes even when service helpers are called outside the HTTP router. For owner-scoped records, cross-user attempts still get a non-disclosing 404; a rightful customer attempting an admin-only order mutation receives 403. Checkout continues to own customer order creation.

### 6. Regression tests
Updated tests to validate the added retriever entry, e-commerce routes/features, owner-scoped entities, unauthenticated-store behavior, admin-only generic order mutations, and current generated Python service behavior.

## Validation performed

Focused command:

```powershell
python -m compileall -q backend tests
python -m pytest -q tests/test_guide_retriever.py tests/test_spec_engine.py tests/test_payment_owner_scope.py tests/test_backend_gen_fastapi.py
```

Result: **65 passed, 3 skipped**. Python compilation completed successfully.

## Verification limits
The **entire repository suite is not certified green**. A full test run exceeded the available time limit. A broader run also revealed existing/environment-related failures outside this patch's scope, including a 3D runtime test expecting `MutationObserver` in `templates/animation/three-hero.js`, Django test imports failing with `ModuleNotFoundError: django.db` / `'django' is not a package`, and a generation pipeline test failing with a Pydantic `ValidationError`. Those failures have not been represented as passing or fixed by this commerce patch. Browser end-to-end tests and a real provider-backed payment checkout were not run.

## Install
1. Back up the current project folder.
2. Extract this ZIP into the root of `fullstack_ai_agent`, preserving the archive paths, and overwrite matching source/test files.
3. Run the focused command above from the project root.
4. Restart the agent backend and generate a small online store with catalog, cart, wishlist, checkout, address book, order history and admin order management. Use Verify/Build and inspect the generated report; do not mark real payments as verified without provider credentials and webhook tests.
