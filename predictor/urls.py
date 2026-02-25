from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),      # ওয়েবসাইটের মূল পেজ হবে ড্যাশবোর্ড
    path('predict/', views.home, name='predict'),     # প্রেডিক্ট করার ফর্ম থাকবে এখানে
]