import json
import os
import joblib
from django.conf import settings 
import numpy as np
import openpyxl
from io import BytesIO
from xhtml2pdf import pisa
import google.generativeai as genai

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Q
from django.http import HttpResponse
from django.template.loader import get_template
from django.core.paginator import Paginator
from django.contrib.auth.forms import PasswordChangeForm

# আপনার মডেলগুলো
from .models import Student, AcademicRecord, Course, StudentSubjectScore

# ফর্মস ইম্পোর্ট
from .forms import StudentForm, CourseForm, AcademicRecordForm, SubjectScoreForm

# ==========================================
# 🔑 API CONFIGURATION
# ==========================================
GOOGLE_API_KEY = "AIzaSyDJd7w-gqIrXoL6aXUtnfPS5UfVBJdaKaE"

 # এই লাইনটি ফাইলের একদম উপরে import সেকশনে থাকতে হবে

# ==========================================
# 🤖 Global AI Model Load (Rule Based / ML)
# ==========================================
model = None
try:
    # আমরা এখন settings.BASE_DIR ব্যবহার করছি যা সরাসরি মেইন ফোল্ডারকে নির্দেশ করে
    model_path = os.path.join(settings.BASE_DIR, 'risk_model.pkl')

    if os.path.exists(model_path):
        model = joblib.load(model_path)
        print(f"✅ Model loaded successfully from: {model_path}")
    else:
        print(f"⚠️ Warning: Model not found at {model_path}")
        
except Exception as e:
    print(f"⚠️ Error loading model: {e}")

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


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from .models import Student, AcademicRecord
import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from .models import Student, AcademicRecord
import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
import json


from .models import Student, AcademicRecord, Course, StudentSubjectScore

@login_required(login_url='login')
def dashboard(request):
   
  
    total_students = Student.objects.count()

    
    TOTAL_CLASS_DAYS = 24
    
    
    avg_att_days = AcademicRecord.objects.aggregate(Avg('attendance'))['attendance__avg'] or 0
    
   
    avg_attendance_percent = (avg_att_days / TOTAL_CLASS_DAYS) * 100
    
    
    if avg_attendance_percent > 100:
        avg_attendance_percent = 100

    # ৩. (Overall CGPA)
    overall_gpa = AcademicRecord.objects.aggregate(Avg('gpa'))['gpa__avg'] or 0
