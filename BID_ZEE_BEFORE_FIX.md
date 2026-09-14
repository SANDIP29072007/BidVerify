# BID ZEE — Baseline Architecture & Issues Report (BEFORE FIX)

**Date**: 2026-09-14
**Repository**: `SANDIP29072007/BidVerify`
**Live Deployment**: https://bidverify-blue.vercel.app/login

---

## 1. Architecture Discovered

### Frontend
- **Framework**: React 19 + Vite (`frontend/src`)
- **Entry point**: [main.jsx](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/frontend/src/main.jsx), [App.jsx](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/frontend/src/App.jsx)
- **Pages**: [Login.jsx](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/frontend/src/pages/Login.jsx), [Home.jsx](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/frontend/src/pages/Home.jsx), [DocumentUpload.jsx](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/frontend/src/pages/DocumentUpload.jsx), [BidderProfile.jsx](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/frontend/src/pages/BidderProfile.jsx)
- **State & Services**: `apiFetch` in [api.js](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/frontend/src/services/api.js), Supabase browser client in [client.js](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/frontend/src/utils/supabase/client.js)

### Backend
- **Framework**: FastAPI + Uvicorn (`backend/app`)
- **Entry point**: [main.py](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/backend/app/main.py)
- **API Routers**: `auth.py`, `users.py`, `bids.py`, `tenders.py`, `documents.py`, `analysis.py`, `audit.py`, etc.
- **Serverless API Entry**: [index.py](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/api/index.py) for Vercel deployment

### Database Layer
- **ORM**: SQLAlchemy with PostgreSQL (`psycopg` / `psycopg2`)
- **Engine Resiliency**: [database.py](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/backend/app/db/database.py) with dynamic driver fallback and local SQLite fallback (`bid_compliance_persistent.db`)
- **Migrations**: Custom self-healing migrations in `apply_schema_migrations()` and Alembic configuration

### Authentication Implementation
- **Current Flow**: Dual authentication system:
  1. Custom bcrypt password hashing (`verify_password`, `get_password_hash`) and custom HS256 JWT tokens generated server-side.
  2. Partial Supabase Auth user creation calls in `AuthService.register_user` and `AuthService.create_user_by_admin` using REST requests to `/auth/v1/admin/users`.
- **Identity Key**: `User.id` (UUIDv4 generated locally or copied from Supabase if created via admin API), with `auth_user_id` stored as a secondary string column.

### Storage & AI Verification
- **Storage**: Ephemeral local uploads directory (`storage/uploads` or OS temp directory) with optional Supabase Storage helper.
- **Verification Engine**: Multi-stage OCR, AI document extraction (Gemini / Groq), and mock government registry checks.

---

## 2. Discovered P0/P1 Issues & Responsible Files

| Issue Category | Description | Exact Files / Functions Responsible |
| :--- | :--- | :--- |
| **Dual Authentication** | System uses local bcrypt password verification for login while creating Supabase Auth users asynchronously without making Supabase Auth the single source of truth. | [auth.py](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/backend/app/api/auth.py#L38-L92), [auth_service.py](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/backend/app/services/auth_service.py#L94-L327) |
| **Unsafe Auth Fallback** | `get_current_user` falls back to returning *any* active user matching a role or triggering `init_admin_user()` if token sub resolution fails. | [auth_service.py:get_current_user](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/backend/app/services/auth_service.py#L454-L466) |
| **Automatic Demo Seeding** | System automatically seeds demo admin, sample tenders, and sample bids on startup in `database.py`. | [database.py](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/backend/app/db/database.py#L208-L343) (`init_admin_user`, `seed_initial_tenders`) |
| **Sample Data Fallbacks** | Backend and frontend logic fall back to `bids[0]`, `INITIAL_BIDS[0]`, or static mock records when queries return empty results. | [bids.py](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/backend/app/api/bids.py), [Home.jsx](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/frontend/src/pages/Home.jsx) |
| **Data Isolation / IDOR** | Certain API routes allow frontend-supplied `bidder_id` or `user_id` query params instead of enforcing ownership via authenticated JWT. | [bids.py](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/backend/app/api/bids.py), [documents.py](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/backend/app/api/documents.py) |
| **Test Collection Failure** | `tests/auth_integration.test.py` fails during pytest collection because pytest treats `auth_integration.test.py` as a module named `auth_integration.test`. | [tests/auth_integration.test.py](file:///c:/Users/sandi/OneDrive/Desktop/SIH_TRAILS/tests/auth_integration.test.py) |

---

## 3. Existing Test Suite Execution Status

1. **Frontend Tests**:
   - Command: `node --test tests/*.test.js` (via `npm test`)
   - Result: **27 / 27 PASS**
2. **Backend Unit Tests**:
   - Command: `pytest backend/tests/`
   - Result: Executing cleanly (47 collected items).
3. **Integration Tests**:
   - File: `tests/auth_integration.test.py`
   - Result: **FAIL** (ImportError: ModuleNotFoundError during collection due to filename syntax).

---

## 4. Secret Security Audit

All configuration environment variable names (`SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `DATABASE_URL`, `JWT_SECRET`, `GROQ_API_KEY`, `GEMINI_API_KEY`) have been verified.
*No actual secret values or credentials are printed or exposed in this report.*
