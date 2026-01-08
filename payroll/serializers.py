# payroll/serializers.py - Fixed with defensive employee name handling

from rest_framework import serializers
from .models import Payroll, PayrollDeduction, PayrollAllowance


class PayrollDeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollDeduction
        fields = ['id', 'deduction_type', 'amount', 'description']


class PayrollAllowanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollAllowance
        fields = ['id', 'allowance_type', 'amount', 'description']


class PayrollSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.IntegerField(source='employee.id', read_only=True)
    employee_position = serializers.SerializerMethodField()
    deduction_items = PayrollDeductionSerializer(many=True, read_only=True)
    allowance_items = PayrollAllowanceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Payroll
        fields = [
            'id', 'employee_id', 'employee_name', 'employee_position', 'month', 'year',
            'salary', 'attendance_days', 'working_days', 'earned_salary', 'allowances',
            'gross_pay', 'deductions', 'tax', 'net_pay', 'status', 'paid_date',
            'created_at', 'updated_at', 'deduction_items', 'allowance_items'
        ]
        read_only_fields = ['earned_salary', 'gross_pay', 'tax', 'net_pay', 'created_at', 'updated_at']
    
    def get_employee_name(self, obj):
        """Get employee name safely - try multiple methods"""
        if not obj.employee:
            return 'Unknown'
        
        employee = obj.employee
        
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
    
    def get_employee_position(self, obj):
        """Get employee position/designation safely"""
        if not obj.employee:
            return 'N/A'
        
        employee = obj.employee
        
        # Try common field names for position
        for field in ['designation', 'position', 'job_title', 'title']:
            if hasattr(employee, field):
                value = getattr(employee, field)
                if value:
                    return value
        
        # Try job_info relationship
        if hasattr(employee, 'job_info') and employee.job_info:
            for field in ['designation', 'position', 'job_title', 'title']:
                if hasattr(employee.job_info, field):
                    value = getattr(employee.job_info, field)
                    if value:
                        return value
        
        return 'N/A'


class PayrollListSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Payroll
        fields = [
            'id', 'employee_name', 'month', 'year', 'gross_pay', 'tax', 'net_pay',
            'attendance_days', 'working_days', 'status', 'paid_date'
        ]
    
    def get_employee_name(self, obj):
        """Get employee name safely - same logic as PayrollSerializer"""
        if not obj.employee:
            return 'Unknown'
        
        employee = obj.employee
        
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
    


# ================= PAYSLIP PDF GENERATION =================

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from io import BytesIO
from django.utils.timezone import now


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

    # Header
    elements.append(Paragraph("<b>Zylker Corp</b>", styles["Title"]))
    elements.append(Paragraph(
        "588, Eastshore Chennai Tamil Nadu, 600031 India",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(
        f"<b>Payslip for {payroll.month} {payroll.year}</b>",
        styles["Heading2"]
    ))
    elements.append(Spacer(1, 12))

    emp = payroll.employee

    emp_data = [
        ["Employee Name", getattr(emp, "full_name", emp.name), "Net Pay",
         f"₹{payroll.net_pay:,.2f}"],
        ["Designation", getattr(emp, "designation", "—"), "Paid Days",
         payroll.attendance_days],
        ["Pay Date", now().strftime("%d/%m/%Y"), "LOP Days",
         max(payroll.working_days - payroll.attendance_days, 0)],
    ]

    emp_table = Table(emp_data, colWidths=[80, 140, 80, 100])
    emp_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
    ]))

    elements.append(emp_table)
    elements.append(Spacer(1, 16))

    earnings = [["EARNINGS", "AMOUNT"]]
    earnings.append(["Basic Salary", f"₹{payroll.earned_salary:,.2f}"])

    for a in payroll.allowance_items.all():
        earnings.append([a.allowance_type, f"₹{a.amount:,.2f}"])

    earnings.append(["Gross Earnings", f"₹{payroll.gross_pay:,.2f}"])

    deductions = [["DEDUCTIONS", "AMOUNT"]]

    for d in payroll.deduction_items.all():
        deductions.append([d.deduction_type, f"₹{d.amount:,.2f}"])

    deductions.append(["Income Tax", f"₹{payroll.tax:,.2f}"])
    deductions.append(
        ["Total Deductions", f"₹{payroll.deductions + payroll.tax:,.2f}"]
    )

    table = Table([[Table(earnings), Table(deductions)]], colWidths=[260, 260])
    elements.append(table)

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph(
            f"<b>Total Net Payable: ₹{payroll.net_pay:,.2f}</b>",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 12))
    elements.append(
        Paragraph(
            "This is a system generated payslip.",
            styles["Italic"]
        )
    )

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf






# ================= PAYSLIP PDF GENERATION =================
# This section goes at the BOTTOM of serializers.py
# Replace the existing generate_payslip_pdf function with this

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from io import BytesIO
from django.utils.timezone import now


def get_employee_name_for_pdf(employee):
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

    # Header
    elements.append(Paragraph("<b>Zylker Corp</b>", styles["Title"]))
    elements.append(Paragraph(
        "588, Eastshore Chennai Tamil Nadu, 600031 India",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(
        f"<b>Payslip for {payroll.month} {payroll.year}</b>",
        styles["Heading2"]
    ))
    elements.append(Spacer(1, 12))

    emp = payroll.employee
    employee_name = get_employee_name_for_pdf(emp)
    designation = getattr(emp, "designation", "—") or "—"

    emp_data = [
        ["Employee Name", employee_name, "Net Pay",
         f"₹{payroll.net_pay:,.2f}"],
        ["Designation", designation, "Paid Days",
         payroll.attendance_days],
        ["Pay Date", now().strftime("%d/%m/%Y"), "LOP Days",
         max(payroll.working_days - payroll.attendance_days, 0)],
    ]

    emp_table = Table(emp_data, colWidths=[80, 140, 80, 100])
    emp_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
    ]))

    elements.append(emp_table)
    elements.append(Spacer(1, 16))

    earnings = [["EARNINGS", "AMOUNT"]]
    earnings.append(["Basic Salary", f"₹{payroll.earned_salary:,.2f}"])

    for a in payroll.allowance_items.all():
        earnings.append([a.allowance_type, f"₹{a.amount:,.2f}"])

    earnings.append(["Gross Earnings", f"₹{payroll.gross_pay:,.2f}"])

    deductions = [["DEDUCTIONS", "AMOUNT"]]

    for d in payroll.deduction_items.all():
        deductions.append([d.deduction_type, f"₹{d.amount:,.2f}"])

    deductions.append(["Income Tax", f"₹{payroll.tax:,.2f}"])
    deductions.append(
        ["Total Deductions", f"₹{payroll.deductions + payroll.tax:,.2f}"]
    )

    table = Table([[Table(earnings), Table(deductions)]], colWidths=[260, 260])
    elements.append(table)

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph(
            f"<b>Total Net Payable: ₹{payroll.net_pay:,.2f}</b>",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 12))
    elements.append(
        Paragraph(
            "This is a system generated payslip.",
            styles["Italic"]
        )
    )

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf