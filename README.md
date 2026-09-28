# 🏙️ CivicDesk — Complain Management System

A production-ready, full-stack **Complain Management System** built with **FastAPI**, **Supabase PostgreSQL**, and **React (Vite + Tailwind CSS + DaisyUI)**. Designed with strict Role-Based Access Control (RBAC), secure JWT authentication, and a minimal, clean slate interface to highlight core backend functionalities.

---

## 🚀 Live Demo & Repository
* **GitHub Repository:** [Nafiz-Howladar/Civic-Desk](https://github.com/Nafiz-Howladar/Civic-Desk)
* **Frontend:** Vercel (Deployment Ready)
* **Backend:** Render (FastAPI + Supabase PostgreSQL)

---

## ✨ Key Features & 50-Marks Breakdown

### 1. Authentication & Authorization (15 Marks)
* **Secure Login & Signup:** Powered by OAuth2 Password Bearer (`POST /User_Login` using `application/x-www-form-urlencoded` and `POST /create_user`) with strict frontend & backend validation (Name: 3-30 chars, Password: 8-30 chars).
* **JWT State Management:** Automatic token handling via Axios interceptors, attaching `Authorization: Bearer <token>` to protected endpoints.
* **Strict Role-Based Access Control (RBAC):** Separate interfaces and protected routing for **Admin** and **Normal Users**.
* **Session Security:** Token expiry handling (401 detection) with automatic redirection and `react-hot-toast` notifications.

### 2. Dashboard & Data Management (15 Marks)
* **Role-Specific Dashboards:** Public Home Feed (`GET /`), User Complain Tracker (`GET /ComplainList`), and Admin Control Panel (`GET /admin/allcomplain`).
* **Advanced Controls:** Instant Search (by ID or text), Category Filtering (`electricity`, `water`, `road`, `garbage`, `internet`, `other`), Multi-criteria Sorting, and Pagination.
* **UX States:** Dedicated Loading Skeletons, Empty States, and Error Retry Handlers.
* **Full Admin CRUD:** Create, Edit, Delete complaints, and update statuses (`Progress` / `Complete`).

### 3. Responsive UI & Forms (10 Marks)
* Built using **React**, **Tailwind CSS**, **DaisyUI**, and **React Icons**.
* Fully responsive across Mobile, Tablet, and Desktop screens.
* Integrated image file uploader with automated **Base64 conversion** and preview support for reports.

### 4. Routing & User Experience (10 Marks)
* Clean component structure with custom Breadcrumbs, responsive Navbar, Footer, and confirmation modals for destructive actions (e.g., deletions).

---

## 🛠️ Tech Stack

* **Frontend:** React, Vite, React Router, Tailwind CSS, DaisyUI, React Icons, React Hot Toast, Axios.
* **Backend:** FastAPI, Python, SQLAlchemy, Passlib (Bcrypt), PyJWT, Pydantic.
* **Database:** Supabase PostgreSQL (with local SQLite fallback capability).

---

## 📋 API Endpoints Reference

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/create_user` | Register a new user | No |
| `POST` | `/User_Login` | OAuth2 form-data login (returns JWT) | No |
| `PUT` | `/edituser` | Update user profile name/email | Yes |
| `PUT` | `/passwordchange` | Change user password | Yes |
| `GET` | `/` | Public view of all complaints | No |
| `POST` | `/complain_create` | Submit a new complaint | Yes |
| `GET` | `/ComplainList` | Get logged-in user's complaints | Yes |
| `GET` | `/admin/allcomplain` | Admin: View all system complaints | Yes (Admin) |
| `GET` | `/admin_search_complain/{id}`| Admin: Search complaint by ID | Yes (Admin) |
| `GET` | `/admin_filter_category/` | Admin: Filter complaints by category | Yes (Admin) |
| `PUT` | `/admin_status_progress/{id}`| Admin: Set status to Progress | Yes (Admin) |
| `PUT` | `/admin_status_complete/{id}`| Admin: Set status to Complete | Yes (Admin) |

---

## 👤 Demo Credentials for Evaluation

* **Admin Account:**
  * **Email:** `admin@example.com`
  * **Password:** `admin1234`
* **Normal User Account:**
  * **Email:** `user@example.com`
  * **Password:** `12345678`

---

## ⚙️ Local Development Setup

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/Nafiz-Howladar/Civic-Desk.git](https://github.com/Nafiz-Howladar/Civic-Desk.git)
   cd Civic-Desk

    cd backend
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn main:app --reload

    cd ../complain-frontend
    npm install
    npm run dev
