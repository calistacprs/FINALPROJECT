from django.shortcuts import get_object_or_404, redirect, render
from .models import Employee, Payslip
from django.db import transaction
from django.db.models import F
from django.contrib import messages

def payslips(request):
    employee_objects = Employee.objects.all()
    payslip_objects = Payslip.objects.all()

    months = [
        "January", "February", "March", "April",
        "May", "June", "July", "August",
        "September", "October", "November", "December"
    ]

    message = ""

    if(request.method == "POST"):
        payroll_for = request.POST.get("payroll_for")
        month = request.POST.get("month")
        year = request.POST.get("year")
        pay_cycle = request.POST.get("pay_cycle")

        if(pay_cycle == "1"):
            date_range = "1-15"
        else:
            date_range = "16-30"

        if(payroll_for == "all"):
            selected_employees = Employee.objects.all()
        else:
            selected_employees = Employee.objects.filter(id_number=payroll_for)

        for employee in selected_employees:
            existing_payslip = Payslip.objects.filter(
                id_number=employee,
                month=month,
                year=year,
                pay_cycle=pay_cycle
            ).first()

            if(existing_payslip):
                message = "Payslip already exists for one or more selected employees."
            
            else:
                rate = float(employee.rate)
                cycle_rate = rate / 2

                if(employee.allowance == None):
                    allowance = 0
                else:
                    allowance = float(employee.allowance)

                if(employee.overtime_pay == None):
                    overtime = 0
                else:
                    overtime = float(employee.overtime_pay)

                pag_ibig = 0
                deductions_health = 0
                sss = 0

                if(pay_cycle == "1"):
                    pag_ibig = 100
                    taxable_amount = cycle_rate + allowance + overtime - pag_ibig
                    deductions_tax = taxable_amount * 0.20
                    total_pay = taxable_amount - deductions_tax
                else:
                    deductions_health = rate * 0.04
                    sss = rate * 0.045
                    taxable_amount = cycle_rate + allowance + overtime - deductions_health - sss
                    deductions_tax = taxable_amount * 0.20
                    total_pay = taxable_amount - deductions_tax

                Payslip.objects.create(
                    id_number=employee,
                    month=month,
                    date_range=date_range,
                    year=year,
                    pay_cycle=pay_cycle,
                    rate=rate,
                    earnings_allowance=allowance,
                    deductions_tax=deductions_tax,
                    deductions_health=deductions_health,
                    pag_ibig=pag_ibig,
                    sss=sss,
                    overtime=overtime,
                    total_pay=total_pay
                )

                employee.overtime_pay = 0
                employee.save()

        if(message != ""):
            payslip_objects = Payslip.objects.all()
            return render(request, 'payroll_app/payslips.html', {
                'employees': employee_objects,
                'payslips': payslip_objects,
                'months': months,
                'message': message
            })

        return redirect('payslips')

    else:
        return render(request, 'payroll_app/payslips.html', {
            'employees': employee_objects,
            'payslips': payslip_objects,
            'months': months,
            'message': message
        })


def view_payslip(request, pk):
    payslip = get_object_or_404(Payslip, pk=pk)
    return render(request, 'payroll_app/view_payslip.html', {'payslip': payslip})

def employees(request):
    employees = Employee.objects.all().order_by('name')
    return render(request, 'payroll_app/employees.html', {'employees': employees})

def create_employee(request):
    if request.method == "POST":
        name = (request.POST.get('name') or "").strip()
        id_number = (request.POST.get('id_number') or "").strip()

        # validate required fields
        if not name or not id_number:
            messages.error(request, "Name and ID Number are required.")
            return redirect('create_employee')

        # parse numbers safely
        try:
            rate = float(request.POST.get('rate') or 0)
            allowance = float(request.POST.get('allowance') or 0)
        except ValueError:
            messages.error(request, "Rate and Allowance must be valid numbers.")
            return redirect('create_employee')

        # prevent negative values
        if rate < 0 or allowance < 0:
            messages.error(request, "Rate and Allowance cannot be negative.")
            return redirect('create_employee')

        # prevent duplicate ID numbers
        if Employee.objects.filter(id_number=id_number).exists():
            messages.error(request, "ID Number already exists.")
            return redirect('create_employee')

        Employee.objects.create(
            name=name,
            id_number=id_number,
            rate=rate,
            allowance=allowance,
            overtime_pay=0
        )

        messages.success(request, "Employee created successfully.")
        return redirect('employees')

    return render(request, 'payroll_app/create_employee.html')

def update_employee(request, id):
    emp = get_object_or_404(Employee, id=id)

    if request.method == "POST":
        name = (request.POST.get('name') or "").strip()
        id_number = (request.POST.get('id_number') or "").strip()

        if not name or not id_number:
            messages.error(request, "Name and ID Number are required.")
            return redirect('update_employee', id=id)

        try:
            rate = float(request.POST.get('rate') or 0)
            allowance = float(request.POST.get('allowance') or 0)
        except ValueError:
            messages.error(request, "Rate and Allowance must be valid numbers.")
            return redirect('update_employee', id=id)

        if rate < 0 or allowance < 0:
            messages.error(request, "Rate and Allowance cannot be negative.")
            return redirect('update_employee', id=id)

        # prevent duplicate ID numbers (excluding current employee)
        if Employee.objects.filter(id_number=id_number).exclude(id=id).exists():
            messages.error(request, "ID Number already exists.")
            return redirect('update_employee', id=id)

        emp.name = name
        emp.id_number = id_number
        emp.rate = rate
        emp.allowance = allowance
        emp.save()

        messages.success(request, "Employee updated.")
        return redirect('employees')

    return render(request, 'payroll_app/update_employee.html', {'emp': emp})

def delete_employee(request, id):
    if request.method == "POST":
        emp = get_object_or_404(Employee, id=id)
        emp.delete()
        messages.success(request, "Employee deleted.")
    return redirect('employees')


# add overtime 
@transaction.atomic
def add_overtime(request, id):
    if request.method == "POST":
        emp = get_object_or_404(Employee, id=id)

        try:
            hours = float(request.POST.get("hours") or 0)
        except ValueError:
            messages.error(request, "Hours must be a valid number.")
            return redirect('employees')

        # prevent negative or absurd values
        if hours <= 0 or hours > 1000:
            messages.error(request, "Enter a valid number of hours.")
            return redirect('employees')

        # ensure field is not None
        if emp.overtime_pay is None:
            emp.overtime_pay = 0

        overtime = (emp.rate / 160) * 1.5 * hours

        # use F() to avoid race conditions (simultaneous updates)
        Employee.objects.filter(id=emp.id).update(
            overtime_pay=F('overtime_pay') + overtime
        )

        messages.success(request, "Overtime added.")

    return redirect('employees')