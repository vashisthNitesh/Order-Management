# Smart Restaurant Ordering System

A full-stack QR-based restaurant ordering web application built with Next.js 14 and Django REST Framework.

## Features

### Customer Experience
- Scan QR code on table → instant menu access (no login required)
- Browse by category, search dishes
- Popular items & Chef's specials sections
- Promotional offers banner
- Add to cart with quantity controls
- Floating cart button with smooth animations
- Order review with special instructions
- Real-time order tracking (auto-refresh every 10s)

### Staff Portal
- Secure JWT login
- Live order dashboard with status tabs
- One-click status updates (Pending → Confirmed → Preparing → Ready → Served)
- Kitchen Display View (3-column kanban board)
- Auto-refresh every 10-15 seconds

### Admin Panel
- Dashboard with today's stats & live orders
- Full Menu Item management (CRUD + image upload)
- Category management with emoji icons
- Promotional offers with discount scheduling
- Table management + QR code generation/download
- Staff account management

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, Framer Motion |
| State | Zustand (cart + auth), TanStack Query (server state) |
| Backend | Django 4.2, Django REST Framework |
| Auth | JWT (simplejwt) |
| Database | PostgreSQL 16 |
| UI Components | Custom + Radix UI primitives |
| Containerization | Docker + Docker Compose |

## Quick Start (Docker)

```bash
# Clone and start
git clone <repo>
cd Order-Management
docker compose up --build

# App will be available at:
# Customer Menu:  http://localhost:3000/menu/1
# Staff Portal:   http://localhost:3000/staff/login
# Admin Panel:    http://localhost:3000/admin/login
# API Docs:       http://localhost:8000/api/docs/
```

## Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Run migrations
python manage.py migrate

# Seed sample data
python manage.py seed_data

# Start development server
python manage.py runserver
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Configure environment
cp .env.example .env.local
# Edit .env.local if needed

# Start development server
npm run dev
```

## Project Structure

```
Order-Management/
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   └── urls.py
│   ├── apps/
│   │   ├── restaurants/    # Restaurant & Table models
│   │   ├── menu/           # Category & MenuItem models
│   │   ├── orders/         # Order & OrderItem models
│   │   ├── offers/         # Promotional offers
│   │   ├── staff/          # Staff profiles
│   │   └── authentication/ # JWT auth endpoints
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── menu/[tableId]/     # Customer menu page
│       │   ├── order/
│       │   │   ├── review/         # Order review
│       │   │   ├── success/        # Order success
│       │   │   └── tracking/       # Order tracking
│       │   ├── staff/
│       │   │   ├── login/
│       │   │   ├── dashboard/      # Order management
│       │   │   └── kitchen/        # Kitchen display
│       │   └── admin/
│       │       ├── dashboard/
│       │       ├── menu/
│       │       ├── categories/
│       │       ├── offers/
│       │       ├── tables/
│       │       └── staff/
│       ├── components/
│       │   ├── customer/   # Menu, cart, food cards
│       │   ├── staff/      # Order cards, layouts
│       │   └── admin/      # Admin layouts, stat cards
│       ├── store/          # Zustand stores
│       ├── lib/            # API client, utilities
│       └── types/          # TypeScript interfaces
│
└── docker-compose.yml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/` | Staff/Admin login |
| GET | `/api/restaurants/` | List restaurants |
| GET | `/api/restaurants/tables/{id}/` | Get table (public) |
| GET | `/api/menu/categories/` | List categories with items |
| GET | `/api/menu/items/` | List menu items |
| GET | `/api/menu/items/popular/` | Popular items |
| GET | `/api/menu/items/specials/` | Chef's specials |
| POST | `/api/orders/` | Place order (public) |
| GET | `/api/orders/{id}/` | Track order (public) |
| PATCH | `/api/orders/{id}/update_status/` | Update order status (auth) |
| GET | `/api/offers/` | List active offers |
| GET | `/api/docs/` | Swagger API documentation |

## Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Manager | `manager1` | `staff123` |
| Waiter | `waiter1` | `staff123` |
| Kitchen | `kitchen1` | `staff123` |

## QR Code Flow

1. Admin creates a table → QR code is auto-generated
2. QR code encodes URL: `http://your-domain.com/menu/{table_id}`
3. Customer scans QR → lands on menu page with table context
4. Table ID is stored in cart state for order placement

## Environment Variables

### Backend (.env)
```
DEBUG=True
SECRET_KEY=your-secret-key
DB_NAME=restaurant_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_MEDIA_URL=http://localhost:8000
NEXT_PUBLIC_DEFAULT_RESTAURANT_ID=1
```
