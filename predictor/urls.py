from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('students/', views.student_list, name='students'),
    path('student/<str:student_id>/', views.student_profile, name='student_profile'),
    path('ai-dashboard/', views.ai_dashboard, name='ai_dashboard'),
    
    # 👇 এই লাইনটি মিসিং আছে, এটি যোগ করুন:
    path('reports/', views.reports, name='reports'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
]