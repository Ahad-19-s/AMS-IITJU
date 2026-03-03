import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

print("🔄 Generating 5000 Data aligned with your requirements...")

np.random.seed(42)
n_samples = 5000

# ১. হুবহু আপনার সফল কোডের কলামগুলো জেনারেট করা হচ্ছে
data = {
    'Attendance': np.random.randint(0, 101, n_samples),  # 0-100 স্কেল
    'Assignment': np.random.randint(0, 11, n_samples),   # 0-10 স্কেল
    'Quiz':       np.random.randint(0, 16, n_samples),   # 0-15 স্কেল
    'Midterm':    np.random.randint(0, 31, n_samples),   # 0-30 স্কেল
    'Final':      np.random.randint(0, 41, n_samples),   # 0-40 স্কেল
    'Previous_GPA': np.random.uniform(0.0, 4.0, n_samples) # 0.0-4.0 স্কেল
}

df = pd.DataFrame(data)

# ২. লজিক সেট করা (যাতে উল্টাপাল্টা রেজাল্ট না আসে)
def get_risk_level(row):
    # সব মার্ক যোগ করা
    total_marks = row['Assignment'] + row['Quiz'] + row['Midterm'] + row['Final']
    
    # লজিক: যদি এটেন্ডেন্স ৬০% এর কম হয় অথবা জিপিএ ২.৫০ এর কম হয় -> High Risk
    if row['Attendance'] < 60 or row['Previous_GPA'] < 2.50 or total_marks < 40:
        return 'High Risk'
    else:
        return 'Safe'

df['Risk_Level'] = df.apply(get_risk_level, axis=1)

# ৩. ফিচার এবং টার্গেট আলাদা করা
# কলামের ক্রম (Order) ঠিক রাখা খুব জরুরি
feature_cols = ['Attendance', 'Assignment', 'Quiz', 'Midterm', 'Final', 'Previous_GPA']
X = df[feature_cols]
y = df['Risk_Level']

# ৪. মডেল ট্রেইনিং
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# ৫. টেস্ট রেজাল্ট
y_pred = model.predict(X_test)
print(f"✅ Model Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")

# ৬. মডেল সেভ করা (.pkl এক্সটেনশন সহ)
joblib.dump(model, 'risk_model.pkl')
print("💾 'risk_model.pkl' saved successfully!")

# ৭. লাইভ টেস্ট (আপনার দেওয়া খারাপ ছাত্রের ডাটা দিয়ে)
test_bad_student = pd.DataFrame([{
    'Attendance': 25, 
    'Assignment': 2, 
    'Quiz': 5, 
    'Midterm': 10, 
    'Final': 15,
    'Previous_GPA': 1.8
}])

# কলামের অর্ডার ঠিক করে প্রেডিকশন
prediction = model.predict(test_bad_student[feature_cols])[0]
print(f"\n🧪 Test Prediction for Bad Student: {prediction}")