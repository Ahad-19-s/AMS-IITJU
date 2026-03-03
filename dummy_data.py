import pandas as pd
import numpy as np
import random

# কনফিগারেশন
TOTAL_RECORDS = 5000
CLASS_DAYS = 24

# সেমিস্টার লিস্ট
semesters = [
    "1st Year - Sem 1", "1st Year - Sem 2",
    "2nd Year - Sem 1", "2nd Year - Sem 2",
    "3rd Year - Sem 1", "3rd Year - Sem 2",
    "4th Year - Sem 1", "4th Year - Sem 2"
]

# ছাত্রের নাম (স্যাম্পল)
student_names = ["Tashin Tuhin", "Ahad Ali", "Shibay Yadav", "Rakib Hasan", "Nadia Islam", "Karim Uddin"]

data = []

print("🔄 Generating 5000 Logical Data Points...")

for i in range(TOTAL_RECORDS):
    # ১. ছাত্রের ক্যাটাগরি ঠিক করা (যাতে ডাটা মিক্সড থাকে)
    # ৭০% ভালো ছাত্র, ৩০% দুর্বল ছাত্র তৈরি হবে
    student_type = np.random.choice(['good', 'average', 'weak'], p=[0.4, 0.4, 0.2])
    
    student_name = np.random.choice(student_names)
    semester = np.random.choice(semesters)
    
    # ২. নাম্বারিং লজিক (ক্যাটাগরি অনুযায়ী)
    if student_type == 'good':
        # ভালো ছাত্র: এটেন্ডেন্স বেশি, মার্কস বেশি
        attendance = np.random.randint(20, 25) # 20-24
        assignment = np.random.randint(8, 11)  # 8-10
        tutorial = np.random.randint(15, 21)   # 15-20
        incourse = np.random.randint(30, 41)   # 30-40
        final = np.random.randint(45, 61)      # 45-60
        
    elif student_type == 'average':
        # মাঝারি ছাত্র
        attendance = np.random.randint(12, 21) # 12-20
        assignment = np.random.randint(5, 9)   # 5-8
        tutorial = np.random.randint(10, 16)   # 10-15
        incourse = np.random.randint(20, 31)   # 20-30
        final = np.random.randint(30, 46)      # 30-45
        
    else: # weak
        # দুর্বল ছাত্র: এটেন্ডেন্স কম, মার্কস কম (Risk)
        attendance = np.random.randint(0, 13)  # 0-12
        assignment = np.random.randint(0, 6)   # 0-5
        tutorial = np.random.randint(0, 11)    # 0-10
        incourse = np.random.randint(0, 21)    # 0-20
        final = np.random.randint(0, 31)       # 0-30

    # ৩. টোটাল মার্কস ক্যালকুলেশন (Max 130)
    total_marks = assignment + tutorial + incourse + final
    
    # ৪. জিপিএ ক্যালকুলেশন (Percentage অনুযায়ী)
    # 130 এর মধ্যে কত পেল, তার ওপর ভিত্তি করে GPA
    percentage = (total_marks / 130) * 100
    
    if percentage >= 80: gpa = 4.00
    elif percentage >= 75: gpa = 3.75
    elif percentage >= 70: gpa = 3.50
    elif percentage >= 65: gpa = 3.25
    elif percentage >= 60: gpa = 3.00
    elif percentage >= 55: gpa = 2.75
    elif percentage >= 50: gpa = 2.50
    elif percentage >= 45: gpa = 2.25
    elif percentage >= 40: gpa = 2.00
    else: gpa = 0.00
    
    # ৫. Risk Status নির্ধারণ (Target Label)
    # জিপিএ ২.৫০ এর কম অথবা এটেন্ডেন্স ৫০% (১২ দিন) এর কম হলে Risk
    if gpa < 2.50 or attendance < 12:
        risk_status = "High Risk"
    elif gpa < 3.00:
        risk_status = "Medium Risk"
    else:
        risk_status = "Safe"

    # ডাটা লিস্টে যোগ করা
    data.append([
        student_name, semester, attendance, assignment, 
        tutorial, incourse, final, gpa, total_marks, risk_status
    ])

# ডাটাফ্রেম তৈরি
columns = [
    'Student_Name', 'Semester', 'Attendance', 'Assignment', 
    'Tutorial', 'Incourse', 'Final', 'GPA', 'Total_Marks', 'Risk_Status'
]
df = pd.DataFrame(data, columns=columns)

# CSV সেভ করা
df.to_csv('student_performance.csv', index=False)
print(f"✅ Successfully created 'student_performance.csv' with {TOTAL_RECORDS} records!")
print(df.head()) # প্রথম ৫টি রেকর্ড দেখাবে