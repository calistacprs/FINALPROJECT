from django.shortcuts import get_object_or_404, redirect, render
from .models import Employee, Payslip, Account
from django.db import transaction
from django.db.models import F
from django.contrib import messages
import calendar

current_user = None

def payslips(request):
    global current_user

    if current_user is None:
        return redirect('login')  
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

        month_number = months.index(month) + 1
        last_day = calendar.monthrange(int(year), month_number)[1]

        # cycle 1 dates
        if(pay_cycle == "1"):
            date_range = "1-15"
        # cycle 2 dates
        else:
            date_range = "16-" + str(last_day)

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

                # cycle 1 computation
                if(pay_cycle == "1"):
                    pag_ibig = 100
                    taxable_amount = cycle_rate + allowance + overtime - pag_ibig
                    deductions_tax = taxable_amount * 0.20
                    total_pay = taxable_amount - deductions_tax
                # cycle 2 computation
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

                employee.resetOvertime()

        if(message != ""):
            payslip_objects = Payslip.objects.all()
            return render(request, 'payroll_app/payslips.html', {
                'employees': employee_objects,
                'payslips': payslip_objects,
                'months': months,
                'message': message,
                'current_user': current_user
            })

        return redirect('payslips')

    else:
        return render(request, 'payroll_app/payslips.html', {
            'employees': employee_objects,
            'payslips': payslip_objects,
            'months': months,
            'message': message,
            'current_user': current_user
        })


def view_payslip(request, pk):
    if current_user is None:
        return redirect('login') 
    
    payslip = get_object_or_404(Payslip, pk=pk)
    return render(request, 'payroll_app/view_payslip.html', {'payslip': payslip, 'current_user': current_user})

def employees(request):
    global current_user

    if current_user is None:
        return redirect('login') 
    
    query = (request.GET.get('q') or "").strip()
    
    if query:
        if query.isdigit():
            # search by ID
            employees = Employee.objects.filter(id_number__icontains=query)
        else:
            # search by name
            employees = Employee.objects.filter(name__icontains=query)

        employees = employees.order_by('name')
    else:
        employees = Employee.objects.all().order_by('name')

    return render(request, 'payroll_app/employees.html', {
        'employees': employees,
        'query': query,
        'current_user': current_user})

def create_employee(request):
    global current_user

    if current_user is None:
        return redirect('login') 
    
    if request.method == "POST":
        name = (request.POST.get('name') or "").strip()
        id_number = (request.POST.get('id_number') or "").strip()
        
        # ID must be numbers only (extra preventive measures)
        if not id_number.isdigit():
            messages.error(request, "ID Number must contain numbers only.")
            return render(request, 'payroll_app/create_employee.html')

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
            return render(request, 'payroll_app/create_employee.html')

        Employee.objects.create(
            name=name,
            id_number=id_number,
            rate=rate,
            allowance=allowance,
            overtime_pay=0
        )

        messages.success(request, "Employee created successfully.")
        return redirect('employees')

    return render(request, 'payroll_app/create_employee.html', {
        'current_user': current_user})

def update_employee(request, id):
    global current_user

    if current_user is None:
        return redirect('login') 
    
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

    return render(request, 'payroll_app/update_employee.html', {'emp': emp, 'current_user': current_user})

def delete_employee(request, id):
    global current_user

    if current_user is None:
        return redirect('login')
     
    if request.method == "POST":
        emp = get_object_or_404(Employee, id=id)
        emp.delete()
        messages.success(request, "Employee deleted.")
    return redirect('employees')


# add overtime 
def add_overtime(request, id):
    global current_user

    if current_user is None:
        return redirect('login') 
    
    if request.method == "POST":
        emp = get_object_or_404(Employee, id=id)

        try:
            hours = float(request.POST.get("hours") or 0)
        except ValueError:
            messages.error(request, "Hours must be a valid number.")
            return redirect('employees')

        # prevent negative values
        if hours <= 0:
            messages.error(request, "Enter a valid number of hours.")
            return redirect('employees')

        # if overtime is empty, treat it as zero so calculations dont break
        if emp.overtime_pay is None:
            emp.overtime_pay = 0
            emp.save()

        # computes overtime
        overtime = (emp.rate / 160) * 1.5 * hours

        # safe update using F() --> extra measure 
        Employee.objects.filter(id=emp.id).update(
            overtime_pay=F('overtime_pay') + overtime
        )

        messages.success(request, "Overtime added.")

    return redirect('employees')

def login_view(request):
    global current_user
    message = request.GET.get("message", "")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        account = Account.objects.filter(username=username, password=password).first()

        if account:
            current_user = account
            return redirect('employees')
        else:
            message = "Invalid login"

    return render(request, 'payroll_app/login.html', {
        'message': message,
        'current_user': current_user
    })


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        existing_account = Account.objects.filter(username=username).first()

        if existing_account:
            return render(request, 'payroll_app/signup.html', {
                'message': 'Account already exists'
            })

        Account.objects.create(username=username, password=password)

        return redirect('/?message=Account created successfully')

    return render(request, 'payroll_app/signup.html')


def manage_account(request, pk):
    global current_user

    if current_user is None:
        return redirect('login') 
    
    user_account = get_object_or_404(Account, pk=pk)

    return render(request, 'payroll_app/manage_account.html', {
        'user': user_account,
        'current_user': current_user
    })


def delete_account(request, pk):
    global current_user

    Account.objects.filter(pk=pk).delete()
    current_user = None

    return redirect('login')


def logout_view(request):
    global current_user
    current_user = None

    return redirect('login')


def change_password(request, pk):
    global current_user
    
    if current_user is None:
        return redirect('login') 
    
    account = get_object_or_404(Account, pk=pk)
    message = ""

    if request.method == "POST":
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if current_password != account.password:
            message = "Current password is incorrect"

        elif new_password != confirm_password:
            message = "New passwords do not match"

        else:
            account.password = new_password
            account.save()

            return redirect('manage_account', pk=account.pk)

    return render(request, 'payroll_app/change_password.html', {
        'account': account,
        'display': message,
        'current_user': current_user
    })

def delete_payslip(request, pk):
    global current_user

    if current_user is None:
        return redirect('login')

    Payslip.objects.filter(pk=pk).delete()
    return redirect('payslips')