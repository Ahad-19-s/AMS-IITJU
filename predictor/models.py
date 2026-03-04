from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


SEMESTER_CHOICES = [
    ('1-1', '1st Year - Sem 1'), ('1-2', '1st Year - Sem 2'),
    ('2-1', '2nd Year - Sem 1'), ('2-2', '2nd Year - Sem 2'),
    ('3-1', '3rd Year - Sem 1'), ('3-2', '3rd Year - Sem 2'),
    ('4-1', '4th Year - Sem 1'), ('4-2', '4th Year - Sem 2'),
]

BATCH_CHOICES = [
    ('Batch-51', 'Batch 51'), ('Batch-52', 'Batch 52'),
    ('Batch-53', 'Batch 53'), ('Batch-54', 'Batch 54'),
]


class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True, verbose_name="Student ID")
    name = models.CharField(max_length=100, verbose_name="Full Name")
    batch = models.CharField(max_length=20, choices=BATCH_CHOICES, verbose_name="Batch")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.student_id})"


class Course(models.Model):
    course_code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=100)
    credit = models.FloatField(default=3.0)
    semester = models.CharField(max_length=5, choices=SEMESTER_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.course_code}: {self.title}"


class AcademicRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES)
    attendance = models.FloatField(help_text="Attendance percentage (0-100)")
    assignment = models.FloatField(default=0.0)
    quiz = models.FloatField(default=0.0)
    final = models.FloatField(default=0.0)
    gpa = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(4.0)], help_text="Semester GPA")

    class Meta:
        unique_together = ('student', 'semester')
        ordering = ['student', 'semester']

    def __str__(self):
        return f"{self.student.student_id} - {self.semester} (GPA: {self.gpa})"


class StudentSubjectScore(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='subject_scores')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    marks = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0.0)
    grade = models.CharField(max_length=2, blank=True, null=True, help_text="Letter Grade (A+, B, etc.)")
    grade_point = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(4.0)], default=0.0)
    
    def __str__(self):
        return f"{self.student.name} - {self.course.course_code}: {self.marks}"