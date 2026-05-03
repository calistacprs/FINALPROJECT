from django.urls import path
from . import views

urlpatterns = [
    path('employees/', views.employees, name='employees'),
    path('update_employee/<int:id>/', views.update_employee, name='update_employee'),

    path('create/', views.create_employee, name='create_employee'),
    path('update/<int:id>/', views.update_employee, name='update_employee'),
    path('delete/<int:id>/', views.delete_employee, name='delete_employee'),

    path('add-overtime/<int:id>/', views.add_overtime, name='add_overtime'),
    
    path('', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('account/<int:pk>/', views.manage_account, name='manage_account'),
    path('account/delete/<int:pk>/', views.delete_account, name='delete_account'),
    path('account/change-password/<int:pk>/', views.change_password, name='change_password'),

    path('payslips/', views.payslips, name='payslips'),
    path('payslip/<int:pk>/', views.view_payslip, name='view_payslip'),
]