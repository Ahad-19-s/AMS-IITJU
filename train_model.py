import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# 1. Load the data
df = pd.read_csv('student_data.csv')

# 2. Select features for AI to learn from
X = df[['Attendance', 'Assignment', 'Quiz', 'Midterm', 'Final', 'Previous_GPA']]
y = df['Risk_Level']

# 3. Split the data into training (80%) and testing (20%) sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Create and train the AI model
print("AI model is reading the data and learning... please wait...")
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# 5. Test the model
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print("🤖 Model Training Complete!")
print(f"🎯 Model Accuracy: {round(accuracy * 100, 2)}%")

# 6. Save the trained model
joblib.dump(model, 'risk_model.pkl')
print("💾 Model saved as 'risk_model.pkl'!")