# ==========================================
    # ৪. Risk Analysis (AI Driven)
    # ==========================================
    
    # প্রথমে মডেল লোড করা
    model_path = os.path.join(settings.BASE_DIR, 'risk_model.pkl')
    model = None
    try:
        model = joblib.load(model_path)
    except:
        print("⚠️ Dashboard: Risk Model not found, using manual fallback.")

    risk_count = 0
    TOTAL_CLASS_DAYS = 24

    # সব ছাত্রকে মডেল দিয়ে চেক করা
    all_students_check = Student.objects.all()

    if model:
        for student in all_students_check:
            records = AcademicRecord.objects.filter(student=student).order_by('semester')
            
            if not records.exists():
                continue

            # Trend Analysis Logic
            sem_risk_count = 0
            total_sems = records.count()
            last_sem_status = "Safe"
            is_at_risk = False

            for record in records:
                # ইনপুট তৈরি
                r_att = record.attendance if record.attendance else 0
                r_pct = (r_att / TOTAL_CLASS_DAYS) * 100
                if r_pct > 100: r_pct = 100

                input_data = pd.DataFrame([{
                    'Attendance': r_pct,
                    'Assignment': record.assignment or 0,
                    'Quiz': record.quiz or 0,
                    'Midterm': record.midterm or 0,
                    'Final': record.final or 0,
                    'Previous_GPA': record.gpa
                }])
                

                # প্রেডিকশন
                try:
                    pred = model.predict(input_data)[0]
                    if pred == 'High Risk' or pred == 'Risk':
                        sem_risk_count += 1
                        last_sem_status = "High Risk"
                    else:
                        last_sem_status = "Safe"
                except:
                    pass
            
            # --- Final Verdict ---
            # ১. শেষ সেমিস্টার খারাপ হলে -> Risk
            # ২. অথবা মোট সেমিস্টারের ৫০% এর বেশি খারাপ হলে -> Risk
            if last_sem_status == "High Risk":
                is_at_risk = True
            elif sem_risk_count >= (total_sems / 2):
                is_at_risk = True
            
            if is_at_risk:
                risk_count += 1
    else:
        # মডেল না থাকলে ম্যানুয়াল ফলব্যাক
        # আমরা দেখব কতজন ছাত্রের শেষ সেমিস্টারের জিপিএ ২.৫০ এর নিচে
        risk_count = 0
        for student in all_students_check:
            last_rec = AcademicRecord.objects.filter(student=student).last()
            if last_rec and last_rec.gpa < 2.50:
                risk_count += 1

    # Safe Count বের করা
    safe_count = total_students - risk_count

    # ৫.  Average CGPA Trend 
    semester_data = AcademicRecord.objects.values('semester').annotate(avg_gpa=Avg('gpa')).order_by('semester')
    sem_labels = [data['semester'] for data in semester_data]
    sem_gpa = [round(data['avg_gpa'], 2) for data in semester_data]

 # ==========================================
    # ৫. Recent Student Evaluations (With AI Trend Analysis)
    # ==========================================
    
    # ১. মডেল লোড করা
    model_path = os.path.join(settings.BASE_DIR, 'risk_model.pkl')
    model = None
    try:
        model = joblib.load(model_path)
    except:
        print("⚠️ Risk Model not found!")

    TOTAL_CLASS_DAYS = 24
    recent_records = []
    
    # যাদের রেকর্ড আছে তাদের খোঁজা
    students_with_records = Student.objects.filter(academicrecord__isnull=False).distinct()

    for student in students_with_records:
        # ছাত্রের সব রেকর্ড আনা (Trend Analysis এর জন্য)
        all_records = AcademicRecord.objects.filter(student=student).order_by('semester')
        
        # ডিসপ্লের জন্য শেষের রেকর্ডটি নেওয়া
        latest_record = all_records.last() 
        
        if latest_record:
            
            # --- A. Display Calculation (Attendance) ---
            present_days = latest_record.attendance if latest_record.attendance else 0
            calculated_percent = (present_days / TOTAL_CLASS_DAYS) * 100
            if calculated_percent > 100: calculated_percent = 100
            
            latest_record.att_percent = round(calculated_percent, 1)
            latest_record.days_present = int(present_days)

            # --- B. AI Prediction (Trend Analysis) ---
            risk_count = 0
            total_semesters = all_records.count()
            last_sem_status = "Safe"
            final_risk_status = "Safe" # ডিফল্ট

            if model:
                # লুপ চালিয়ে সব সেমিস্টার চেক করা
                for record in all_records:
                    # ইনপুট ডাটা তৈরি
                    r_att = record.attendance if record.attendance else 0
                    r_pct = (r_att / TOTAL_CLASS_DAYS) * 100
                    if r_pct > 100: r_pct = 100

                    input_data = pd.DataFrame([{
                        'Attendance': r_pct,
                        'Assignment': record.assignment or 0,
                        'Quiz': record.quiz or 0,
                        'Midterm': record.midterm or 0,
                        'Final': record.final or 0,
                        'Previous_GPA': record.gpa
                    }])

                    # প্রেডিকশন
                    try:
                        pred = model.predict(input_data)[0]
                        if pred == 'High Risk' or pred == 'Risk':
                            risk_count += 1
                            last_sem_status = "High Risk"
                        else:
                            last_sem_status = "Safe"
                    except:
                        pass
                
                # --- Final Verdict Logic ---
                # শেষ সেমিস্টার খারাপ অথবা মোট সেমিস্টারের অর্ধেক খারাপ হলে রিস্ক
                if last_sem_status == "High Risk":
                    final_risk_status = "High Risk"
                elif risk_count >= (total_semesters / 2):
                    final_risk_status = "High Risk"
            
            else:
                # মডেল না থাকলে ম্যানুয়াল ফলব্যাক
                if calculated_percent < 60 or latest_record.gpa < 2.5:
                    final_risk_status = "High Risk"

            # অবজেক্টের সাথে স্ট্যাটাস জুড়ে দেওয়া (HTML এ দেখানোর জন্য)
            latest_record.ai_status = final_risk_status
            
            recent_records.append(latest_record)

    # সর্টিং এবং স্লাইসিং
    recent_records.sort(key=lambda x: x.id, reverse=True)
    recent_records = recent_records[:5]
    
    
    semester_performance = {}
    semesters_list = ['1-1', '1-2', '2-1', '2-2', '3-1', '3-2', '4-1', '4-2']
    
    for sem in semesters_list:
        
        courses = Course.objects.filter(semester=sem)
        
        subject_data = []
        for course in courses:
          
            avg_marks = StudentSubjectScore.objects.filter(course=course).aggregate(Avg('marks'))['marks__avg']
            
            if avg_marks is not None:
                subject_data.append({
                   
                    'name': course.title,  
                    
                    'score': round(avg_marks, 1),
                    'total': 100 
                })
        
        semester_performance[sem] = subject_data

    # context এ ডাটা পাঠানো (আগের মতোই)
    context = {
        'total_students': total_students,
        'avg_attendance': round(avg_attendance_percent, 1),
        'overall_gpa': round(overall_gpa, 2),
        'risk_count': risk_count,
        'recent_records': recent_records,
        'sem_labels': json.dumps(sem_labels),
        'sem_gpa': json.dumps(sem_gpa),
        'risk_data': json.dumps([safe_count, risk_count]),
        
        # এই লাইনটি খুব গুরুত্বপূর্ণ
        'semester_performance': json.dumps(semester_performance),
    }

    return render(request, 'dashboard.html', context)
    # ==========================================
    # Context তৈরি এবং রিটার্ন
    # ==========================================
    context = {
        'total_students': total_students,
        'avg_attendance': round(avg_attendance_percent, 1),
        'overall_gpa': round(overall_gpa, 2),
        'risk_count': risk_count,
        'recent_records': recent_records,
        
        # চার্ট ডাটা
        'sem_labels': json.dumps(sem_labels),
        'sem_gpa': json.dumps(sem_gpa),
        'risk_data': json.dumps([safe_count, risk_count]),
        
        # নতুন ডাটা (Subject Grades এর জন্য)
        'semester_performance': json.dumps(semester_performance),
    }

    return render(request, 'dashboard.html', context)

