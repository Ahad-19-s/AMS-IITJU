from django.shortcuts import render
import joblib

# আমাদের AI ব্রেনকে লোড করা হচ্ছে
model = joblib.load('risk_model.pkl')

def home(request):
    prediction = None
    if request.method == 'POST':
        # ১. ফর্ম থেকে শিক্ষকের দেওয়া মার্কসগুলো নিচ্ছি
        attendance = float(request.POST.get('attendance'))
        assignment = float(request.POST.get('assignment'))
        quiz = float(request.POST.get('quiz'))
        midterm = float(request.POST.get('midterm'))
        final = float(request.POST.get('final'))
        previous_gpa = float(request.POST.get('previous_gpa'))

        # ২. AI ব্রেনকে ডাটাগুলো দিচ্ছি হিসাব করার জন্য
        result = model.predict([[attendance, assignment, quiz, midterm, final, previous_gpa]])
        
        # ৩. AI-এর দেওয়া রেজাল্টটা (High/Medium/Low) আলাদা করছি
        prediction = result[0]

    # রেজাল্টটা ওয়েবসাইটের পেজে পাঠিয়ে দিচ্ছি
    return render(request, 'index.html', {'prediction': prediction})

def dashboard(request):
    return render(request, 'dashboard.html')