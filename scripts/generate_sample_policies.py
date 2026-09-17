import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = PROJECT_ROOT / "knowledge_base"


def create_policy_pdf(filename: str, title: str, pages_content: list[list[str]]) -> None:
    output_path = KB_DIR / filename
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=14,
    )
    heading_style = ParagraphStyle(
        "DocHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1f2937"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#374151"),
        spaceAfter=8,
    )

    story = []
    for page_idx, page_paragraphs in enumerate(pages_content):
        if page_idx == 0:
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 10))
        else:
            story.append(PageBreak())
            story.append(Paragraph(f"{title} (Continued)", heading_style))
            story.append(Spacer(1, 10))

        for para in page_paragraphs:
            if para.startswith("## "):
                story.append(Paragraph(para[3:], heading_style))
            else:
                story.append(Paragraph(para, body_style))

    doc.build(story)
    print(f"Generated: {output_path.name}")


def generate_all():
    KB_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating sample policy PDF documents in knowledge_base/...")

    # 1. Leave Policy
    create_policy_pdf(
        "leave_policy.pdf",
        "Company Leave and Time Off Policy",
        [
            [
                "## 1. Annual Paid Time Off (PTO)",
                "Full-time permanent employees are entitled to 20 business days of paid annual leave per calendar year.",
                "Leave accrues monthly at a rate of 1.67 days per completed month of active service. Part-time employees receive pro-rated leave based on contracted weekly hours.",
                "Employees can carry forward up to a maximum of 5 unused leave days into the following calendar year, which must be utilized before March 31 (end of Q1). Any remaining carryover days beyond 5 days will be forfeited without monetary compensation.",
                "All planned annual leave requests exceeding 3 consecutive days must be submitted through the HR portal at least 2 weeks in advance and approved by the direct manager.",
            ],
            [
                "## 2. Sick Leave and Medical Absences",
                "Employees receive 10 paid sick days per calendar year. Sick leave is allocated in full on January 1st each year (or pro-rated upon start date).",
                "If an employee is absent due to illness for more than 3 consecutive working days, an official medical certificate signed by a licensed healthcare provider must be provided to People Operations upon return.",
                "## 3. Bereavement Leave",
                "Employees are granted up to 5 consecutive paid days off for the death of an immediate family member (spouse, child, parent, sibling). For extended relatives, 2 paid days are provided.",
            ],
            [
                "## 4. Parental and Family Caregiver Leave",
                "Primary caregivers are eligible for 16 weeks of 100% paid parental leave following the birth, adoption, or foster placement of a child. Secondary caregivers are entitled to 6 weeks of fully paid leave.",
                "Employees must complete at least 6 consecutive months of employment before becoming eligible for paid parental leave benefits.",
                "## 5. Unpaid Personal Leave",
                "Employees may request unpaid leaves of absence for personal emergencies or educational sabbaticals up to 90 calendar days. Approval is subject to Department Director and Head of HR consent.",
            ],
        ],
    )

    # 2. Remote Work Policy
    create_policy_pdf(
        "remote_work_policy.pdf",
        "Remote and Hybrid Work Policy",
        [
            [
                "## 1. Hybrid Work Framework",
                "The company operates under a hybrid working model. Eligible employees whose roles permit remote execution may work remotely up to 3 days per week, subject to direct manager approval.",
                "To foster team collaboration, Tuesday and Thursday are designated as mandatory in-office core collaboration days for all hybrid employees residing within 50 miles of a regional office.",
                "Core business working hours are 10:00 AM to 4:00 PM local time. All remote employees must remain reachable via Slack and email during these core hours.",
            ],
            [
                "## 2. Home Office Equipment Stipend",
                "Upon successful completion of the 90-day introductory probationary period, full-time employees are eligible for a one-time home office setup stipend of up to $500.",
                "Eligible items for reimbursement include ergonomic office chairs, external monitors, keyboards, mice, and desk risers. Receipts must be submitted via the expense portal within 45 days of purchase.",
                "## 3. Internet Connectivity Reimbursement",
                "Remote employees are eligible for a monthly home high-speed internet stipend of up to $50. Monthly bills must be uploaded for reimbursement by the 15th of the subsequent month.",
                "## 4. Security and Data Protection for Remote Work",
                "Employees working remotely must always connect to the corporate VPN when accessing internal networks, code repositories, or customer data.",
            ],
        ],
    )

    # 3. Travel Policy
    create_policy_pdf(
        "travel_policy.pdf",
        "Corporate Business Travel Policy",
        [
            [
                "## 1. Travel Authorization Requirements",
                "All business travel must have prior written approval before booking tickets. Domestic travel requires Department Head approval at least 14 days in advance. International travel requires Vice President (VP) approval at least 30 days in advance.",
                "## 2. Air Travel Booking Guidelines",
                "Economy class is the standard travel booking class for all domestic and short-haul flights. Business class booking is only permitted for continuous commercial flight segments exceeding 6 hours duration.",
                "All bookings must be completed using the corporate travel management tool (Navan) to secure pre-negotiated corporate discounts.",
            ],
            [
                "## 3. Hotel Accommodations and Nightly Limits",
                "The maximum reimbursable nightly rate for standard hotel rooms is $200 per night (excluding mandatory state/city taxes and resort fees). For designated Tier 1 high-cost cities (New York, San Francisco, London, Zurich), the nightly ceiling is increased to $320.",
                "## 4. Daily Meal Per Diem Allowance",
                "The daily meal per diem cap is $75 per day when traveling on overnight business trips. The recommended breakdown is: Breakfast: $15, Lunch: $25, Dinner: $35.",
                "Original itemized receipts are strictly required for any individual meal or transit expense exceeding $25.",
            ],
        ],
    )

    # 4. Expense Policy
    create_policy_pdf(
        "expense_policy.pdf",
        "Corporate Expense and Reimbursement Policy",
        [
            [
                "## 1. General Principles and Deadlines",
                "All business expenditures must be ordinary, reasonable, and necessary for business operations. Expense reports must be submitted within 30 calendar days of the date the expense was incurred.",
                "Late submissions past 60 days will be rejected and will not be reimbursed by Accounts Payable.",
                "## 2. Client Entertainment and Dining",
                "Client dining expenses are reimbursable up to a maximum of $100 per attendee including tax and tip. Alcohol is only eligible when accompanied by a full meal with external clients or partners. The names, titles, and company affiliations of all attendees must be documented on the receipt.",
            ],
            [
                "## 3. Non-Reimbursable Expenses",
                "The following items are strictly non-reimbursable under any circumstances: traffic or parking violations, personal grooming or spa services, airline seat upgrades without pre-approval, companion travel expenses, and personal streaming subscriptions.",
                "## 4. Corporate Credit Cards and Monthly Auditing",
                "Employees issued corporate credit cards must reconcile statements monthly. Inadvertent personal charges must be identified and reimbursed to the company within 10 business days.",
            ],
        ],
    )

    # 5. Security Policy
    create_policy_pdf(
        "security_policy.pdf",
        "Information Security and Data Protection Policy",
        [
            [
                "## 1. Password and Authentication Requirements",
                "Passwords for corporate accounts must be a minimum of 14 characters in length and include uppercase letters, lowercase letters, numbers, and special characters (!@#$%^&*).",
                "Passwords must be changed every 90 days. Reusing any of the previous 6 passwords is prohibited by the identity directory.",
                "Multi-Factor Authentication (MFA) via company-approved hardware tokens or authenticator apps is mandatory for all employee accounts and single-sign-on (SSO) systems. SMS-based 2FA is prohibited.",
            ],
            [
                "## 2. Workstation and Clean Desk Policy",
                "Employees must lock their workstation screens (Win + L or Control + Command + Q) whenever stepping away from their desk, whether in the office or in a public space.",
                "Sensitive physical documents, badges, and keys must not be left unattended and must be locked in drawers at the conclusion of the workday.",
                "## 3. Removable Media and External Storage",
                "Connecting unencrypted personal USB thumb drives, external hard disks, or unauthorized peripheral storage to corporate laptops is strictly prohibited. Exceptions require written authorization from the Chief Information Security Officer (CISO).",
            ],
        ],
    )

    # 6. Employee Handbook
    create_policy_pdf(
        "employee_handbook.pdf",
        "Employee Handbook and Code of Conduct",
        [
            [
                "## 1. Welcome and Company Culture",
                "Welcome to the team! Our company values transparency, innovation, mutual respect, and ethical conduct in all business dealings.",
                "We are committed to maintaining a diverse, inclusive, and harassment-free workplace. Any forms of discrimination or harassment are met with zero tolerance and result in immediate disciplinary action up to termination.",
                "## 2. Working Hours and Time Tracking",
                "The standard working week consists of 40 hours for full-time personnel, typically Monday through Friday. Flexible scheduling around core collaboration hours may be arranged with manager agreement.",
            ],
            [
                "## 3. Employee Health and Retirement Benefits",
                "Full-time employees are eligible for comprehensive medical, dental, and vision insurance coverage starting on the first day of the calendar month following their date of hire.",
                "The company offers a 401(k) retirement plan with an immediate employer match of 100% on employee contributions up to 4% of base salary. Employees become eligible to enroll in the 401(k) program after 90 days of continuous employment.",
                "## 4. Professional Development Stipend",
                "Each full-time team member receives an annual professional learning budget of $1,200 for courses, conferences, certifications, and technical books.",
            ],
            [
                "## 5. Performance Evaluations and Compensation Reviews",
                "Formal performance reviews take place twice per calendar year: mid-year in June and end-of-year in December.",
                "Annual merit-based compensation adjustments and promotional cycles take effect on February 1st of each calendar year following review completion.",
                "## 6. Grievance and Conflict Escalation",
                "Employees encountering workplace conflicts or ethical concerns should first approach their direct manager. If unresolved or inappropriate, matters should be escalated directly to People Operations or submitted anonymously via the Ethics Hotline.",
            ],
        ],
    )
    print("\nSuccessfully generated 6 realistic policy PDFs in knowledge_base/!\n")


if __name__ == "__main__":
    generate_all()