# ==========================================
# 👥 ৩. স্টুডেন্ট লিস্ট
# ==========================================

@login_required(login_url='login')
def student_list(request):
    students = Student.objects.all().order_by('student_id')

    # ব্যাচ ফিল্টার
    batches = Student.objects.values_list('batch', flat=True).distinct().order_by('batch')
    selected_batch = request.GET.get('batch')
    
    if selected_batch:
        students = students.filter(batch=selected_batch)

    # সার্চ ফিল্টার
    query = request.GET.get('q')
    if query:
        students = students.filter(
            Q(name__icontains=query) | Q(student_id__icontains=query)
        )

    context = {
        'students': students,
        'batches': batches,
        'selected_batch': selected_batch
    }
    return render(request, 'students.html', context)


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Student, AcademicRecord
import joblib
import pandas as pd
import os
from django.conf import settings

@login_required(login_url='login')
def student_profile(request, student_id):
    
    # ১. স্টুডেন্ট খোঁজা
    try:
        student = Student.objects.get(id=student_id)
    except (Student.DoesNotExist, ValueError):
        student = get_object_or_404(Student, student_id=student_id)
    
    records = AcademicRecord.objects.filter(student=student).order_by('semester')

    # ২. AI মডেল লোড করা
    model_path = os.path.join(settings.BASE_DIR, 'risk_model.pkl')
    model = None
    try:
        model = joblib.load(model_path)
    except:
        print("⚠️ risk_model.pkl not found!")

    # ==========================================
    # ৩. এভারেজ ক্যালকুলেশন এবং ফাইনাল সিদ্ধান্ত
    # ==========================================
    
    final_prediction = "Unknown"
    total_semesters = records.count()
    TOTAL_CLASS_DAYS = 24

    # যোগফল রাখার জন্য ভেরিয়েবল
    sum_attendance_pct = 0
    sum_assignment = 0
    sum_quiz = 0
    sum_midterm = 0
    sum_final = 0
    sum_gpa = 0

    if model and total_semesters > 0:
        
        # সব সেমিস্টারের ডাটা যোগ করা হচ্ছে
        for record in records:
            # Attendance কে পার্সেন্টেজে কনভার্ট করা
            att_days = record.attendance if record.attendance else 0
            att_percent = (att_days / TOTAL_CLASS_DAYS) * 100
            if att_percent > 100: att_percent = 100
            
            sum_attendance_pct += att_percent
            sum_assignment += (record.assignment or 0)
            sum_quiz += (record.quiz or 0)
            sum_midterm += (record.midterm or 0)
            sum_final += (record.final or 0)
            sum_gpa += (record.gpa or 0.0)

        # গড় (Average) বের করা
        avg_attendance = sum_attendance_pct / total_semesters
        avg_assignment = sum_assignment / total_semesters
        avg_quiz = sum_quiz / total_semesters
        avg_midterm = sum_midterm / total_semesters
        avg_final = sum_final / total_semesters
        avg_gpa = sum_gpa / total_semesters

        # AI এর জন্য ইনপুট তৈরি (গড় ডাটা দিয়ে)
        input_data = pd.DataFrame([{
            'Attendance': avg_attendance,
            'Assignment': avg_assignment,
            'Quiz': avg_quiz,
            'Midterm': avg_midterm,
            'Final': avg_final,
            'Previous_GPA': avg_gpa
        }])

        # --- ফাইনাল প্রেডিকশন (একবারই কল হবে) ---
        try:
            final_prediction = model.predict(input_data)[0] # Output: 'Safe' or 'High Risk'
        except Exception as e:
            print(f"Prediction Error: {e}")
            final_prediction = "Error"

    # Context এ পাঠানো
    context = {
        'student': student,
        'records': records,
        'prediction': final_prediction,  # এখন এটি এভারেজ পারফরম্যান্সের ওপর ভিত্তি করে
        'total_semesters': total_semesters
    }
    
    return render(request, 'student_profile.html', context)

