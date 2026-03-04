from django.contrib import admin
from .models import Student, AcademicRecord, Course, StudentSubjectScore


admin.site.register(Student)
admin.site.register(AcademicRecord)
admin.site.register(Course)
admin.site.register(StudentSubjectScore)