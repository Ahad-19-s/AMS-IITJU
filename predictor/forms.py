from django import forms
from .models import Student, Course, AcademicRecord, StudentSubjectScore 
# লক্ষ্য করুন: এখানে কোনো "from .forms import..." লাইন থাকবে না

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['student_id', 'name', 'batch']
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'batch': forms.Select(attrs={'class': 'form-select'}),
        }

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_code', 'title', 'credit', 'semester']
        widgets = {
            'course_code': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'credit': forms.NumberInput(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
        }

# predictor/forms.py
from django import forms
from .models import AcademicRecord

class AcademicRecordForm(forms.ModelForm):
    class Meta:
        model = AcademicRecord
        fields = ['student', 'semester', 'attendance', 'assignment', 'quiz', 'midterm', 'final', 'gpa']
        # ফর্মটিকে সুন্দর করার জন্য উইজেট ব্যবহার করুন
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'attendance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Attendance %'}),
            'assignment': forms.NumberInput(attrs={'class': 'form-control'}),
            'quiz': forms.NumberInput(attrs={'class': 'form-control'}),
            'midterm': forms.NumberInput(attrs={'class': 'form-control'}),
            'final': forms.NumberInput(attrs={'class': 'form-control'}),
            'gpa': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SubjectScoreForm(forms.ModelForm):
    class Meta:
        model = StudentSubjectScore
        fields = ['student', 'course', 'marks', 'grade_point']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'grade_point': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }