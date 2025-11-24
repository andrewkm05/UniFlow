# UniFlow - Student Planner & Academic Dashboard

#### Video Demo: 

#### Description:

UniFlow is a full-stack Flask web application that helps university students centralize all academic responsibilities into one structured environment. 

Instead of checking separate tools for schedules, assignments, grades and internship applications, UniFlow brings everything into one unified dashboard with a consistent design and smooth interactions

---

## **Project Goals**

The main purpose of UniFlow is to simplify planning so students can focus on what actually matters: studying, working on projects, and keeping balance. 

The app was built to be:

- **Simple** - clean UI, minimal steps
- **Organized** - all academic information in one place 
- **Responsive** - works smoothly across devices
- **Clean & Modern** - warm aesthetic and clean card
- **Practical** - matches real student workflows

I wanted a tool that i would genuinely use every day.

---

## Project Structure

- `app.py`
- `db.py`

- `instance/`
  - `uniflow.db`

- `templates/`
  - `base.html`
  - `welcome.html`
  - `signup.html`
  - `login.html`
  - `home.html`
  - `schedule.html`
  - `assignments.html`
  - `applications.html`
  - `grades.html`

- `static/`
  - `css/`
    - `styles.css`
  - `js/`
    - `schedule.js`
    - `assignments.js`
    - `applications.js`
    - `grades.js`

---

## **Features in Detail**

### **1. Authentication & Entry pages (Welcome / Login / Signup)**

UniFlow includes a fully custom authentication flow:

- **Welcome Page** - a minimal landing screen with project's color palette, large logo typography, and two primary actions (Log In / Sign Up)

- **Login Page** - form with server-side validation, CS50-style error handling, and session creation

- **Signup Page** - form for new users with validation for empty fields, duplicate emails, and secure password hashing

Flask's session management is used to keep users logged in and restrict access to all dashboard routes unless authenticated

---

### **2. Weekly Schedule (Time-based Grid System)**

This is one of the most technically involved parts of the project. Entries can be added, edited, and deleted for any day of the week.

The schedule page contains:

- A **vertical timeline** implicitly built into each column
- Automatic positioning of events based on their start time
- Adjust event height based on duration (1h, 2h, 3h, etc.)
- Avoids visual overlap
- Modal-based UI using Bootstrap for adding/editing events
- Applies CSS variables and custom JS logic

This system replaces the need for a calendar library and demonstrates algorithmic thinking, CSS variable usage, and JS DOM manipulation.

---

### **3. Assignment Tracker**

A structured table that allows the student to:

- Add assignments with due dates
- Track completion and subtasks / stages
- Automatically highlight assignments based on priority (urgent, normal, low)
- Notes per assignment

Each assignment receives a priority badge based on how close the due date is, and the due date itselfnis color-coded with JavaScript (red for urgent, yellow for soon, green for low priority, and strong red for overdue items).

Completed stages are visually marked with a strikethrough, and the UI supports autosizing textareas and smooth open/close panels for a clean workflow.

---

### **4. Internship Applications Tracker**

A dedicated dashboard to track opportunities such as internships, summer programs, part-time opportunities, and scholarships.

Features include:

- Status selection across many stages
- Opening and closing date tracking with automatic color coding
- JavaScript logic that highlights deadlines based on urgency (upcoming or overdue)
- Status-based styling (green border for "Offer Received" and red for "Rejected")
- Flags for required documents (CV, cover letter, written answers)
- Dynamic row editing
- Large responsive table with equalized column widths

This module became extremely useful in real life, as i myself began preparing for internships.

---

### **5. Grades Dashboard**

The grade module allows students to see their progress in a structured and visual way.

- Terms (semesters)
- Modules (courses)
- Assessments per module
- Weighted grade calculations for each module
- An "Across Terms" section that aggregates overall performance
- An automatically computed overall percentage grade based on all terms
- Expandable cards for cleaner navigation and usability

---

### **6. Homepage Dashboard Cards**

The homepage provides an instant overview, including:

- Assignments due in the next 7 days
- Active internship applications
- Next closing application deadline
- Overall academic grade

---

## **Backend Implementations**

#### **Flask (Python)** 

- Handles routing, session management, data validation and CRUD logic

#### **Jinja2** 

- Used for loops, conditionals, rendering dynamic content and passing backend data to frontend templates

#### **SQLite** 

Database consists of:

- `users`
- `schedule_items`
- `assignments`
- `stages`
- `applications`
- `grades_term`
- `grades_modules`
- `grades_assessments`

#### **db.py**
A minimal custom wrapper that provides:

- Safe parameterized SQL queries
- Auto-commit for write operations
- Returning rows as Python dictionaries

---

## Frontend & UX

#### **Bootstrap 5**

- For layout and components

#### **Custom CSS (large file)**

- For theme, cards, animations

#### **CSS variables**

- For colors, spacing, card styles

#### **JavaScript**

- For schedule event placement
- For autosizing textareas
- For deadline highlighting
- For grade computation in real time 

No external JS libraries were used

---

## AI Usage Disclosure (Required by CS50)

During UniFlow's development, ChatGPT was used **strictly** as a **learning + debugging assistant**, never as a code generator.

**No AI-generated code was copied** into the project.

AI was used responsibly to:

- Understand errors in code i wrote myself
- Explore alternative implementations
- Learn new and better patterns in Flask, SQL, CSS grid and JS 
- Resolve tricky bugs

All backend logic, SQL queries, HTML, CSS and JS were manually implemented by me.

This fully follows CS50's policy.

---

## Future Enhancements

- Drag-and-drop schedule editing
- Dark mode toggle
- Study session timer
- PDF export for assignments and schedule
- Mobile app version
- Google / Outlook calendar integration
- Notifications & reminders

---

## Conclusion

UniFlow is my most complete full-stack project to date. It integrates backend logic, database design, frontend engineering, and UI/UX into a tool that genuinely helps students stay organized.

Throughout this project i gained experience in:

- Designing clear Flask routes
- Building CRUD-based pages
- Using dynamic JS interactions
- Designing maintainable CSS
- Structuring a database that supports real use cases

I am proud of this project and excited to keep improving it.

> This was CS50!

