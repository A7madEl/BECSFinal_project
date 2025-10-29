🩸 BECS – Blood Bank Management System

This is a Django-based Blood Bank Management System designed for educational use.
It allows donors to donate blood, patients to request blood, and gives doctors and students the ability to view and manage blood stock.

🚀 How to Run the Project

## First Time Setup

1. **Clone or Open the Project**

   Make sure you're inside the folder where `manage.py` exists:

   ```bash
   cd BECSFinal_project
   ```

2. **Create a Virtual Environment**

   **Windows (PowerShell):**
   ```powershell
   python -m venv .venv
   . .\.venv\Scripts\Activate.ps1
   ```

   **Mac/Linux:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   Or manually:
   ```bash
   pip install django==5.2.7 reportlab
   ```

4. **Run Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
   > ⚠️ **Note:** After running `migrate`, a default doctor user will be automatically created:
   > - Username: `doctor1`
   > - Password: `Root1978`
   > - Email: `doctor@example.com`

5. **Create an Admin User (Optional)**
   ```bash
   python manage.py createsuperuser
   ```
   This creates a Django superuser for the admin panel.

6. **Run the Server**
   ```bash
   python manage.py runserver
   ```
   Then open: http://127.0.0.1:8000/

## Setting Up on Another PC (After Cloning from GitHub)

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd BECSFinal_project
   ```

2. **Create virtual environment** (same as step 2 above)

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```
   > ✅ The default doctor user (`doctor1` / `Root1978`) will be automatically created during this step!

5. **Run the server:**
   ```bash
   python manage.py runserver
   ```

## 📦 What to Upload to GitHub

### ✅ **DO Include (Commit these):**
- ✅ All Python code files (`.py`)
- ✅ **Migration files** in `accounts/migrations/` and `blood/migrations/` (except `__pycache__`)
- ✅ Templates, static files, HTML files
- ✅ `requirements.txt`
- ✅ `.gitignore`
- ✅ `README.md`
- ✅ `manage.py`

### ❌ **DON'T Include (Git will ignore these):**
- ❌ `db.sqlite3` (database file - each PC has its own)
- ❌ `__pycache__/` folders (Python cache)
- ❌ `.venv/` or `venv/` (virtual environment)
- ❌ `.vscode/`, `.idea/` (IDE settings)
- ❌ `*.pyc` files (compiled Python files)

The `.gitignore` file handles this automatically!

👤 User Roles Overview

**Doctor (Admin)** – Automatically created on first migration (`doctor1` / `Root1978`). Can also be created from `/admin/`. Can approve/reject requests, view stock, export PDF.

**Student** – Created from `/admin/`. Can view stock and export PDF.

Donor / Patient – Can sign up through /accounts/signup/.

Donor: can donate blood and make requests.

Patient: can only make requests.

🧭 Main Pages
URL	Description
/	Home Page
/accounts/login/	Login Page
/accounts/signup/	Signup for Donor/Patient
/dashboard/	Role-based Dashboard
/admin/	Admin Panel (for creating users)
/doctor/stock/	View stock & Export PDF (Doctor)
/student/stock/	View stock (Student)
📝 Short Explanation

Donors can donate blood units, which are stored in the system.

Patients can make requests for specific blood types.

Doctors review requests and approve or reject them.

Students can only view stock reports.

Stock reports can be exported to PDF for record keeping.

🛠️ Built With

Django
 (Backend)

Tailwind CSS
 (Frontend styling via CDN)

ReportLab
 (PDF Export)

SQLite (Default database)
