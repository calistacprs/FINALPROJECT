from django.shortcuts import render

# Create your views here.
def create_employee(request):
    return render(request, 'payroll_app/create_employee.html')