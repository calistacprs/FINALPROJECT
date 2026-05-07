from django.contrib import admin
from .models import Account, Employee, Payslip

admin.site.register(Account)
admin.site.register(Employee)
admin.site.register(Payslip)