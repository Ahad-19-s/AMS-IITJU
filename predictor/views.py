import json
import os
import joblib
import numpy as np
import openpyxl
from io import BytesIO
from xhtml2pdf import pisa
import google.generativeai as genai  # AI লাইব্রেরি

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Q
from django.http import HttpResponse
from django.template.loader import get_template
from django.core.paginator import Paginator

# সব মডেল একসাথে ইম্পোর্ট করা হলো
from .models import Student, AcademicRecord, Course, StudentSubjectScore

# ==========================================
# 🔑 API CONFIGURATION
# ==========================================
GOOGLE_API_KEY = "AIzaSyBerpcsDO8BrVZrW_W4gHRBivUa9p57REw"

# ==========================================
# 🤖 Global AI Model Load (Rule Based / ML)
# ==========================================
try:
    model = joblib.load('risk_model.pkl')
    print("✅ Local ML Model loaded successfully!")
except Exception as e:
    model = None
    print(f"⚠️ Warning: 'risk_model.pkl' not found. Error: {e}")


# ==========================================
# 🔐 ১. অথেন্টিকেশন (Login & Logout)
# ==========================================

def user_login(request):
    if request.method == 'POST':
        u_name = request.POST.get('username')
        p_word = request.POST.get('password')
        
        user = authenticate(request, username=u_name, password=p_word)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid Username or Password!')
            
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')


# ==========================================
# 🏠 ২. মেইন ড্যাশবোর্ড (Home) - Updated
# ==========================================

# from django.core.paginator import Paginator  # <--- এই লাইনটি সবার উপরে ইম্পোর্ট সেকশনে যোগ করুন

# ... বাকি ইম্পোর্টগুলো একই থাকবে ...

@login_required(login_url='login')
def dashboard(request):
    # ১. সাধারণ পরিসংখ্যান
    total_students = Student.objects.count()
    averages = AcademicRecord.objects.aggregate(Avg('gpa'), Avg('attendance'))
    
    avg_gpa = averages['gpa__avg'] if averages['gpa__avg'] else 0.0
    avg_attendance = averages['attendance__avg'] if averages['attendance__avg'] else 0.0

    # ২. সাবজেক্ট ওয়াইজ পারফরমেন্স
    courses = Course.objects.all()
    subject_performance = {}
    semesters = ['1-1', '1-2', '2-1', '2-2', '3-1', '3-2', '4-1', '4-2']
    
    for sem in semesters:
        sem_courses = courses.filter(semester=sem)
        course_data = []
        for course in sem_courses:
            avg_mark = StudentSubjectScore.objects.filter(course=course).aggregate(Avg('marks'))['marks__avg']
            if avg_mark:
                course_data.append({
                    'subject': course.name,
                    'score': round(avg_mark, 1)
                })
        subject_performance[sem] = course_data

    subject_json = json.dumps(subject_performance)

    # ৩. রিস্ক অ্যানালাইসিস এবং প্যাজিনেশন (Pagination)
    students = Student.objects.all().order_by('student_id') # আইডি অনুযায়ী সর্ট করা
    evaluated_students = []
    risk_students_count = 0

    for student in students:
        # সর্বশেষ সেমিস্টারের রেকর্ড চেক করা
        latest_record = AcademicRecord.objects.filter(student=student).order_by('-semester').first()

        # কন্ডিশন: শুধুমাত্র যাদের রেকর্ড আছে (যাদের প্রেডিক্ট/ইভ্যালুয়েট করা হয়েছে) তাদের নেওয়া হবে
        if latest_record:
            student.gpa = latest_record.gpa
            student.attendance = latest_record.attendance
            
            # রিস্ক স্ট্যাটাস সেট করা (টেমপ্লেটে ব্যবহারের জন্য)
            if student.gpa < 2.50 or student.attendance < 60:
                student.risk_status = "At Risk"
                risk_students_count += 1
            else:
                student.risk_status = "Safe"
            
            # লিস্টে যোগ করা
            evaluated_students.append(student)

    # --- Pagination Logic (১০ জন প্রতি পেজে) ---
    paginator = Paginator(evaluated_students, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'total_students': total_students,
        'avg_gpa': round(avg_gpa, 2),
        'avg_attendance': round(avg_attendance, 1),
        'risk_students': risk_students_count,
        'recent_students': page_obj,  # এখন আমরা পুরো পেজ অবজেক্ট পাঠাচ্ছি
        'subject_performance_json': subject_json,
    }
    return render(request, 'dashboard.html', context)


