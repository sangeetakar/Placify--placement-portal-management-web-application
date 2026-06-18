For demo , please check out this Youtube link : https://www.youtube.com/watch?v=syl3uE62lTY

# 🎓 Placify - Placement Portal Application

A role-based web application built using **Flask, SQLite, Jinja2, and Bootstrap** to manage campus recruitment activities including company approvals, placement drives, and student applications.

---

## 📌 Project Overview

Institutes often rely on spreadsheets and emails to manage placement activities. This application provides a structured and automated system that allows:

- Admin (Institute Placement Cell)
- Companies
- Students

to interact through clearly defined workflows and approval mechanisms.

The system ensures:

- Company approval before drive creation
- Drive approval before visibility to students
- Duplicate application prevention
- Complete placement history tracking
- Role-based authentication and access control

---

## 🏗 Architecture Overview

The project follows a modular Flask architecture using Blueprints.


The database is created **programmatically** using SQLAlchemy.

---

## 🛠 Technologies Used

| Technology | Purpose |
|------------|----------|
| Flask | Backend framework |
| SQLAlchemy | ORM for database modeling |
| SQLite | Lightweight local database |
| Jinja2 | Server-side templating |
| Bootstrap 5 | Responsive UI |
| Werkzeug | Password hashing |
| Flask Sessions | Role-based authentication |

---

## 👥 User Roles & Functionalities

### 🏛 Admin (Institute Placement Cell)

- Pre-existing superuser (no public registration)
- Dashboard displaying:
  - Total students
  - Total companies
  - Total placement drives
  - Total applications
- Approve / Reject company registrations
- Approve / Reject placement drives
- Search students and companies
- Blacklist / deactivate accounts
- View historical placement data

---

### 🏢 Company

- Register and create profile
- Login only after admin approval
- Create placement drives
- Edit / Close drives
- View applicants
- Update application status:
  - Shortlisted
  - Selected
  - Rejected

---

### 🎓 Student

- Self-register and login
- Update profile
- Upload resume
- View approved placement drives
- Apply to drives
- Prevent duplicate applications
- Track application status
- View complete placement history

---

## 🗄 Database Schema

### Tables

**Admin**
- id
- username
- password

**Student**
- id
- name
- email
- password
- resume
- status

**Company**
- id
- company_name
- hr_contact
- website
- approval_status
- status

**PlacementDrive**
- id
- company_id (Foreign Key)
- job_title
- description
- eligibility
- deadline
- status (Pending / Approved / Closed)

**Application**
- id
- student_id (Foreign Key)
- drive_id (Foreign Key)
- application_date
- status (Applied / Shortlisted / Selected / Rejected)

---

### Relationships

- One-to-Many → Company → PlacementDrive  
- One-to-Many → Student → Application  
- One-to-Many → PlacementDrive → Application  

Foreign key constraints ensure relational integrity.

---

## 🔐 Authentication & Security

- Role-based login system
- Session-based authentication
- Secure password hashing
- Backend validation for:
  - Duplicate applications
  - Drive approval checks
  - Company approval enforcement  

---

