"""
Knowledge base for the BuckeyeLink prompt enhancer.

Contains known pages, navigation hints for undiscovered pages,
and PeopleSoft UI knowledge that helps the browser-use agent navigate.
"""

# Pages with known direct URLs (matches buckeyelink/browser.py URLS dict)
KNOWN_PAGES = {
    "schedule": {
        "url": "https://buckeyelink.osu.edu/launch-task/all/my-class-schedule",
        "description": "Student class schedule for the current term",
        "keywords": ["class schedule", "classes", "weekly schedule", "courses"],
    },
    "grades": {
        "url": "https://buckeyelink.osu.edu/task/all/grades",
        "description": "View grades by term",
        "keywords": ["grades", "gpa", "transcript", "marks"],
    },
    "financial_aid": {
        "url": "https://buckeyelink.osu.edu/task/all/financial-aid-status",
        "description": "Financial aid awards, status, and disbursements",
        "keywords": ["financial aid", "fafsa", "scholarships", "grants", "loans", "aid status"],
    },
    "schedule_planner": {
        "url": "https://buckeyelink.osu.edu/task/all/schedule-planner",
        "description": "Plan future semester schedules",
        "keywords": ["schedule planner", "plan schedule", "next semester"],
    },
    "holds_todos": {
        "url": "https://buckeyelink.osu.edu/collection/all/holds-todos",
        "description": "Account holds and to-do action items",
        "keywords": ["holds", "to-do", "todos", "action items", "blocks"],
    },
    "enrollment": {
        "url": "https://buckeyelink.osu.edu/collection/all/enrollment-center",
        "description": "Enrollment and registration center",
        "keywords": ["enrollment", "registration", "enroll", "add class", "drop class"],
    },
    "dashboard": {
        "url": "https://buckeyelink.osu.edu",
        "description": "BuckeyeLink home dashboard with academics, finances, and announcements",
        "keywords": ["dashboard", "home", "overview"],
    },
}

# Navigation hints for pages that don't have known direct URLs.
# The browser-use agent will use these to navigate from the dashboard.
SITEMAP_HINTS = {
    "tuition_bill": {
        "description": "Tuition and fee charges, account balance, payment due dates",
        "keywords": ["tuition", "bill", "charges", "fees", "balance", "payment", "amount due", "pay"],
        "nav_hint": (
            "From the BuckeyeLink dashboard, look for 'Account Balance' or 'Make a Payment' "
            "or navigate to Finances section. May also appear under Student Center > Finances."
        ),
    },
    "billing_statement": {
        "description": "Detailed billing statement / eBill",
        "keywords": ["billing statement", "ebill", "statement", "invoice"],
        "nav_hint": (
            "From BuckeyeLink, look for 'View eBill' or 'Billing Statement' under Finances. "
            "May require navigating to Student Center > Finances > View eBill."
        ),
    },
    "degree_audit": {
        "description": "Degree audit / DARS report showing degree progress",
        "keywords": ["degree audit", "dars", "degree progress", "requirements", "graduation requirements"],
        "nav_hint": (
            "Look for 'Degree Audit' or 'DARS' link. Often found under Academics section "
            "or Student Center > Academics > View My Degree Audit."
        ),
    },
    "transfer_credit": {
        "description": "Transfer credit report",
        "keywords": ["transfer credit", "transfer", "credit transfer", "ap credit", "ib credit"],
        "nav_hint": (
            "Navigate to Academics > Transfer Credit Report or look for 'Transfer Credit' "
            "in the Student Center."
        ),
    },
    "tax_1098t": {
        "description": "1098-T tax form for tuition payments",
        "keywords": ["1098-t", "1098t", "tax form", "tax", "tuition tax"],
        "nav_hint": (
            "Look for '1098-T' or 'Tax Information' under Finances. "
            "May redirect to an external tax document portal."
        ),
    },
    "direct_deposit": {
        "description": "Direct deposit / refund setup",
        "keywords": ["direct deposit", "refund", "bank account", "ach"],
        "nav_hint": (
            "Look for 'Direct Deposit' or 'Manage Refunds' under Finances. "
            "May also be under Student Center > Finances."
        ),
    },
    "addresses": {
        "description": "Student addresses on file (mailing, home, campus)",
        "keywords": ["address", "addresses", "mailing address", "home address", "update address"],
        "nav_hint": (
            "Navigate to Personal Information > Addresses. "
            "May be under Student Center > Personal Information."
        ),
    },
    "exam_schedule": {
        "description": "Final exam schedule for the current term",
        "keywords": ["exam schedule", "final exam", "finals", "exam time", "exam location"],
        "nav_hint": (
            "Look for 'Exam Schedule' or 'Final Exams' under Academics. "
            "May also be found from the class schedule page."
        ),
    },
    "advisor": {
        "description": "Academic advisor information and contact",
        "keywords": ["advisor", "adviser", "academic advisor", "advising"],
        "nav_hint": (
            "Look for 'My Advisor' or 'Advisor' information. Often found in the "
            "Student Center under Academics or on the dashboard."
        ),
    },
    "unofficial_transcript": {
        "description": "Unofficial academic transcript",
        "keywords": ["unofficial transcript", "transcript", "academic record", "academic history"],
        "nav_hint": (
            "Navigate to Academics > View Unofficial Transcript or look for "
            "'Transcript' link in Student Center."
        ),
    },
    "class_search": {
        "description": "Search for classes to enroll in",
        "keywords": ["class search", "search classes", "find class", "course search"],
        "nav_hint": (
            "Look for 'Search for Classes' or 'Class Search' under Enrollment. "
            "Usually in Enrollment Center or Student Center > Academics."
        ),
    },
    "waitlist": {
        "description": "Waitlist status for classes",
        "keywords": ["waitlist", "wait list", "waitlisted"],
        "nav_hint": (
            "Check enrollment status in Student Center > Academics > My Class Schedule "
            "or Enrollment Center. Waitlisted classes show status."
        ),
    },
}

# System knowledge about how BuckeyeLink / PeopleSoft works
PEOPLESOFT_KNOWLEDGE = """\
BuckeyeLink (buckeyelink.osu.edu) is Ohio State University's student portal.

UI Architecture:
- The outer shell is a React SPA (Single Page Application)
- Many academic/financial tasks render inside PeopleSoft iframes
- PeopleSoft pages may have their own navigation, tabs, and dropdown selectors
- Some pages require selecting a term (semester) from a dropdown before data appears

Common UI Patterns:
- Loading overlays: the SPA shows "Loading..." while content renders; wait for it
- Term selectors: dropdowns labeled "Term" or "Select Term" — pick the current/most recent term
- PeopleSoft iframes: data often lives inside an iframe; look inside iframes for content
- Accordions/expandable sections: click section headers to reveal content
- "Student Center" is the main PeopleSoft hub with links to most features
- Navigation tiles on the dashboard link to major sections

Important Constraints:
- This is READ-ONLY — never click buttons that modify data (enroll, drop, pay, submit)
- Never fill in forms that could change student records
- Only navigate, read, and extract information
- If a confirmation dialog appears, always cancel

Tips for Navigation:
- If you can't find something, try the Student Center (PeopleSoft) which has the most links
- Some links open new tabs/windows — stay in the current tab
- BuckeyeLink URLs follow patterns: /launch-task/all/*, /task/all/*, /collection/all/*
- After clicking a link, wait for the page/iframe to fully load before extracting
"""
