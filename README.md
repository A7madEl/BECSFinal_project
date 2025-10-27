🩸 BECS – Blood Bank Management System

This is a Django-based Blood Bank Management System designed for educational use.
It allows donors to donate blood, patients to request blood, and gives doctors and students the ability to view and manage blood stock.

🚀 How to Run the Project
1. Clone or Open the Project

Make sure you’re inside the folder where manage.py exists:

cd becs_web

2. Create a Virtual Environment

Windows (PowerShell):

python -m venv .venv
. .\.venv\Scripts\Activate.ps1


Mac/Linux:

python3 -m venv .venv
source .venv/bin/activate

3. Install Dependencies
pip install django==5.2.7 reportlab

4. Run Migrations
python manage.py makemigrations
python manage.py migrate

5. Create an Admin User
python manage.py createsuperuser


Enter a username and password to log into the admin panel.

6. Run the Server
python manage.py runserver


Then open: http://127.0.0.1:8000/

👤 User Roles Overview

Doctor (Admin) – Created from /admin/. Can approve/reject requests, view stock, export PDF.

Student – Created from /admin/. Can view stock and export PDF.

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
