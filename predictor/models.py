from django.db import models

# ১. স্টুডেন্টের বেসিক তথ্য
class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True, verbose_name="Student ID")  # যেমন: 1957
    name = models.CharField(max_length=100, verbose_name="Full Name")
    
    def __str__(self):
        return f"{self.name} ({self.student_id})"

# ২. সেমিস্টার অনুযায়ী স্টুডেন্টের রেজাল্ট
class AcademicRecord(models.Model):
    # সেমিস্টার ফিক্সড অপশন (ড্রপডাউনের জন্য এবং সর্টিং ঠিক রাখার জন্য)
    SEMESTER_CHOICES = [
        ('1-1', '1-1'),
        ('1-2', '1-2'),
        ('2-1', '2-1'),
        ('2-2', '2-2'),
        ('3-1', '3-1'),
        ('3-2', '3-2'),
        ('4-1', '4-1'),
        ('4-2', '4-2'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='records')
    semester = models.CharField(max_length=5, choices=SEMESTER_CHOICES, verbose_name="Semester") 
    
    # গ্রাফ এবং AI-এর জন্য প্রয়োজনীয় ৬টি ডাটা ফিল্ড
    attendance = models.FloatField(help_text="Attendance % (0-100)", default=0.0)
    assignment = models.FloatField(help_text="Assignment Marks (0-100)", default=0.0)
    quiz = models.FloatField(help_text="Quiz Marks (0-100)", default=0.0)
    midterm = models.FloatField(help_text="Midterm Marks (0-100)", default=0.0)
    final = models.FloatField(help_text="Final Exam Marks (0-100)", default=0.0)
    gpa = models.FloatField(help_text="GPA (0.00 - 4.00)", default=0.0)

    class Meta:
        # একই সেমিস্টারের ডাটা যেন দুইবার এন্ট্রি না হয়
        unique_together = ('student', 'semester')
        # ডাটাবেস থেকে ডাটা আনার সময় অটোমেটিক সেমিস্টার অনুযায়ী সাজানো থাকবে
        ordering = ['semester']

    def __str__(self):
        return f"{self.student.student_id} - {self.semester}"
    
    # predictor/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# আগের মডেলগুলো (Student, AcademicRecord) যেমন আছে তেমনই থাকবে...

# ১. সাবজেক্টের তালিকা (যেমন: Physics, Math, OOP)
class Course(models.Model):
    SEMESTER_CHOICES = [
        ('1-1', '1st Year - Sem 1'), ('1-2', '1st Year - Sem 2'),
        ('2-1', '2nd Year - Sem 1'), ('2-2', '2nd Year - Sem 2'),
        ('3-1', '3rd Year - Sem 1'), ('3-2', '3rd Year - Sem 2'),
        ('4-1', '4th Year - Sem 1'), ('4-2', '4th Year - Sem 2'),
    ]
    name = models.CharField(max_length=100) # সাবজেক্টের নাম
    semester = models.CharField(max_length=5, choices=SEMESTER_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.semester})"

# ২. স্টুডেন্টের সাবজেক্ট ওয়াইজ মার্কস
class StudentSubjectScore(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    marks = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])

    def __str__(self):
        return f"{self.student.name} - {self.course.name}: {self.marks}"