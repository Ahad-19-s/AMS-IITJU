import pandas as pd
import numpy as np
import random

TOTAL_RECORDS = 5000
CLASS_DAYS = 24


semesters = [
    "1st Year - Sem 1", "1st Year - Sem 2",
    "2nd Year - Sem 1", "2nd Year - Sem 2",
    "3rd Year - Sem 1", "3rd Year - Sem 2",
    "4th Year - Sem 1", "4th Year - Sem 2"
]


student_names = ["Tashin Tuhin", "Ahad Ali", "Shibay Yadav", "Rakib Hasan", "Nadia Islam", "Karim Uddin"]

data = []

print("🔄 Generating 5000 Logical Data Points...")

for i in range(TOTAL_RECORDS):
    
    student_type = np.random.choice(['good', 'average', 'weak'], p=[0.4, 0.4, 0.2])
    
    student_name = np.random.choice(student_names)
    semester = np.random.choice(semesters)
    
    
    if student_type == 'good':
      
        attendance = np.random.randint(20, 25) # 20-24
        assignment = np.random.randint(8, 11)  # 8-10
        tutorial = np.random.randint(15, 21)   # 15-20
        incourse = np.random.randint(30, 41)   # 30-40
        final = np.random.randint(45, 61)      # 45-60
        
    elif student_type == 'average':
      
        attendance = np.random.randint(12, 21) # 12-20
        assignment = np.random.randint(5, 9)   # 5-8
        tutorial = np.random.randint(10, 16)   # 10-15
        incourse = np.random.randint(20, 31)   # 20-30
        final = np.random.randint(30, 46)      # 30-45
        
    else: # weak
       
        attendance = np.random.randint(0, 13)  # 0-12
        assignment = np.random.randint(0, 6)   # 0-5
        tutorial = np.random.randint(0, 11)    # 0-10
        incourse = np.random.randint(0, 21)    # 0-20
        final = np.random.randint(0, 31)       # 0-30

   
    total_marks = assignment + tutorial + incourse + final
    
    
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
    
    
    if gpa < 2.50 or attendance < 12:
        risk_status = "High Risk"
    elif gpa < 3.00:
        risk_status = "Medium Risk"
    else:
        risk_status = "Safe"

  
    data.append([
        student_name, semester, attendance, assignment, 
        tutorial, incourse, final, gpa, total_marks, risk_status
    ])


columns = [
    'Student_Name', 'Semester', 'Attendance', 'Assignment', 
    'Tutorial', 'Incourse', 'Final', 'GPA', 'Total_Marks', 'Risk_Status'
]
df = pd.DataFrame(data, columns=columns)


df.to_csv('student_performance.csv', index=False)
print(f"✅ Successfully created 'student_performance.csv' with {TOTAL_RECORDS} records!")
print(df.head()) 