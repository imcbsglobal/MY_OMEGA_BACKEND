from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from io import BytesIO
from django.utils.timezone import now


def get_employee_name(employee):
    """Safely get employee name with multiple fallbacks"""
    if not employee:
        return 'Unknown'
    
    # Try get_full_name() method first
    if hasattr(employee, 'get_full_name') and callable(employee.get_full_name):
        try:
            name = employee.get_full_name()
            if name and name.strip():
                return name
        except:
            pass
    
    # Try full_name attribute
    if hasattr(employee, 'full_name') and employee.full_name:
        return employee.full_name
    
    # Try name attribute
    if hasattr(employee, 'name') and employee.name:
        return employee.name
    
    # Try first_name + last_name
    first = getattr(employee, 'first_name', '')
    last = getattr(employee, 'last_name', '')
    if first or last:
        return f"{first} {last}".strip()
    
    # Try user relationship
    if hasattr(employee, 'user') and employee.user:
        user = employee.user
        if hasattr(user, 'get_full_name') and callable(user.get_full_name):
            try:
                name = user.get_full_name()
                if name and name.strip():
                    return name
            except:
                pass
        
        if hasattr(user, 'name') and user.name:
            return user.name
        
        first = getattr(user, 'first_name', '')
        last = getattr(user, 'last_name', '')
        if first or last:
            return f"{first} {last}".strip()
    
    # Fallback to employee_id or id
    emp_id = getattr(employee, 'employee_id', None) or getattr(employee, 'id', None)
    return f'Employee {emp_id}' if emp_id else 'Unknown'


def generate_payslip_pdf(payroll):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()
    elements = []

    # ================= HEADER =================
    elements.append(Paragraph("<b>Omega</b>", styles["Title"]))
    elements.append(Paragraph("588, Eastshore Chennai Tamil Nadu, 600031 India", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph(
            f"<b>Payslip for the month of {payroll.month}, {payroll.year}</b>",
            styles["Heading2"]
        )
    )
    elements.append(Spacer(1, 12))

    # ================= EMPLOYEE INFO =================
    emp = payroll.employee
    employee_name = get_employee_name(emp)
    designation = getattr(emp, "designation", "—") or "—"

    emp_data = [
        ["Employee Name", employee_name, "Employee Net Pay",
         f"₹{payroll.net_pay:,.2f}"],
        ["Designation", designation, "Paid Days",
         f"{payroll.attendance_days}"],
        ["Pay Date", now().strftime("%d/%m/%Y"), "LOP Days",
         f"{max(payroll.working_days - payroll.attendance_days, 0)}"],
    ]

    emp_table = Table(emp_data, colWidths=[70, 120, 80, 100])
    emp_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("SPAN", (1, 0), (1, 0)),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 16))

    # ================= EARNINGS =================
    earnings = [
        ["EARNINGS", "AMOUNT", "YTD"]
    ]

    earnings.append(["Basic", f"₹{payroll.earned_salary:,.2f}", f"₹{payroll.earned_salary:,.2f}"])

    for a in payroll.allowance_items.all():
        earnings.append([a.allowance_type, f"₹{a.amount:,.2f}", f"₹{a.amount:,.2f}"])

    earnings.append(["<b>Gross Earnings</b>", f"<b>₹{payroll.gross_pay:,.2f}</b>", ""])

    earn_table = Table(earnings, colWidths=[170, 80, 80])
    earn_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f4f8")),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
    ]))

    # ================= DEDUCTIONS =================
    deductions = [
        ["DEDUCTIONS", "AMOUNT", "YTD"]
    ]
    
    deductions.append(["Income Tax", f"₹{payroll.tax:,.2f}", f"₹{payroll.tax:,.2f}"])

    for d in payroll.deduction_items.all():
        deductions.append([d.deduction_type, f"₹{d.amount:,.2f}", f"₹{d.amount:,.2f}"])

    deductions.append(["<b>Total Deductions</b>", f"<b>₹{payroll.deductions + payroll.tax:,.2f}</b>", ""])

    ded_table = Table(deductions, colWidths=[170, 80, 80])
    ded_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f4f8")),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
    ]))

    # ================= REIMBURSEMENTS =================
    reimbursements = [
        ["REIMBURSEMENTS", "AMOUNT", "YTD"]
    ]
    
    total_reimbursement = 0
    for a in payroll.allowance_items.all():
        reimbursements.append([f"{a.allowance_type} Reimbursement", f"₹{a.amount:,.2f}", f"₹{a.amount:,.2f}"])
        total_reimbursement += float(a.amount)

    if total_reimbursement > 0:
        reimbursements.append(["<b>Total Reimbursement</b>", f"<b>₹{total_reimbursement:,.2f}</b>", ""])
    else:
        reimbursements.append(["No reimbursements", "₹0.00", "₹0.00"])

    reimb_table = Table(reimbursements, colWidths=[170, 80, 80])
    reimb_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f4f8")),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
    ]))

    # Side-by-side tables in a single row
    elements.append(
        Table([[earn_table, ded_table, reimb_table]], colWidths=[170, 170, 170])
    )
    elements.append(Spacer(1, 20))

    # ================= NET PAY =================
    elements.append(
        Paragraph(
            f"<b>NET PAY (Gross Earnings - Total Deductions) + Reimbursements</b>",
            styles["Normal"]
        )
    )
    elements.append(Spacer(1, 8))
    
    elements.append(
        Paragraph(
            f"<b>₹{payroll.net_pay:,.2f}</b>",
            styles["Heading1"]
        )
    )

    elements.append(Spacer(1, 16))
    
    # Total Net Payable in words
    elements.append(
        Paragraph(
            f"Total Net Payable ₹{payroll.net_pay:,.2f} (Rupees {number_to_words(payroll.net_pay)})",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph(
            "This is a system generated payslip and does not require signature.",
            styles["Italic"]
        )
    )

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def number_to_words(num):
    """Simple number to words converter (placeholder - you may want a better implementation)"""
    # This is a simplified version
    return f"{int(num)} only"