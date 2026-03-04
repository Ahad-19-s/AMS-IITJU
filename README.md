# 🎓 Student Academic Risk Prediction System

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Django](https://img.shields.io/badge/Django-4.0%2B-green)
![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## 🚀 Overview
**Student Academic Risk Prediction System** is an intelligent web application designed to help educators identify "at-risk" students early in the semester. 

Using **Machine Learning**, the system analyzes student data (Attendance, Quiz, Assignments, etc.) and predicts whether a student is likely to fail or face academic probation. It compares four different algorithms to ensure the highest accuracy.

---

## 🔑 Key Features
* **🤖 Multi-Model Comparison:** Automatically trains and compares **Logistic Regression, Decision Tree, Random Forest, and KNN**.
* **🏆 Auto-Selection:** Selects the best model based on the **F1-Score** to balance Precision and Recall.
* **📊 Real-time Prediction:** Teachers can input student data and get instant risk analysis (Safe vs. High Risk).
* **📉 Synthetic Data Generation:** Includes a script to generate 5,000+ synthetic student records for training.
* **💾 Model Persistence:** Saves the trained model using `joblib` for efficient reuse without retraining.

---

## 🧠 Machine Learning Workflow

### 1. Dataset Features
The model is trained on the following academic parameters:
| Feature | Description | Range |
| :--- | :--- | :--- |
| **Attendance** | Percentage of classes attended | 0 - 100% |
| **Assignment** | Marks obtained in assignments | 0 - 10 |
| **Quiz** | Marks obtained in quizzes | 0 - 20 |
| **Final** | Final exam score | 0 - 60 |
| **Previous GPA** | Student's CGPA from last semester | 0.00 - 4.00 |

### 2. Risk Logic (Target Variable)
A student is labeled as **"High Risk"** if:
* Attendance < 50% **OR**
* Previous GPA < 2.00 **OR**
* Total Marks (Assignment + Quiz + Final) < 40

### 3. Algorithm Performance
The system evaluates models based on **Accuracy, Precision, Recall, and F1-Score**.

| Algorithm | Accuracy | F1-Score | Status |
| :--- | :---: | :---: | :---: |
| **Random Forest** | **99.8%** | **0.99** | ✅ **Selected** |
| Decision Tree | 98.5% | 0.98 | - |
| Logistic Regression | 92.1% | 0.91 | - |
| KNN | 89.4% | 0.88 | - |

> *Note: Random Forest usually performs best due to its ability to handle non-linear relationships in academic data.*

---

## 🛠️ Installation & Setup

Follow these steps to run the project locally:

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/student-risk-prediction.git](https://github.com/your-username/student-risk-prediction.git)
cd student-risk-prediction


# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txtpip install -r requirements.txt


student-risk-prediction/
│
├── core/                   # Django App
│   ├── views.py            # Loads model & predicts
│   ├── urls.py
│   └── templates/
│
├── ml_models/              # ML Scripts
│   ├── train_model.py      # Script to train & compare models
│   ├── academic_risk_model.pkl  # Saved Model
│   └── scaler.pkl          # Saved Scaler
│
├── manage.py
├── requirements.txt
└── README.md
