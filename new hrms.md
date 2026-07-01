# New HRMS — TalentOS

## Ye project kya hai?

Ek **AI-powered HRMS (HR Management System)** ek specific company ke liye. Isme **do tarah ke log** login karte hain:

- **Admin (HR)** — puri company manage karta hai (employees, leave, payroll, hiring, settings).
- **Employee** — apni self-service cheezein dekhta hai (payslip, leave, profile, chatbot).

Iska khaas hissa: har employee ka apna **AI chatbot (agentic)** hoga jo real data se jawab dega — jaise *"mera leave balance kitna hai?"* → *"Aapka balance 12 din hai"* — aur chhote kaam khud kar dega. Aage chalke **ML models** company ke data pe train honge (leave decisions, attrition, etc.).

**Status legend:** ✅ ban gaya · 🔜 banana hai

---

## 👔 ADMIN (Employer) Side — Features

| # | Feature | Kya karega | Status |
|---|---|---|---|
| 1 | Company Signup | Company kholna + pehla admin account | ✅ |
| 2 | Login / Logout | Secure admin login | ✅ |
| 3 | Add Employee | Naya employee add → auto password + welcome email | ✅ |
| 4 | Manage Employees | Employee list, edit, role change, deactivate | ✅ |
| 5 | Leave Approvals | Employees ki leave requests dekhna + approve/reject | ✅ |
| 6 | Company Settings | Yearly leave limit, company info set karna | 🔜 |
| 7 | Payroll Setup | Salary structure (basic, HRA, deductions) set karna | 🔜 |
| 8 | Payslip Generation | Har mahine payslip banana + release karna | 🔜 |
| 9 | Attendance Tracking | Employee attendance / regularization dekhna | 🔜 |
| 10 | Job Postings (ATS) | Job create karna hiring ke liye | 🔜 |
| 11 | AI Resume Scoring | Resume upload → AI match score + ranking | 🔜 |
| 12 | Knowledge Base | Policy documents upload (chatbot inhe use karega) | 🔜 |
| 13 | Bulk Email / Announcements | Puri company ko email / notice bhejna | 🔜 |
| 14 | Meeting Scheduler | Google Calendar meeting banana | 🔜 |
| 15 | People Analytics | Dashboard — headcount, leave trends, attrition | 🔜 |
| 16 | Attrition Prediction (ML) | Kaun resign kar sakta hai — model batayega | 🔜 |
| 17 | Expense / Reimbursement | Employee claims approve karna | 🔜 |
| 18 | Audit Log | Har action ka record (kisne kya kiya) | 🔜 |
| 19 | AI Agent Console | Agents ne kya kiya dekhna + approve karna | 🔜 |

---

## 👋 EMPLOYEE Side — Features

| # | Feature | Kya karega | Status |
|---|---|---|---|
| 1 | Login / Logout | Emailed credentials se login | ✅ |
| 2 | My Profile | Apni info dekhna / edit request | 🔜 |
| 3 | Apply Leave | Leave apply karna (type, dates, reason) | ✅ |
| 4 | Leave Balance | Kitni leave bachi, kitni use hui | ✅ |
| 5 | My Leave History | Apni saari requests + status | ✅ |
| 6 | Payslip Access | Monthly payslip dekhna / download | 🔜 |
| 7 | Tax / Salary Info | Salary breakup, tax declaration | 🔜 |
| 8 | Attendance | Clock in/out, timesheet, regularize | 🔜 |
| 9 | Personal AI Chatbot | "Mera leave balance?", "payslip bhejo", "WFH policy?" — sab ek chat se | 🔜 |
| 10 | Policy Q&A | Company documents se sawaalon ke jawab | 🔜 |
| 12 | Announcements Feed | Company news / notices dekhna | 🔜 |
| 13 | Documents | Offer letter, contracts download | 🔜 |
| 14 | Onboarding Checklist | Naye joiner ke tasks | 🔜 |
| 15 | Helpdesk / Tickets | HR se query raise karna | 🔜 |

---

## 🤖 Cross-cutting (dono side ko touch karta hai)

| Feature | Kya karega | Status |
|---|---|---|
| Role-based access (Admin/Employee) | Har role ko sirf uske features dikhein | ✅ |
| Multi-tenant | Har company ka data alag + secure | ✅ |
| Light-theme UI (no purple color mujhe white off white aur light blue ya apko jo sahi lage wo but ui light theme me cchaiye bilkul keka jaisa.)| Saaf, light-coloured modern interface | 🔜 |
| Agentic AI layer | Chatbot jo tools use karke real kaam kare | 🔜 |
| ML models (company-trained) | Leave decisions, attrition, fraud detection | 🔜 |

---

*Note: Ye sirf features ki list hai — banane ka tareeka (tech/architecture) alag doc `docs/HRMS_ARCHITECTURE.md` mein hai.*
