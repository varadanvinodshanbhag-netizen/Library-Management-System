# Library Management System

A Python-based desktop Library Management System developed as a 3rd Semester Diploma in Computer Science project.

## Project Overview

The Library Management System is a Windows desktop application developed using Python, Tkinter and SQLite. It helps manage books, members, book issue and return transactions, fines, extension requests, reports, magazines and newspapers from a single application.

The system provides separate access for administrators and library members.

## Main Features

- Admin login and dashboard
- Member login and dashboard
- Book management
- Member management
- Member account management
- Book issue and return
- Automatic due-date calculation
- Automatic overdue fine calculation
- Fine management
- Book extension requests
- Email reminders
- Printable library slips
- Library reports
- CSV report export
- Magazine management
- Newspaper management
- Search and sorting
- Activity logging
- Library settings
- College portal and news links

## Technologies Used

- Python 3
- Tkinter
- SQLite
- bcrypt
- python-dotenv
- PyInstaller

## Project Modules

The project is divided into separate modules for:

- Database management
- Authentication
- Admin dashboard
- Member dashboard
- Book management
- Member management
- Member accounts
- Issue and return
- Fine calculation
- Fine management
- Extension requests
- Reminders
- Reports
- Magazine management
- Newspaper management
- Activity logging
- Library slip generation

## Security Features

Security is an important part of the system.

- Passwords are protected using bcrypt hashing.
- Admin and member access are separated.
- Parameterized SQL queries are used.
- User input is validated.
- Member accounts can be activated or deactivated.
- Important actions are recorded in the activity log.
- Notification credentials are kept outside the source code.

## Installation

### 1. Install Python

Install Python 3.x on Windows.

### 2. Clone the repository

```bash
git clone https://github.com/varadanvinodshanbhag-netizen/Library-Management-System.git