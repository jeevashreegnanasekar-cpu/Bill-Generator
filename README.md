 Project Overview
 
 RVCE Fee Management System is a modern, role-based web application built with Flask for efficient fee collection and management at RV College of Engineering. Features neon cyberpunk UI, multi-role authentication, PDF bill generation, Excel import/export, and real-time analytics.
 
 📋 Key Features
 
 3 Role System: Student (Register/Login), Admin, Owner
 
 Student Registration: One-time registration with duplicate check
 
 Dashboard Analytics: Total Bills, Total Revenue, Pending Fees count
 
 Pending Fees Table: Name, Dept, Fee Type, Due Date, Amount
 
 Excel Import: Bulk upload pending students from Excel
 
 Generate Bill: PDF generation with payment proof upload
 
 Total Bills: Auto-save generated bills with preview option
 
 Responsive Design: Cyberpunk neon theme with glassmorphism effects
 
 
 
 🗂️ Project Structure
 
 rvce-fee-management/
│
├── app.py                 # Main Flask application
├── static/
│   ├── style.css          # Global styles
│   ├── script.js          # Client-side JavaScript
│   └── logo.jpeg          # College logo
├── templates/
│   ├── index.html         # Role selection page
│   ├── register.html      # Student registration
│   ├── login.html         # Login pages (all roles)
│   ├── success.html       # Registration success
│   └── dashboard.html     # Main dashboard (Dashboard + Generate Bill + Total Bills)
├── data/
│   ├── students.db        # SQLite database
│   ├── pending_fees.xlsx  # Excel import/export
│   └── bills/             # Generated PDF bills
└── README.md              # This file


🎮 User Flow


index.html (Role Selection)
    ↓
├── STUDENT → register.html → success.html → login.html → dashboard.html
├── ADMIN   → login.html → dashboard.html
└── OWNER   → login.html → dashboard.html

Dashboard Features:

Sidebar: Dashboard | Generate Bill | Profile | Logout

DASHBOARD PAGE:
├── Top Metrics: [Total Bills] [Total Revenue] [Pending Count]
├── Buttons: [Import Excel] [Total Bills]
└── Pending Fees Table: Name | Dept | Fee Type | Due Date | Amount

GENERATE BILL PAGE:
Form Fields: Student Name | Dept | Fee Type | Date | Reg No | Year/Sem
            | Payment Mode | Amount | Reference (File Upload)
→ Generate PDF → Auto-save to Total Bills

TOTAL BILLS PAGE:
├── Same table structure as Pending Fees
└── Preview button (shows bill text)

🚀 Quick Setup & Demo

# 1. Clone & Install

git clone <your-repo>
cd rvce-fee-management
pip install -r requirements.txt

# 2. Run
python app.py
# Visit: http://localhost:5000

# 3. Test Flow
# Student: index → Register → Login → Dashboard
# Admin/Owner: index → Direct Login → Dashboard

🛠️ Tech Stack

Backend: Flask, SQLite, Pandas (Excel), ReportLab (PDF)
Frontend: HTML5, CSS3 (Cyberpunk/Neon), Vanilla JS
Features: File Upload, PDF Generation, Excel I/O, Role Auth

🔧 Core Functionalities
1. Role-Based Access

index.html → Asks "Which role?" → Routes to respective pages
Student: Registration → Login
Admin/Owner: Direct Login

2. Dashboard Analytics [dashboard.html]Top Cards:
- Total Bills Count
- Total Revenue (Sum of all paid amounts)
- Pending Fees Count

Pending Table: Lists unpaid students
Import Excel: Bulk upload from Excel file

3. Bill Generation [dashboard.html - Generate Bill tab]Form → PDF Generation → Auto-save to Total Bills
Fields: All student + payment details + proof upload
Revenue auto-updates from Total Bills sum

4. Data FlowExcel Import → Pending Table → Generate Bill → PDF + Total Bills Table
                                    ↓
                              Total Revenue Updates
                              
 📱 Responsive Features
 
 Cyberpunk Neon Theme: Glassmorphism + glowing effects
 
 Mobile-First: Sidebar collapses on mobile
 
 Smooth Animations: Hover effects, transitions
 
 Dark Mode: Native cyberpunk palette


📄 Requirements.txt

Flask==2.3.3
pandas==2.1.4
openpyxl==3.1.2
reportlab==4.0.7
Werkzeug==3.0.1

🔒 Security Features

Role-based routing
Duplicate registration check
File upload validation
Session management
SQLite data isolation

 Contribution
 
Fork → Clone → Create Feature Branch → PR
Focus areas: New payment gateways, SMS alerts, Multi-college support