# ==========================================
# 👥 ৩. স্টুডেন্ট লিস্ট
# ==========================================

@login_required(login_url='login')
def student_list(request):
    query = request.GET.get('q')
    
    if query:
        students = Student.objects.filter(
            Q(name__icontains=query) | Q(student_id__icontains=query)
        ).order_by('student_id')
    else:
        students = Student.objects.all().order_by('student_id')

    context = {'students': students}
    return render(request, 'students.html', context)


# ==========================================
# 📊 ৪. স্টুডেন্ট প্রোফাইল (ML Prediction সহ)
# ==========================================

@login_required(login_url='login')
def student_profile(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    records = AcademicRecord.objects.filter(student=student).order_by('semester')
    
    prediction = None
    prediction_prob = 0 

    if request.method == 'POST' and records.exists() and model:
        avg_stats = records.aggregate(
            Avg('attendance'), Avg('assignment'), Avg('quiz'), 
            Avg('midterm'), Avg('final'), Avg('gpa')
        )

        input_data = [[
            avg_stats['attendance__avg'],
            avg_stats['assignment__avg'],
            avg_stats['quiz__avg'],
            avg_stats['midterm__avg'],
            avg_stats['final__avg'],
            avg_stats['gpa__avg']
        ]]
        
        try:
            prediction = model.predict(input_data)[0]
            try:
                probs = model.predict_proba(input_data)
                prediction_prob = round(probs[0][0] * 100, 2)
            except:
                prediction_prob = 0
        except Exception as e:
            print(f"Prediction Error: {e}")
            prediction = "Error"

    context = {
        'student': student,
        'records': records,
        'prediction': prediction,
        'prediction_prob': prediction_prob
    }
    return render(request, 'student_profile.html', context)


# ==========================================
# 🧠 ৫. AI Reports & Analytics (GEMINI INTELLIGENCE)
# ==========================================

@login_required(login_url='login')
def reports(request):
    # ১. ডাটা ফিল্টারিং
    records = AcademicRecord.objects.all().order_by('-semester')
    
    risk_filter = request.GET.get('risk_level')
    max_attendance = request.GET.get('max_attendance')
    max_gpa = request.GET.get('max_gpa')

    # ফিল্টার লজিক
    if max_attendance:
        records = records.filter(attendance__lte=int(max_attendance))
    if max_gpa:
        records = records.filter(gpa__lte=float(max_gpa))
    
    if risk_filter == 'High Risk':
        records = records.filter(Q(gpa__lt=2.5) | Q(attendance__lt=60))
    elif risk_filter == 'Low Risk':
        records = records.filter(gpa__gte=3.5)

    # ২. Rule-Based Actions
    ai_actions = []
    
    high_risk_count = records.filter(Q(gpa__lt=2.5) | Q(attendance__lt=60)).count()
    if high_risk_count > 0:
        ai_actions.append({
            'title': 'High Risk Alert',
            'desc': f'{high_risk_count} students found in critical academic risk.',
            'color': 'danger',
            'btn_text': 'View Students',
            'icon': 'fas fa-exclamation-triangle'
        })
    
    low_att_count = records.filter(attendance__lt=50).count()
    if low_att_count > 0:
        ai_actions.append({
            'title': 'Attendance Warning',
            'desc': f'{low_att_count} students have less than 50% attendance.',
            'color': 'warning',
            'btn_text': 'Send Notice',
            'icon': 'fas fa-clock'
        })

    # ৩. Gemini AI Data Preparation
    student_data_summary = ""
    count = 0
    total_students = records.count()

    for record in records[:10]: 
        student_data_summary += f"- Name: {record.student.name}, GPA: {record.gpa}, Attendance: {record.attendance}%\n"
        count += 1
    
    # ৪. Gemini API Call
    ai_response_text = ""
    
    if count > 0:
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            model_gemini = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Analyze the following academic data of {total_students} students. 
            Here is a sample of the data:
            {student_data_summary}

            As an AI Academic Advisor, provide 3 short, actionable, and specific recommendations for the faculty to improve their performance.
            Format the output strictly as HTML list items (<li>...</li>) without <ul> tags. 
            Keep it professional and encouraging.
            """
            
            response = model_gemini.generate_content(prompt)
            ai_response_text = response.text
            
        except Exception as e:
            ai_response_text = f"<li>AI Analysis Unavailable: {str(e)}</li>"
    else:
        ai_response_text = "<li>No data available to analyze. Please adjust your filters.</li>"

    context = {
        'records': records,
        'ai_response_text': ai_response_text,
        'ai_actions': ai_actions, 
        'selected_risk': risk_filter,
        'selected_attendance': max_attendance,
        'selected_gpa': max_gpa
    }
    
    return render(request, 'reports.html', context)


# ==========================================
# 📥 ৬. এক্সপোর্ট ফিচার (Excel & PDF)
# ==========================================

def export_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Academic_Report.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Student Report"
    headers = ['Student ID', 'Name', 'Semester', 'GPA', 'Attendance (%)', 'Risk Status']
    ws.append(headers)

    students = Student.objects.all()
    
    for student in students:
        latest_record = AcademicRecord.objects.filter(student=student).order_by('-semester').first()
        
        semester = latest_record.semester if latest_record else "N/A"
        gpa = latest_record.gpa if latest_record else 0.0
        attendance = latest_record.attendance if latest_record else 0.0
        
        risk = "Low Risk"
        if gpa < 2.5 or attendance < 60:
            risk = "High Risk"
            
        ws.append([student.student_id, student.name, semester, gpa, attendance, risk])

    wb.save(response)
    return response

def export_pdf(request):
    students = Student.objects.all()
    student_data = []

    for student in students:
        latest_record = AcademicRecord.objects.filter(student=student).order_by('-semester').first()
        risk = "Low"
        if latest_record:
            if latest_record.gpa < 2.5 or latest_record.attendance < 60:
                risk = "High"
        
        student_data.append({
            'name': student.name,
            'id': student.student_id,
            'gpa': latest_record.gpa if latest_record else 0.0,
            'attendance': latest_record.attendance if latest_record else 0.0,
            'risk': risk
        })

    context = {'students': student_data}
    template_path = 'pdf_template.html'
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Academic_Report.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    
    return response

# এই view টি অপশনাল, যদি reports পেজ ব্যবহার করেন তবে এটি না থাকলেও চলবে।
# তবুও রেখে দেওয়া হলো যদি আলাদা AI Dashboard লাগে।
@login_required(login_url='login')
def ai_dashboard(request):
    students = Student.objects.all()
    student_risks = []

    if not model:
        messages.warning(request, "AI Model is not loaded.")
        return render(request, 'ai_dashboard.html', {'student_risks': []})

    for student in students:
        records = AcademicRecord.objects.filter(student=student)
        if records.exists():
            avg_stats = records.aggregate(
                Avg('attendance'), Avg('assignment'), Avg('quiz'), 
                Avg('midterm'), Avg('final'), Avg('gpa')
            )
            input_data = [[
                avg_stats['attendance__avg'],
                avg_stats['assignment__avg'],
                avg_stats['quiz__avg'],
                avg_stats['midterm__avg'],
                avg_stats['final__avg'],
                avg_stats['gpa__avg']
            ]]
            try:
                risk_status = model.predict(input_data)[0]
                student_risks.append({
                    'id': student.student_id,
                    'name': student.name,
                    'risk': risk_status,
                    'gpa': round(avg_stats['gpa__avg'], 2),
                    'attendance': round(avg_stats['attendance__avg'], 2)
                })
            except:
                pass

    return render(request, 'ai_dashboard.html', {'student_risks': student_risks})