from django.db.models import Avg, Sum, Count, F
# নিশ্চিত করুন এই ইমপোর্টগুলো উপরে আছে
# from .models import Student, AcademicRecord, Course, StudentSubjectScore

from django.shortcuts import render
from .models import Student, AcademicRecord, StudentSubjectScore
from django.db.models import Avg
import joblib
import pandas as pd
import os
from django.conf import settings
import google.generativeai as genai

# আপনার API KEY ইম্পোর্ট করুন অথবা settings এ রাখুন
# from .config import GOOGLE_API_KEY 

@login_required(login_url='login')
def reports(request):
    # ১. ফিল্টার প্যারামিটার রিসিভ করা
    risk_filter = request.GET.get('risk_level')
    max_attendance = request.GET.get('max_attendance')
    max_gpa = request.GET.get('max_gpa')

    # ==========================================
    # ২. মডেল লোড করা (একবার)
    # ==========================================
    model_path = os.path.join(settings.BASE_DIR, 'risk_model.pkl')
    model = None
    try:
        model = joblib.load(model_path)
    except:
        print("⚠️ risk_model.pkl not found!")

    TOTAL_CLASS_DAYS = 24
    
    # ==========================================
    # ৩. স্টুডেন্ট ডাটা প্রসেসিং & AI Prediction
    # ==========================================
    report_data = []  
    
    # পরিসংখ্যান ভেরিয়েবল
    total_gpa_sum = 0
    total_att_sum = 0
    
    all_students = Student.objects.all().order_by('student_id')

    for student in all_students:
        records = AcademicRecord.objects.filter(student=student).order_by('semester')
        
        if records.exists():
            # --- A. ডিসপ্লের জন্য গড় (Average) বের করা ---
            aggregates = records.aggregate(Avg('gpa'), Avg('attendance'))
            avg_gpa = aggregates['gpa__avg'] or 0
            avg_att_days = aggregates['attendance__avg'] or 0
            
            # ডিসপ্লের জন্য পার্সেন্টেজ
            att_percent_display = (avg_att_days / TOTAL_CLASS_DAYS) * 100
            if att_percent_display > 100: att_percent_display = 100

            # --- B. AI Prediction (Trend Analysis) ---
            # ম্যানুয়াল লজিক বাদ দিয়ে এখন মডেল ডিসিশন নেবে
            
            is_high_risk = False # ডিফল্ট সেইফ
            risk_count = 0
            total_semesters = records.count()
            last_sem_status = "Safe"

            if model:
                # প্রতিটি রেকর্ড চেক করা হচ্ছে
                for record in records:
                    # ইনপুট তৈরি
                    r_att = record.attendance if record.attendance else 0
                    r_pct = (r_att / TOTAL_CLASS_DAYS) * 100
                    if r_pct > 100: r_pct = 100

                    input_data = pd.DataFrame([{
                        'Attendance': r_pct,
                        'Assignment': record.assignment or 0,
                        'Quiz': record.quiz or 0,
                        'Midterm': record.midterm or 0,
                        'Final': record.final or 0,
                        'Previous_GPA': record.gpa
                    }])
                    
                    try:
                        pred = model.predict(input_data)[0]
                        if pred == 'High Risk' or pred == 'Risk':
                            risk_count += 1
                            last_sem_status = "High Risk"
                        else:
                            last_sem_status = "Safe"
                    except:
                        pass
                
                # --- Final Verdict Logic ---
                # ১. শেষ সেমিস্টার খারাপ হলে -> Risk
                # ২. অথবা মোট সেমিস্টারের ৫০% এর বেশি খারাপ হলে -> Risk
                if last_sem_status == "High Risk":
                    is_high_risk = True
                elif risk_count >= (total_semesters / 2):
                    is_high_risk = True
                else:
                    is_high_risk = False
            else:
                # মডেল না থাকলে কেবল ম্যানুয়াল ফলব্যাক (অপশনাল)
                if avg_gpa < 2.5: is_high_risk = True

            # --- C. Filtering Logic ---
            # ইউজার ইনপুট ফিল্টার
            if max_attendance and att_percent_display > float(max_attendance):
                continue 
            if max_gpa and avg_gpa > float(max_gpa):
                continue

            # রিস্ক ফিল্টার (এখন is_high_risk আসছে মডেল থেকে)
            if risk_filter == 'High Risk' and not is_high_risk:
                continue
            elif risk_filter == 'Low Risk' and is_high_risk:
                continue 

            # --- D. লিস্টে যোগ করা ---
            report_data.append({
                'name': student.name,
                'student_id': student.student_id,
                'avg_gpa': round(avg_gpa, 2),
                'att_percent': round(att_percent_display, 1), 
                'att_days': round(avg_att_days, 1),
                'is_risk': is_high_risk # মডেলের সিদ্ধান্ত
            })
            
            total_gpa_sum += avg_gpa
            total_att_sum += att_percent_display

    # ==========================================
    # ৪. AI Actions / Alerts
    # ==========================================
    ai_actions = []
    
    # মডেলের রেজাল্ট অনুযায়ী কাউন্ট করা হচ্ছে
    high_risk_students = [s for s in report_data if s['is_risk'] == True]
    high_risk_count = len(high_risk_students)
    
    if high_risk_count > 0:
        ai_actions.append({
            'title': 'High Risk Alert (AI Detected)',
            'desc': f'{high_risk_count} students identified as High Risk by the ML Model.',
            'color': 'danger',
            'btn_text': 'View Students',
            'icon': 'fas fa-brain'
        })
    
    # অ্যাটেনডেন্স ওয়ার্নিং (ম্যানুয়াল চেক রাখা ভালো)
    low_att_count = len([s for s in report_data if s['att_percent'] < 50])
    if low_att_count > 0:
        ai_actions.append({
            'title': 'Attendance Warning',
            'desc': f'{low_att_count} students have critically low attendance (<50%).',
            'color': 'warning',
            'btn_text': 'Send Notice',
            'icon': 'fas fa-clock'
        })

    # ==========================================
    # ৫. গ্রাফ ডাটা (Subjet Wise)
    # ==========================================
    course_performance = StudentSubjectScore.objects.values('course__title').annotate(
        avg_marks=Avg('marks') 
    ).order_by('course__title')

    course_labels = [item['course__title'] for item in course_performance]
    course_data = [round(item['avg_marks'], 1) for item in course_performance]

    if not course_labels:
        course_labels = ['No Data']
        course_data = [0]

    # ==========================================
    # ৬. Gemini Text Summary
    # ==========================================
    ai_response_text = ""
    total_students = len(report_data)
    
    if total_students > 0:
        # ১. গড় বের করা (Average Calculation)
        class_avg_gpa = round(total_gpa_sum / total_students, 2)
        class_avg_att = round(total_att_sum / total_students, 1) # এই লাইনটি মিসিং ছিল
        
        try:
            # ২. জেমিনাই কনফিগারেশন
            genai.configure(api_key="AIzaSyDJd7w-gqIrXoL6aXUtnfPS5UfVBJdaKaE") # অথবা settings.GOOGLE_API_KEY
            model_gemini = genai.GenerativeModel('gemini-2.5-flash')
            
            # ৩. প্রম্পট তৈরি
            prompt = f"""
            Act as an Academic Advisor. Analyze this class report:
            - Total Students: {total_students}
            - Students at High Risk (ML Prediction): {high_risk_count}
            - Average Class CGPA: {class_avg_gpa}
            - Average Attendance: {class_avg_att}%
            
            Write exactly 3 short, actionable bullet points (using HTML <li> tags) suggesting how to improve the class performance.
            """
            
            # ৪. রেসপন্স জেনারেট
            response = model_gemini.generate_content(prompt)
            ai_response_text = response.text
            
        except Exception as e:
            print(f"Gemini Error: {e}")
            ai_response_text = "<li>AI Analysis unavailable (Check API Key or Connection).</li>"
            
    else:
        # ৫. ডাটা না থাকলে
        ai_response_text = "<li>No student data found matching your filters.</li>"

    # ==========================================
    # ৭. রেন্ডার
    # ==========================================
    context = {
        'report_data': report_data,
        'ai_actions': ai_actions,
        'course_labels': course_labels,
        'course_data': course_data,
        'ai_response_text': ai_response_text,
        'selected_risk': risk_filter,
        'selected_att': max_attendance,
        'selected_gpa': max_gpa
    }

    return render(request, 'reports.html', context)

