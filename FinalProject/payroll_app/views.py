from django.shortcuts import get_object_or_404, redirect, render
from .models import Employee, Payslip

def create_employee(request):
    return render(request, 'payroll_app/create_employee.html')

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