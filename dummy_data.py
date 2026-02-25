import pandas as pd
import numpy as np

np.random.seed(42)
n_students = 5000

# real dataset
attendance = np.random.randint(40, 100, n_students)
assignment = np.random.randint(30, 100, n_students)
quiz = np.random.randint(20, 100, n_students)
midterm = np.random.randint(20, 100, n_students)
final = np.random.randint(20, 100, n_students)
# CGPA 2.00 from 4.00 
previous_gpa = np.round(np.random.uniform(2.0, 4.0, n_students), 2)

data = {
    'Student_ID': range(1, n_students + 1),
    'Attendance': attendance,
    'Assignment': assignment,
    'Quiz': quiz,
    'Midterm': midterm,
    'Final': final,
    'Previous_GPA': previous_gpa
}
df = pd.DataFrame(data)

# Average Score ক্যালকুলেশন (ভার্সিটির নিয়মে Weighted Average)
# ধরি: Att(10%) + Ass(10%) + Quiz(10%) + Mid(30%) + Final(40%)
df['Average_Score'] = (df['Attendance']*0.10 + df['Assignment']*0.10 + 
                       df['Quiz']*0.10 + df['Midterm']*0.30 + df['Final']*0.40)
df['Average_Score'] = np.round(df['Average_Score'], 2)

# Risk Level realstic
def calculate_risk(row):
    if row['Average_Score'] < 50 or row['Attendance'] < 60:
        return 'High'
    elif 50 <= row['Average_Score'] <= 65 or row['Previous_GPA'] < 2.50:
        return 'Medium'
    else:
        return 'Low'

df['Risk_Level'] = df.apply(calculate_risk, axis=1)

# ডাটাগুলো CSV ফাইলে সেভ করা
df.to_csv('student_data.csv', index=False)
print("there are 5000 student dataset successfull")