from django.urls import path
from . import views

urlpatterns = [
    path('', views.employees, name='employees'),

    path('create/', views.create_employee, name='create_employee'),
    path('update/<int:id>/', views.update_employee, name='update_employee'),
    path('delete/<int:id>/', views.delete_employee, name='delete_employee'),

    path('add-overtime/<int:id>/', views.add_overtime, name='add_overtime'),
]