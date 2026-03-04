import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score


from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier


print("🔄 Generating Synthetic Data...")
n_samples = 5000
np.random.seed(42)

data = {
    'Attendance': np.random.randint(0, 101, n_samples),   # 0-100%
    'Assignment': np.random.randint(0, 11, n_samples),    # 0-10
    'Quiz':       np.random.randint(0, 21, n_samples),    # 0-20
    'Final':      np.random.randint(0, 61, n_samples),    # 0-60
    'Previous_GPA': np.random.uniform(0.0, 4.0, n_samples)
}

df = pd.DataFrame(data)


def get_risk_level(row):
    total_marks = row['Assignment'] + row['Quiz'] + row['Final']
   
    if row['Attendance'] < 50 or row['Previous_GPA'] < 2.0 or total_marks < 40:
        return 1 # 'High Risk'
    else:
        return 0 # 'Safe'

df['Risk_Level'] = df.apply(get_risk_level, axis=1)

feature_cols = ['Attendance', 'Assignment', 'Quiz', 'Final', 'Previous_GPA']
X = df[feature_cols]
y = df['Risk_Level']


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


models = {
    "Logistic Regression": LogisticRegression(),
    "Decision Tree":       DecisionTreeClassifier(),
    "Random Forest":       RandomForestClassifier(n_estimators=100, random_state=42),
    "KNN":                 KNeighborsClassifier(n_neighbors=5)
}

best_model = None
best_f1 = 0.0  #
best_model_name = ""
best_scaler_needed = False

print("\n" + "="*80)
print(f"{'Model Name':<20} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
print("="*80)

for name, model in models.items():
   
    if name in ["Logistic Regression", "KNN"]:
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        scaler_used = True
    else:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        scaler_used = False
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"{name:<20} | {acc*100:.2f}%     | {prec:.4f}     | {rec:.4f}     | {f1:.4f}")
    
    if f1 > best_f1:
        best_f1 = f1
        best_model = model
        best_model_name = name
        best_scaler_needed = scaler_used


print("="*80)
print(f"🏆 WINNER MODEL: {best_model_name}")
print(f"📊 Best F1 Score: {best_f1:.4f}")
print("="*80)


joblib.dump(best_model, 'academic_risk_model.pkl')
print(f"💾 Model Saved: academic_risk_model.pkl")


joblib.dump(scaler, 'scaler.pkl')
print(f"💾 Scaler Saved: scaler.pkl")


config = {'model_name': best_model_name, 'needs_scaling': best_scaler_needed}
joblib.dump(config, 'model_config.pkl')
print(f"💾 Config Saved: model_config.pkl")


print("\n🧪 Testing Prediction with a Sample Student:")
sample_student = pd.DataFrame([{
    'Attendance': 35,   
    'Assignment': 5,
    'Quiz': 12, 
    'Final': 30,
    'Previous_GPA': 2.5
}], columns=feature_cols)


if best_scaler_needed:
    input_data = scaler.transform(sample_student)
else:
    input_data = sample_student

prediction = best_model.predict(input_data)[0]
result_text = "🔴 High Risk" if prediction == 1 else "🟢 Safe"

print(f"Input Data: {sample_student.iloc[0].to_dict()}")
print(f"Prediction: {result_text}")