# ==========================================
# 📥 ৬. এক্সপোর্ট ফিচার
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


# ==========================================
# ➕ ৭. ডাটা এন্ট্রি (Menu & Separate Forms)
# ==========================================

@login_required(login_url='login')
def add_data(request):
    """
    এই ফাংশনটি 'add_data.html' পেজটি রেন্ডার করবে
    এবং সেখানে ৪টি ফর্ম একসাথে পাঠাবে যাতে ট্যাব সিস্টেমে কাজ করে।
    """
    context = {
        'student_form': StudentForm(),
        'course_form': CourseForm(),
        'record_form': AcademicRecordForm(),
        'score_form': SubjectScoreForm(),
    }
    return render(request, 'add_data.html', context)


@login_required(login_url='login')
def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Student added successfully!')
            return redirect('add_data') # সফল হলে মেইন পেজে ফিরে যাবে
        else:
            print("❌ Student Form Error:", form.errors)
            messages.error(request, f'Error: {form.errors}')
            # এরর হলে আবার মেইন পেজে পাঠিয়ে দিচ্ছি
            return redirect('add_data') 
            
    # কেউ যদি সরাসরি লিংকে হিট করে, তাকে মেইন পেজে পাঠিয়ে দেওয়া হবে
    return redirect('add_data')


