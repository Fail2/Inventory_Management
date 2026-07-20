# Inventory Management System

A Django-based multi-role e-commerce and inventory platform with a buyer storefront, a supplier fulfillment dashboard, and an admin control panel — built around passwordless (email OTP) authentication and a strict, auditable order-status workflow.

**Repository:** [https://github.com/Fail2/Inventory_Management.git](https://github.com/Fail2/Inventory_Management.git)

**Live deployment:** [https://inventory-management-hl9y.onrender.com](https://inventory-management-hl9y.onrender.com)

**Admin login:** [https://inventory-management-hl9y.onrender.com/accounts/admin-login/](https://inventory-management-hl9y.onrender.com/accounts/admin-login/)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [Deployment (Render)](#deployment-render)
- [External Services Used](#external-services-used)
- [Deployment Challenges & Solutions](#deployment-challenges--solutions)
- [Project Structure](#project-structure)

---

## Overview

The system serves three distinct roles from one Django project:

| Role | Entry point | Capability |
|---|---|---|
| **Buyer** | [Storefront](https://inventory-management-hl9y.onrender.com/accounts/buyer/home/) | Browse products, cart, wishlist, checkout, order history, self-service profile editing |
| **Supplier** | [Supplier dashboard](https://inventory-management-hl9y.onrender.com/accounts/supplier/home/) | View orders assigned to them, mark shipped orders as delivered |
| **Admin** | [Admin login](https://inventory-management-hl9y.onrender.com/accounts/admin-login/) | Manage products, categories, seasons, buyers/suppliers, and the full order lifecycle |

Buyers and suppliers authenticate passwordlessly via a one-time email code (no passwords stored for these roles). Admin access uses Django's standard superuser authentication.

## Features

- **Passwordless OTP login** for buyers and suppliers (email verification code, auto-registers on first login)
- **Hierarchical order workflow**: `pending → approved → shipped → delivered`, with role-based transition rules (admin can advance one step at a time and never directly to *delivered*; only the assigned supplier can mark an order *delivered*)
- **One checkout = one order** with multiple line items (`OrderGroup` / `OrderItem`), rather than one row per product
- **Stock management**: reserved at checkout, automatically restored if a pending order is deleted
- **Order history integrity**: deleting a product from the catalog never destroys past orders that included it — the order/line item persists with a "Product no longer available" fallback, and historical totals stay accurate (price/quantity are snapshotted at order time)
- **Live cart** with a "View Cart" affordance that replaces "Add to Cart" once an item is already in the session cart
- **Wishlist**, real-time client-side search/filtering (no submit button) across product and order listings
- **Self-service profile editing** ("My Info") for buyers and suppliers, with email locked against tampering
- **Consistent design system**: a single shared set of CSS custom properties (colors, radii, shadows) used across the buyer storefront, admin panel, and authentication pages

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Django 5.2 (Python 3.12) |
| Database (production) | PostgreSQL, hosted on [Neon](https://neon.tech) |
| Database (local dev) | SQLite (automatic fallback, zero configuration) |
| Media storage | [Cloudinary](https://cloudinary.com) |
| Transactional email | [Brevo](https://www.brevo.com), via `django-anymail` |
| Static file serving | WhiteNoise |
| App server | Gunicorn |
| Hosting | [Render](https://render.com) (free tier, Blueprint deployment via `render.yaml`) |

## Architecture

- **`accounts`** is the single Django app powering every role (models, views, and templates for buyer/supplier/admin all live here).
- **Auth model**: `CustomUser` (Django's `AbstractUser`) is used only for admin/superuser login. Buyers and suppliers are separate, password-less models (`Buyer`, `Supplier`) whose "session" is just two keys (`buyer_id` / `supplier_id`) stored in `request.session` after a successful OTP verification — not Django's `auth` login system.
- **Cart and wishlist** are stored entirely in the session (a plain dict keyed by product ID), not database tables — kept intentionally simple for a project at this scale.
- **Orders**: `OrderGroup` represents one checkout (buyer, delivery address, status); `OrderItem` represents one product line within it, with `unit_price` and `quantity` snapshotted at order time so historical totals never change even if the product's price changes later or the product is deleted (`on_delete=SET_NULL`).
- **Design tokens**: one shared partial, `accounts/templates/accounts/partials/design_tokens.html`, defines every color/radius/shadow as a CSS custom property and is `{% include %}`-ed into every page's `:root {}` block — including pages that don't share a common base template.

## Local Setup

Local development requires **zero environment variables** — sensible defaults (SQLite, console email backend, `DEBUG=True`) are used automatically.

1. **Clone the repository and create a virtual environment**
   ```bash
   git clone https://github.com/Fail2/Inventory_Management.git
   cd Inventory_Management
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   cd inventory_management
   python manage.py migrate
   ```

4. **Create an admin (superuser) account**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server**
   ```bash
   python manage.py runserver
   ```
   Visit `http://127.0.0.1:8000/`. OTP codes sent during buyer/supplier login are printed to the console (no real email is sent locally) since `EMAIL_BACKEND` defaults to Django's console backend when `DEBUG=True`.

## Environment Variables

None of these are required for local development. They only need to be set in a production-like environment (e.g., Render's dashboard).

| Variable | Purpose | Notes |
|---|---|---|
| `DJANGO_DEBUG` | `True`/`False` | Defaults to `True`. Must be explicitly set to `False` in production. |
| `DJANGO_SECRET_KEY` | Django's cryptographic secret key | **Required** when `DEBUG=False` — the app refuses to start without it. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hostnames | Defaults to `127.0.0.1,localhost`. Render's own hostname is auto-appended via `RENDER_EXTERNAL_HOSTNAME`. |
| `DATABASE_URL` | PostgreSQL connection string | If unset, falls back to local SQLite automatically. |
| `ANYMAIL_BREVO_API_KEY` | Brevo API key | Required for outbound email in production (see below). |
| `DEFAULT_FROM_EMAIL` | Sender address for OTP emails | Must be a sender verified in your Brevo account. |
| `CLOUDINARY_CLOUD_NAME` / `_API_KEY` / `_API_SECRET` | Cloudinary credentials | If unset, product images are stored on local disk instead (fine for local dev; not durable in production — see below). |

## Deployment (Render)

This project deploys via Render's **Blueprint** system, defined entirely in `render.yaml`, so most configuration is automatic.

1. **Push the repository to GitHub** (Render deploys from a connected Git repo).
2. **Create a Neon Postgres database** (see [External Services Used](#external-services-used)) and copy its connection string.
3. **In Render**, create a new Blueprint pointing at the repository — it will read `render.yaml` and provision the web service automatically.
4. **Set the following secrets** in the Render dashboard's Environment tab (these are intentionally excluded from `render.yaml` since it's committed to git):
   - `DJANGO_SECRET_KEY`
   - `DATABASE_URL` (the Neon connection string)
   - `ANYMAIL_BREVO_API_KEY`, `DEFAULT_FROM_EMAIL`
   - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
5. **Deploy.** The build process (`buildCommand` in `render.yaml`) installs dependencies, collects static files, and runs migrations — no shell access is needed at any point.
6. **Create the admin (superuser) account.** Render's free tier has no shell access, so this is done from a local machine against the live Neon database directly (Neon allows reliable external connections, unlike Render's own free-tier Postgres):
   ```bash
   DATABASE_URL="<your Neon connection string>" DJANGO_SECRET_KEY="<any value>" python manage.py createsuperuser
   ```
   Run this from `inventory_management/` with your virtual environment active. It only needs to be done once — the account persists in the database from then on.
7. **Note:** `autoDeploy` is set to `false` — after the initial deploy, new commits require a manual **Deploy latest commit** click from the Render dashboard. Saving changed environment variables still triggers a redeploy automatically regardless of this setting.

## External Services Used

Render's free tier has several real limitations that a single-service Django deployment runs into quickly. Each of the following was adopted specifically to work around one of them:

| Service | Used for | Why it was needed |
|---|---|---|
| **Neon** (Postgres) | Primary database | Render's own free-tier Postgres could not reliably be reached from outside Render's network, which blocked running `createsuperuser` from a local machine. Neon is built for reliable external connections and has a permanently free tier. |
| **Brevo** (via `django-anymail`) | Sending OTP verification emails | Since September 2025, Render blocks outbound traffic on SMTP ports (25/465/587) on free web services — a direct Gmail SMTP connection would hang until timing out, surfacing as a `502 Bad Gateway` on login. Brevo's HTTP API sends over standard HTTPS (port 443), which isn't blocked. |
| **Cloudinary** | Product image storage | Render's free web services have no persistent disk — any file uploaded through the app (e.g., a product photo) is wiped the next time the service redeploys or restarts. Cloudinary stores uploads externally and permanently. |
| **Render** | Application hosting | Free-tier web service hosting, deployed via Blueprint (`render.yaml`). |

## Deployment Challenges & Solutions

A number of non-obvious issues came up while getting this project running reliably on free-tier infrastructure. Documented here so they aren't re-discovered the hard way:

1. **Health check permanently failing on deploy.** Two separate causes stacked together: (a) Gunicorn defaults to binding `127.0.0.1:8000`, which Render's health checker cannot reach — fixed by explicitly binding to `0.0.0.0:$PORT`. (b) Once that was fixed, `SECURE_SSL_REDIRECT` was still 301-redirecting Render's internal health check (which hits the app over plain HTTP, bypassing the HTTPS-terminating proxy) — fixed with a dedicated `/healthz/` endpoint exempted via Django's `SECURE_REDIRECT_EXEMPT` setting.

2. **Invalid `render.yaml` Blueprint fields.** Render's database spec requires `postgresMajorVersion`, not the more intuitive `engine`/`version` keys. Similarly, `plan: starter` is a legacy plan that demands a credit card even for a database — `plan: free` is the actual no-card option.

3. **No shell access on the free tier, and no reliable way to create a superuser at build time.** `createsuperuser` normally requires an interactive terminal, unavailable on Render's free plan. A build-time management command (auto-creating a superuser from environment variables during every deploy) was attempted but did not reliably work in practice. The approach that actually worked: create the superuser from a local machine, connected directly to the live database, since Django's `createsuperuser` just needs a working `DATABASE_URL` — it doesn't care whether the process is running locally or on the server.

4. **External database connection timeouts.** The first attempt at the above — running `createsuperuser` locally against Render's own free-tier Postgres — consistently timed out. Root-caused to Render's free Postgres not being reliably reachable from outside its own network. Resolved by migrating the database to Neon, which is designed for reliable external connections; the same `createsuperuser` command then worked immediately by pointing `DATABASE_URL` at Neon's connection string.

5. **OTP emails failing with a 502 Bad Gateway.** Traced to Render's free-tier firewall blocking outbound SMTP ports entirely (a change Render rolled out in September 2025) — the app would hang trying to reach `smtp.gmail.com:587` until Gunicorn's worker timeout killed the request. Fixed by switching email delivery to Brevo's HTTP API via `django-anymail`, which requires no SMTP port at all.

6. **Uploaded product images disappearing after every deploy.** Render's free web services have no persistent disk; anything written to local storage at runtime — including uploaded images — is wiped on the next build. Fixed by routing all media uploads to Cloudinary instead of local disk (active only when Cloudinary credentials are present, so local development is unaffected).

7. **`collectstatic` crashing after adding Cloudinary.** `django-cloudinary-storage`'s custom `collectstatic` command reads the legacy, pre-Django-4.2 `STATICFILES_STORAGE` setting directly rather than the newer `STORAGES` dict this project uses, raising an `AttributeError` since that legacy setting was never defined. Fixed by defining it explicitly (mirroring the equivalent `STORAGES` entry) purely to satisfy that check.

8. **500 errors editing or deleting any product with an image.** Custom `save()`/`delete()` logic on the `Product` model called `.path` on the image field to manually remove the old file from disk — `.path` only exists for local filesystem storage and raises `NotImplementedError` on Cloudinary. Fixed by using Django's storage-agnostic `FieldFile.delete()` API instead, which works identically regardless of where the file actually lives.

9. **Deleting a product silently destroyed order history.** `OrderItem.product` originally used `on_delete=CASCADE`, so removing a product from the catalog cascade-deleted every order line item that ever referenced it — including already-delivered orders — zeroing out order totals and erasing what was purchased. Fixed by switching to `on_delete=SET_NULL`; since `unit_price` and `quantity` are already snapshotted on the order item, historical totals remain correct even after the product itself is gone.

10. **Intermittent "Bad Gateway" errors with no clear pattern.** Traced to two independent, stacked free-tier cold-start behaviors: Render sleeps an idle web service after ~15 minutes, and Neon independently suspends its database compute after 5 minutes of inactivity. A request arriving after both have gone idle has to wait for both to wake up, occasionally exceeding Render's own gateway timeout. Mitigated with an external uptime pinger hitting `/healthz/` periodically to keep the service warm.

11. **Accidental repository bloat.** The Python virtual environment (`venv/`) had been committed to git at some point, adding roughly 5,500 machine-specific, non-portable files to the repository history — removed from tracking (kept on disk) since `requirements.txt` already makes it fully reproducible.

## Project Structure

```
Inventory_Management/
├── render.yaml                  # Render Blueprint: build/start commands, env vars, health check
├── Procfile                     # Fallback process definition
├── requirements.txt
├── runtime.txt                  # Python version pin
└── inventory_management/
    ├── manage.py
    ├── inventory_management/    # Project settings, URLs, WSGI entry point
    └── accounts/                # The single app: models, views, forms, templates
        ├── migrations/
        └── templates/accounts/
            ├── partials/design_tokens.html        # Shared CSS design-token source of truth
            └── ...                                 # Buyer, admin, and auth page templates
```
