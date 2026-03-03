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
GOOGLE_API_KEY = "AIzaSyBdtmf4wjAE-As2nGXlRSymy2Z3xQ8ilmE"

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

# আপনার মডেলগুলো ইম্পোর্ট করুন (StudentSubjectScore ও Course যোগ করা হয়েছে)
from .models import Student, AcademicRecord, Course, StudentSubjectScore

@login_required(login_url='login')
def dashboard(request):
    # ==========================================
    # ১. আগের কোড (Total, Attendance, GPA, Risk, Trend)
    # ==========================================
    
    # ১. মোট ছাত্র সংখ্যা
    total_students = Student.objects.count()

    # ২. অ্যাটেনডেন্স ক্যালকুলেশন (২৪ দিনের ভিত্তিতে)
    TOTAL_CLASS_DAYS = 24
    
    # ডাটাবেস থেকে গড় দিন (Days) বের করা
    avg_att_days = AcademicRecord.objects.aggregate(Avg('attendance'))['attendance__avg'] or 0
    
    # দিনকে পার্সেন্টেজে কনভার্ট করা: (প্রাপ্ত দিন / ২৪) * ১০০
    avg_attendance_percent = (avg_att_days / TOTAL_CLASS_DAYS) * 100
    
    # ১০০% এর বেশি যেন না দেখায়
    if avg_attendance_percent > 100:
        avg_attendance_percent = 100

    # ৩. ওভারঅল জিপিএ (Overall CGPA)
    overall_gpa = AcademicRecord.objects.aggregate(Avg('gpa'))['gpa__avg'] or 0

    # ৪. রিস্ক স্টুডেন্ট বের করা (যাদের জিপিএ ২.৫০ এর নিচে)
    risk_count = AcademicRecord.objects.filter(gpa__lt=2.50).count()
    safe_count = total_students - risk_count

    # ৫. চার্ট ডাটা: Average CGPA Trend (সেমিস্টার অনুযায়ী)
    semester_data = AcademicRecord.objects.values('semester').annotate(avg_gpa=Avg('gpa')).order_by('semester')
    sem_labels = [data['semester'] for data in semester_data]
    sem_gpa = [round(data['avg_gpa'], 2) for data in semester_data]

 # ==========================================
    # ৫. Recent Student Evaluations (Unique Students)
    # ==========================================
    
    recent_records = []
    students_with_records = Student.objects.filter(academicrecord__isnull=False).distinct()

    for student in students_with_records:
        latest_record = AcademicRecord.objects.filter(student=student).order_by('-id').first()
        
        if latest_record:
            # ডাটাবেজে যদি 'দিন' থাকে (যেমন: 14 বা 17)
            present_days = latest_record.attendance 
            total_days = 24
            
            # পার্সেন্টেজ ক্যালকুলেশন: (উপস্থিত দিন / মোট দিন) * ১০০
            calculated_percent = (present_days / total_days) * 100
            
            # --- ভেরিয়েবল সেট করা ---
            
            # ১. যেখানে % দেখাবে (Progress Bar এবং বড় টেক্সট)
            # এখন 14 এর বদলে 58.3 দেখাবে
            latest_record.att_percent = round(calculated_percent, 1)
            latest_record.attendance = round(calculated_percent, 1)

            # ২. যেখানে দিন দেখাবে (ছোট টেক্সট: 14/24 Days)
            latest_record.days_present = int(present_days)
            
            recent_records.append(latest_record)

    recent_records.sort(key=lambda x: x.id, reverse=True)
    recent_records = recent_records[:5]
    
    # ==========================================
    # ৭. নতুন লজিক: Avg. Subject Grades
    # ==========================================
    semester_performance = {}
    semesters_list = ['1-1', '1-2', '2-1', '2-2', '3-1', '3-2', '4-1', '4-2']
    
    for sem in semesters_list:
        # Course মডেল থেকে এই সেমিস্টারের সাবজেক্টগুলো খোঁজা
        courses = Course.objects.filter(semester=sem)
        
        subject_data = []
        for course in courses:
            # StudentSubjectScore থেকে 'marks' এর গড় বের করা
            # (আগে ভুল করে 'score' লেখা ছিল, এখন ঠিক করা হয়েছে)
            avg_marks = StudentSubjectScore.objects.filter(course=course).aggregate(Avg('marks'))['marks__avg']
            
            if avg_marks is not None:
                subject_data.append({
                    # ==========================================
                    # পরিবর্তন: এখানে course.title ব্যবহার করা হয়েছে
                    # আপনি চাইলে কোডসহ দেখাতে পারেন: f"{course.course_code}: {course.title}"
                    # ==========================================
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
from django.db.models import Avg
from .models import Student, AcademicRecord
import joblib
import numpy as np
import os

# সঠিক মডেল পাথ সেট করুন (উদাহরণস্বরূপ: 'model.pkl')
MODEL_PATH = 'academic_risk_model.pkl' 

try:
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print("Model loaded successfully!")
    else:
        model = None
        print("Model file not found.")
except Exception as e:
    model = None
    print(f"Error loading model: {e}")

@login_required(login_url='login')
def student_profile(request, student_id):
    
    # ==========================================
    # স্মার্ট সলিউশন: ID এবং Student_ID দুইভাবেই কাজ করবে
    # ==========================================
    try:
        # ১. প্রথমে চেষ্টা করবে ডাটাবেস ID (Primary Key) দিয়ে খুঁজতে
        student = Student.objects.get(id=student_id)
    except (Student.DoesNotExist, ValueError):
        # ২. যদি ID দিয়ে না পাওয়া যায়, তখন student_id (রোল নম্বর) দিয়ে খুঁজবে
        # যদি এখানেও না পায়, কেবল তখনই 404 এরর দেখাবে
        student = get_object_or_404(Student, student_id=student_id)
    
    # বাকি কোড আগের মতোই থাকবে
    records = AcademicRecord.objects.filter(student=student).order_by('semester')

    # Attendance Logic (আপনার আগের ফিক্স)
    for record in records:
        if record.attendance:
            record.attendance_int = int(record.attendance)
        else:
            record.attendance_int = 0

    prediction = "No Data" # ডিফল্ট ভ্যালু সেট করা ভালো
    prediction_prob = 0 

    # Prediction Logic
    if request.method == 'POST' and records.exists() and 'model' in globals():
        try:
            # অ্যাভারেজ বের করা
            avg_stats = records.aggregate(
                Avg('attendance'), Avg('assignment'), Avg('quiz'), 
                Avg('midterm'), Avg('final'), Avg('gpa')
            )
            
            # ইনপুট ডাটা তৈরি
            # (নোট: None হ্যান্ডেল করার জন্য 'or 0' ব্যবহার করা হয়েছে)
            input_data = [[
                avg_stats['attendance__avg'] or 0,
                avg_stats['assignment__avg'] or 0,
                avg_stats['quiz__avg'] or 0,
                avg_stats['midterm__avg'] or 0,
                avg_stats['final__avg'] or 0,
                avg_stats['gpa__avg'] or 0
            ]]
            
            # প্রেডিকশন
            raw_prediction = model.predict(input_data)[0]
            
            if raw_prediction == 1 or raw_prediction == 'Risk' or str(raw_prediction) == '1':
                prediction = "High Risk"
            else:
                prediction = "Safe"

            # রিস্ক প্রবাবিলিটি বের করা
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(input_data)
                # ক্লাস ১ (রিস্ক) এর প্রবাবিলিটি নেওয়া
                if len(probs[0]) > 1:
                    risk_probability = probs[0][1] * 100 
                    prediction_prob = round(risk_probability, 2)
            
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


from django.db.models import Avg, Sum, Count, F
# নিশ্চিত করুন এই ইমপোর্টগুলো উপরে আছে
# from .models import Student, AcademicRecord, Course, StudentSubjectScore

@login_required(login_url='login')
def reports(request):
    # ১. ফিল্টার প্যারামিটার রিসিভ করা
    risk_filter = request.GET.get('risk_level')
    max_attendance = request.GET.get('max_attendance')
    max_gpa = request.GET.get('max_gpa')

    # ==========================================
    # ২. ইউনিক স্টুডেন্ট ডাটা প্রসেসিং
    # ==========================================
    report_data = []  # ফাইনাল লিস্ট যা টেবিলে দেখাবে
    
    # AI এর জন্য পরিসংখ্যান ভেরিয়েবল
    total_gpa_sum = 0
    total_att_sum = 0
    
    all_students = Student.objects.all().order_by('student_id')

    for student in all_students:
        # স্টুডেন্টের সব রেকর্ড থেকে গড় বের করা
        records = AcademicRecord.objects.filter(student=student)
        
        if records.exists():
            aggregates = records.aggregate(Avg('gpa'), Avg('attendance'))
            
            # ডাটা লোড
            avg_gpa = aggregates['gpa__avg'] or 0
            avg_att_days = aggregates['attendance__avg'] or 0 # এটি দিনে (Days) আছে
            
            # --- Attendance % Calculation (24 Days Logic) ---
            # সূত্র: (উপস্থিত দিন / ২৪) * ১০০
            att_percent = (avg_att_days / 24) * 100
            if att_percent > 100: att_percent = 100 # ক্যাপ ১০০%
            
            # --- Filtering Logic ---
            # যদি ইউজার ফিল্টার সেট করে, তবে চেক করা হবে
            if max_attendance and att_percent > float(max_attendance):
                continue 
            if max_gpa and avg_gpa > float(max_gpa):
                continue

            # রিস্ক স্ট্যাটাস নির্ধারণ
            is_high_risk = False
            if avg_gpa < 2.50 or att_percent < 60:
                is_high_risk = True

            # রিস্ক ফিল্টার চেক
            if risk_filter == 'High Risk' and not is_high_risk:
                continue
            elif risk_filter == 'Low Risk' and is_high_risk:
                continue 

            # লিস্টে যোগ করা (Unique Entry)
            report_data.append({
                'name': student.name,
                'student_id': student.student_id,
                'avg_gpa': round(avg_gpa, 2),
                'att_percent': round(att_percent, 1), # %
                'att_days': round(avg_att_days, 1),   # Days
                'is_risk': is_high_risk
            })
            
            # AI ক্যালকুলেশনের জন্য যোগ
            total_gpa_sum += avg_gpa
            total_att_sum += att_percent

    # ==========================================
    # ৩. AI Actions / Alerts (সাজানো ডাটার উপর ভিত্তি করে)
    # ==========================================
    ai_actions = []
    
    # হাই রিস্ক স্টুডেন্ট গণনা (যাদের GPA < 2.5 অথবা Attendance < 60%)
    high_risk_students = [s for s in report_data if s['avg_gpa'] < 2.5 or s['att_percent'] < 60]
    high_risk_count = len(high_risk_students)
    
    if high_risk_count > 0:
        ai_actions.append({
            'title': 'High Risk Alert',
            'desc': f'{high_risk_count} students found in critical academic risk.',
            'color': 'danger',
            'btn_text': 'View Students',
            'icon': 'fas fa-exclamation-triangle'
        })
    
    # লো অ্যাটেনডেন্স ওয়ার্নিং (যাদের Attendance < 50%)
    low_att_count = len([s for s in report_data if s['att_percent'] < 50])
    
    if low_att_count > 0:
        ai_actions.append({
            'title': 'Attendance Warning',
            'desc': f'{low_att_count} students have less than 50% attendance.',
            'color': 'warning',
            'btn_text': 'Send Notice',
            'icon': 'fas fa-clock'
        })

    # ==========================================
    # ৪. গ্রাফের জন্য ডাটা (Course Batch Wise)
    # ==========================================
    # আপনার মডেলে ফিল্ডের নাম: 'title' এবং 'marks'
    course_performance = StudentSubjectScore.objects.values('course__title').annotate(
        avg_marks=Avg('marks') 
    ).order_by('course__title')

    course_labels = []
    course_data = []

    for item in course_performance:
        # কোর্সের নাম
        course_labels.append(item['course__title']) 
        # গড় নম্বর
        course_data.append(round(item['avg_marks'], 1))

    # গ্রাফ যাতে ফাঁকা না দেখায়
    if not course_labels:
        course_labels = ['No Data']
        course_data = [0]

    # ==========================================
    # ৫. Gemini AI Text Analysis (Dynamic Generation)
    # ==========================================
    ai_response_text = ""
    total_students = len(report_data)
    
    if total_students > 0:
        class_avg_gpa = round(total_gpa_sum / total_students, 2)
        
        try:
            # API Key কনফিগারেশন
            genai.configure(api_key=GOOGLE_API_KEY)
            model_gemini = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            Analyze this academic report summary:
            - Total Unique Students: {total_students}
            - High Risk Count: {high_risk_count}
            - Class Average GPA: {class_avg_gpa}
            - Course Performance Data: {dict(zip(course_labels, course_data))}
            
            Provide 3 bullet points (HTML <li> tags) summarizing the class performance and suggesting improvements for the specific weak courses.
            """
            
            response = model_gemini.generate_content(prompt)
            ai_response_text = response.text
            
        except Exception as e:
            ai_response_text = f"<li>AI Analysis Temporarily Unavailable. ({str(e)})</li>"
    else:
        ai_response_text = "<li>No student data found matching your filters.</li>"

    # ==========================================
    # ৬. ফাইনাল রেন্ডার
    # ==========================================
    context = {
        'report_data': report_data,     # ইউনিক স্টুডেন্ট লিস্ট
        'ai_actions': ai_actions,       # অ্যালার্ট কার্ডের জন্য
        'course_labels': course_labels, # গ্রাফের লেবেল
        'course_data': course_data,     # গ্রাফের ডাটা
        'ai_response_text': ai_response_text, # Gemini's Response
        
        # ফিল্টার ভ্যালুগুলো টেমপ্লেটে ফেরত পাঠানো (যাতে ইনপুটে লেখা থাকে)
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

@login_required(login_url='login')
def ai_dashboard(request):
    students = Student.objects.all()
    student_risks = []
    
    total_students = students.count()
    high_risk_count = 0

    for student in students:
        last_record = AcademicRecord.objects.filter(student=student).order_by('-semester').first()
        
        if last_record:
            risk_status = "Safe"
            if last_record.gpa < 2.50 or last_record.attendance < 60:
                risk_status = "High Risk"
                high_risk_count += 1
            
            student_risks.append({
                'id': student.id,
                'student_id': student.student_id,
                'name': student.name,
                'gpa': last_record.gpa,
                'attendance': last_record.attendance,
                'risk': risk_status
            })
        else:
            student_risks.append({
                'id': student.id,
                'student_id': student.student_id,
                'name': student.name,
                'gpa': 'N/A',
                'attendance': 'N/A',
                'risk': 'Unknown'
            })

    context = {
        'student_risks': student_risks,
        'total_students': total_students,
        'high_risk_count': high_risk_count,
        'safe_count': total_students - high_risk_count
    }
    
    return render(request, 'ai_dashboard.html', context)