@login_required(login_url='login')
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Course added successfully!')
            return redirect('add_data')
        else:
            print("❌ Course Form Error:", form.errors)
            messages.error(request, f'Error: {form.errors}')
            return redirect('add_data')

    return redirect('add_data')


@login_required(login_url='login')
def add_academic_record(request):
    if request.method == 'POST':
        form = AcademicRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Academic Record added successfully!')
            return redirect('add_data')
        else:
            print("❌ Record Form Error:", form.errors)
            messages.error(request, f'Error: {form.errors}')
            return redirect('add_data')

    return redirect('add_data')


@login_required(login_url='login')
def add_subject_score(request):
    if request.method == 'POST':
        form = SubjectScoreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Subject Score added successfully!')
            return redirect('add_data')
        else:
            print("❌ Score Form Error:", form.errors)
            messages.error(request, f'Error: {form.errors}')
            return redirect('add_data')

    return redirect('add_data')

# ==========================================
# ⚙️ ৮. সেটিংস এবং পাসওয়ার্ড চেঞ্জ
# ==========================================

# এই ফাংশনটি মিসিং ছিল
@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # পাসওয়ার্ড বদলানোর পর লগইন ঠিক রাখতে
            messages.success(request, 'Your password was successfully updated!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})


@login_required(login_url='login')
def admin_settings(request):
    user = request.user
    
    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('admin_settings')
            else:
                messages.error(request, 'Please correct the password errors below.')
    
    # শুধু GET রিকোয়েস্টের জন্য
    password_form = PasswordChangeForm(user)

    context = {
        'password_form': password_form
    }
    return render(request, 'admin_settings.html', context)


# ==========================================
# 🧠 ৯. AI Dashboard (Optional)
# ==========================================
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Student, AcademicRecord
import joblib
import pandas as pd
import os
from django.conf import settings

@login_required(login_url='login')
def ai_dashboard(request):
    
    # ১. AI মডেল লোড করা (নিরাপদভাবে)
    model_path = os.path.join(settings.BASE_DIR, 'risk_model.pkl')
    try:
        model = joblib.load(model_path)
        model_loaded = True
    except:
        model = None
        model_loaded = False
        print("⚠️ Warning: risk_model.pkl not found! Please train the model first.")

    students = Student.objects.all()
    student_risks = []
    
    total_students = students.count()
    high_risk_count = 0
    
    TOTAL_CLASS_DAYS = 24  # আপনার মোট ক্লাস সংখ্যা

    for student in students:
        # লেটেস্ট রেকর্ড নেওয়া
        last_record = AcademicRecord.objects.filter(student=student).order_by('-semester').first()
        
        if last_record:
            # ২. অ্যাটেনডেন্সকে দিনে (Days) থেকে শতাংশে (%) রূপান্তর করা
            # সূত্র: (উপস্থিতি / ২৪) * ১০০
            attendance_days = last_record.attendance
            att_percentage = (attendance_days / TOTAL_CLASS_DAYS) * 100
            
            if att_percentage > 100: att_percentage = 100

            # ৩. AI এর জন্য ডাটা সাজানো
            # (লক্ষ্য রাখুন: কলামের নাম যেন ট্রেনিং ডাটার সাথে হুবহু মিলে)
            input_data = pd.DataFrame([{
                'Attendance': att_percentage,
                'Assignment': getattr(last_record, 'assignment', 0), # ফিল্ড না থাকলে 0
                'Quiz': getattr(last_record, 'quiz', 0),
                'Midterm': getattr(last_record, 'midterm', 0),
                'Final': getattr(last_record, 'final', 0),
                'Previous_GPA': last_record.gpa 
            }])

            # ৪. প্রেডিকশন করা
            risk_status = "Safe" # ডিফল্ট
            if model_loaded:
                try:
                    prediction = model.predict(input_data)[0]
                    risk_status = prediction # 'High Risk' or 'Safe'
                except Exception as e:
                    print(f"Prediction Error for {student.name}: {e}")

            # ৫. রিস্ক কাউন্ট আপডেট করা
            if risk_status == "High Risk" or risk_status == "Risk":
                high_risk_count += 1
                color_class = "danger" # লাল
            else:
                color_class = "success" # সবুজ
            
            # ৬. লিস্টে ডাটা যোগ করা
            student_risks.append({
                'id': student.id,
                'student_id': student.student_id,
                'name': student.name,
                'gpa': last_record.gpa,
                'attendance': f"{attendance_days}/{TOTAL_CLASS_DAYS} ({round(att_percentage)}%)", # সুন্দর করে দেখানো
                'risk': risk_status,
                'color': color_class
            })

        else:
            # যদি কোনো রেকর্ড না থাকে
            student_risks.append({
                'id': student.id,
                'student_id': student.student_id,
                'name': student.name,
                'gpa': 'N/A',
                'attendance': 'N/A',
                'risk': 'Unknown',
                'color': 'secondary'
            })

    context = {
        'student_risks': student_risks,
        'total_students': total_students,
        'high_risk_count': high_risk_count,
        'safe_count': total_students - high_risk_count
    }
    
    return render(request, 'ai_dashboard.html', context)