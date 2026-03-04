import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


n_samples = 5000
np.random.seed(42)

data = {
    'Attendance': np.random.randint(0, 101, n_samples),   
    'Assignment': np.random.randint(0, 11, n_samples),    
    'Quiz':       np.random.randint(0, 21, n_samples),    
    'Final':      np.random.randint(0, 61, n_samples),    
    'Previous_GPA': np.random.uniform(0.0, 4.0, n_samples)
}

df = pd.DataFrame(data)


def get_risk_level(row):
    
    if row['Attendance'] < 50 or row['Previous_GPA'] < 2.0 or (row['Assignment'] + row['Quiz'] + row['Final']) < 40:
        return 'High Risk'
    else:
        return 'Safe'

df['Risk_Level'] = df.apply(get_risk_level, axis=1)

feature_cols = ['Attendance', 'Assignment', 'Quiz', 'Final', 'Previous_GPA']
X = df[feature_cols]
y = df['Risk_Level']


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


print("⏳ Training Model... Please wait.")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)


y_pred = model.predict(X_test)

print("\n" + "="*30)
print("📊 MODEL PERFORMANCE METRICS")
print("="*30)


acc = accuracy_score(y_test, y_pred)
print(f"✅ Accuracy: {acc * 100:.2f}%")


print("\n📝 Classification Report (Includes F1-Score):")
print(classification_report(y_test, y_pred))


model_filename = 'risk_model.pkl'
joblib.dump(model, model_filename)


current_directory = os.getcwd()
full_path = os.path.join(current_directory, model_filename)
print("="*30)
print(f"💾 Model Saved Successfully!")
print(f"📂 Location: {full_path}")
print("="*30)


test_sample = pd.DataFrame([{
    'Attendance': 40.0, 
    'Assignment': 5.0, 
    'Quiz': 10.0, 
    'Final': 20.0,
    'Previous_GPA': 1.5
}])

prediction = model.predict(test_sample[feature_cols])[0]
print(f"\n🧪 Test Prediction for sample student: {prediction}")
