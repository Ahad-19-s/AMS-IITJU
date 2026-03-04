from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('students/', views.student_list, name='students'),
    path('student/<str:student_id>/', views.student_profile, name='student_profile'),
    path('ai-dashboard/', views.ai_dashboard, name='ai_dashboard'),
    
   
    path('reports/', views.reports, name='reports'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
    path('add-data/', views.add_data, name='add_data'),
     path('add-data/student/', views.add_student, name='add_student'),
    path('add-data/course/', views.add_course, name='add_course'),
    path('add-data/record/', views.add_academic_record, name='add_academic_record'),
    path('add-data/score/', views.add_subject_score, name='add_subject_score'),
    path('student/<int:student_id>/', views.student_profile, name='student_profile'),

   
    path('settings/', views.admin_settings, name='admin_settings'),
]

