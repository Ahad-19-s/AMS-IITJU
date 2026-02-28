import random
from django.core.management.base import BaseCommand
from predictor.models import Student, Course, StudentSubjectScore

class Command(BaseCommand):
    help = 'Populate database with REAL academic data from IIT, JU Syllabus'

    def handle(self, *args, **kwargs):
        self.stdout.write("Generating real academic data...")

        # ১. আসল সাবজেক্ট তৈরি করা (JU Syllabus অনুযায়ী)
        subjects = {
            '1-1': [
                'Structured Programming Language', 
                'Electrical Circuits', 
                'Physics', 
                'Engineering Mathematics-I', 
                'Communicative English'
            ],
            '1-2': [
                'Electronic Devices and Circuits', 
                'Object Oriented Programming', 
                'Engineering Mathematics-II', 
                'Discrete Mathematics', 
                'Bangladesh Studies'
            ],
            '2-1': [
                'Data Structures', 
                'Digital Logic Design', 
                'Data Communication & Networks', 
                'Numerical Analysis', 
                'Statistics and Probability'
            ],
            '2-2': [
                'Algorithm Analysis and Design', 
                'Analog and Digital Communication', 
                'Engineering Mathematics-III', 
                'Financial and Managerial Accounting', 
                'Innovation and Entrepreneurship'
            ],
            '3-1': [
                'Operating Systems', 
                'Database Management System', 
                'Software Engineering', 
                'Business Analytics & Visualization', 
                'Principles of Economics'
            ],
            '3-2': [
                'Internet and Web Technology', 
                'AI and Neural Networks', 
                'Software Architecture', 
                'Information and Data Security', 
                'Smart Sensors and IoT'
            ],
            '4-1': [
                'Cloud Computing and Web Services', 
                'Mobile Application Development', 
                'Computer Vision and Robotics', 
                'Cyber Security and ICT Auditing', 
                'Big Data Analytics'
            ],
            '4-2': [
                'Software Project Management', 
                'Machine Learning', 
                'Software QA & Documentation', 
                'Natural Language Processing', 
                'Research Methodology'
            ]
        }

        created_courses = []
        for sem, course_list in subjects.items():
            for name in course_list:
                # get_or_create ব্যবহার করছি যাতে ডুপ্লিকেট না হয়
                course, created = Course.objects.get_or_create(name=name, semester=sem)
                created_courses.append(course)

        self.stdout.write(f"✅ Verified/Created {len(created_courses)} real courses.")

        # ২. স্টুডেন্টদের জন্য র‍্যান্ডম মার্কস বসানো
        students = Student.objects.all()
        if not students.exists():
            self.stdout.write(self.style.ERROR("❌ No students found! Please add students first."))
            return

        score_count = 0
        for student in students:
            for course in created_courses:
                # র‍্যান্ডম মার্কস (৬০ থেকে ৯৫ এর মধ্যে)
                marks = random.randint(60, 95)
                
                # ১০% ক্ষেত্রে মার্কস কম দেওয়া (রিস্ক স্টুডেন্ট দেখানোর জন্য)
                if random.random() < 0.1: 
                    marks = random.randint(40, 58)

                # মার্কস আপডেট বা ক্রিয়েট করা
                obj, created = StudentSubjectScore.objects.update_or_create(
                    student=student,
                    course=course,
                    defaults={'marks': marks}
                )
                score_count += 1
        
        self.stdout.write(f"✅ Successfully updated {score_count} exam scores for {students.count()} students.")
        self.stdout.write(self.style.SUCCESS("🎉 Database populated with REAL subjects! Refresh your dashboard now."))