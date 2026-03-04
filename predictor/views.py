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


from .models import Student, AcademicRecord, Course, StudentSubjectScore


from .forms import StudentForm, CourseForm, AcademicRecordForm, SubjectScoreForm


model = None
try:
   
    model_path = os.path.join(settings.BASE_DIR, 'risk_model.pkl')

    if os.path.exists(model_path):
        model = joblib.load(model_path)
        print(f"✅ Model loaded successfully from: {model_path}")
    else:
        print(f"⚠️ Warning: Model not found at {model_path}")
        
except Exception as e:
    print(f"⚠️ Error loading model: {e}")


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

    
    overall_gpa = AcademicRecord.objects.aggregate(Avg('gpa'))['gpa__avg'] or 0

    model_path = os.path.join(settings.BASE_DIR, 'risk_model.pkl')
    model = None
    try:
        model = joblib.load(model_path)
    except:
        print("⚠️ Dashboard: Risk Model not found, using manual fallback.")

    risk_count = 0
    TOTAL_CLASS_DAYS = 24

   
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
              
                r_att = record.attendance if record.attendance else 0
                r_pct = (r_att / TOTAL_CLASS_DAYS) * 100
                if r_pct > 100: r_pct = 100

                input_data = pd.DataFrame([{
                    'Attendance': r_pct,
                    'Assignment': record.assignment or 0,
                    'Quiz': record.quiz or 0,
                    'Final': record.final or 0,
                    'Previous_GPA': record.gpa
                }])
                

                
                try:
                    pred = model.predict(input_data)[0]
                    if pred == 'High Risk' or pred == 'Risk':
                        sem_risk_count += 1
                        last_sem_status = "High Risk"
                    else:
                        last_sem_status = "Safe"
                except:
                    pass
            
           
            if last_sem_status == "High Risk":
                is_at_risk = True
            elif sem_risk_count >= (total_sems / 2):
                is_at_risk = True
            
            if is_at_risk:
                risk_count += 1
    else:
       
        risk_count = 0
        for student in all_students_check:
            last_rec = AcademicRecord.objects.filter(student=student).last()
            if last_rec and last_rec.gpa < 2.50:
                risk_count += 1

    safe_count = total_students - risk_count

   
    semester_data = AcademicRecord.objects.values('semester').annotate(avg_gpa=Avg('gpa')).order_by('semester')
    sem_labels = [data['semester'] for data in semester_data]
    sem_gpa = [round(data['avg_gpa'], 2) for data in semester_data]

 
    model_path = os.path.join(settings.BASE_DIR, 'risk_model.pkl')
    model = None
    try:
        model = joblib.load(model_path)
    except:
        print("⚠️ Risk Model not found!")

    TOTAL_CLASS_DAYS = 24
    recent_records = []
    
   
    students_with_records = Student.objects.filter(academicrecord__isnull=False).distinct()

    for student in students_with_records:
       
        all_records = AcademicRecord.objects.filter(student=student).order_by('semester')
        
       
        latest_record = all_records.last() 
        
        if latest_record:
            
           
            present_days = latest_record.attendance if latest_record.attendance else 0
            calculated_percent = (present_days / TOTAL_CLASS_DAYS) * 100
            if calculated_percent > 100: calculated_percent = 100
            
            latest_record.att_percent = round(calculated_percent, 1)
            latest_record.days_present = int(present_days)

           
            risk_count = 0
            total_semesters = all_records.count()
            last_sem_status = "Safe"
            final_risk_status = "Safe" 

            if model:
              
                for record in all_records:
                   
                    r_att = record.attendance if record.attendance else 0
                    r_pct = (r_att / TOTAL_CLASS_DAYS) * 100
                    if r_pct > 100: r_pct = 100

                    input_data = pd.DataFrame([{
                        'Attendance': r_pct,
                        'Assignment': record.assignment or 0,
                        'Quiz': record.quiz or 0,
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
                
                
                if last_sem_status == "High Risk":
                    final_risk_status = "High Risk"
                elif risk_count >= (total_semesters / 2):
                    final_risk_status = "High Risk"
            
            else:
               
                if calculated_percent < 60 or latest_record.gpa < 2.5:
                    final_risk_status = "High Risk"

            
            latest_record.ai_status = final_risk_status
            
            recent_records.append(latest_record)

  
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

   
    context = {
        'total_students': total_students,
        'avg_attendance': round(avg_attendance_percent, 1),
        'overall_gpa': round(overall_gpa, 2),
        'risk_count': risk_count,
        'recent_records': recent_records,
        'sem_labels': json.dumps(sem_labels),
        'sem_gpa': json.dumps(sem_gpa),
        'risk_data': json.dumps([safe_count, risk_count]),
        
       
        'semester_performance': json.dumps(semester_performance),
    }

    return render(request, 'dashboard.html', context)
   
    context = {
        'total_students': total_students,
        'avg_attendance': round(avg_attendance_percent, 1),
        'overall_gpa': round(overall_gpa, 2),
        'risk_count': risk_count,
        'recent_records': recent_records,
        
        
        'sem_labels': json.dumps(sem_labels),
        'sem_gpa': json.dumps(sem_gpa),
        'risk_data': json.dumps([safe_count, risk_count]),
        
       
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
    
   
    try:
        student = Student.objects.get(id=student_id)
    except (Student.DoesNotExist, ValueError):
        student = get_object_or_404(Student, student_id=student_id)
    
    records = AcademicRecord.objects.filter(student=student).order_by('semester')

   
    model_path = os.path.join(settings.BASE_DIR, 'risk_model.pkl')
    model = None
    try:
        model = joblib.load(model_path)
    except Exception as e:
        print(f"⚠️ Model not found or error loading: {e}")

    final_prediction = "Unknown"
    total_semesters = records.count()
    TOTAL_CLASS_DAYS = 24

    sum_attendance_pct = 0
    sum_assignment = 0
    sum_quiz = 0
    sum_final = 0
    sum_gpa = 0

    if model and total_semesters > 0:
        for record in records:
          
            att_days = record.attendance if record.attendance else 0
            att_percent = (att_days / TOTAL_CLASS_DAYS) * 100
            if att_percent > 100: att_percent = 100
            
            sum_attendance_pct += att_percent
            sum_assignment += (record.assignment or 0)
            sum_quiz += (record.quiz or 0)
            sum_final += (record.final or 0)
            sum_gpa += (record.gpa or 0.0)

       
        avg_attendance = sum_attendance_pct / total_semesters
        avg_assignment = sum_assignment / total_semesters
        avg_quiz = sum_quiz / total_semesters
        avg_final = sum_final / total_semesters
        avg_gpa = sum_gpa / total_semesters

      
        input_data = pd.DataFrame([{
            'Attendance': avg_attendance,
            'Assignment': avg_assignment,
            'Quiz': avg_quiz,
            'Final': avg_final,
            'Previous_GPA': avg_gpa
        }])

       
        try:
            final_prediction = model.predict(input_data)[0]
        except Exception as e:
            print(f"Prediction Error: {e}")
            final_prediction = "Error"

    context = {
        'student': student,
        'records': records,
        'prediction': final_prediction,
        'total_semesters': total_semesters
    }
    
    return render(request, 'student_profile.html', context)

from django.db.models import Avg, Sum, Count, F

# from .models import Student, AcademicRecord, Course, StudentSubjectScore

from django.shortcuts import render
from .models import Student, AcademicRecord, StudentSubjectScore
from django.db.models import Avg
import joblib
import pandas as pd
import os
from django.conf import settings
import google.generativeai as genai



@login_required(login_url='login')
def reports(request):
   
    risk_filter = request.GET.get('risk_level')
    max_attendance = request.GET.get('max_attendance')
    max_gpa = request.GET.get('max_gpa')

 
    model_path = os.path.join(settings.BASE_DIR, 'risk_model.pkl')
    model = None
    try:
        model = joblib.load(model_path)
    except:
        print("⚠️ risk_model.pkl not found!")

    TOTAL_CLASS_DAYS = 24
    
  
    report_data = []  
    
  
    total_gpa_sum = 0
    total_att_sum = 0
    
    all_students = Student.objects.all().order_by('student_id')

    for student in all_students:
        records = AcademicRecord.objects.filter(student=student).order_by('semester')
        
        if records.exists():
            
            aggregates = records.aggregate(Avg('gpa'), Avg('attendance'))
            avg_gpa = aggregates['gpa__avg'] or 0
            avg_att_days = aggregates['attendance__avg'] or 0
            
          
            att_percent_display = (avg_att_days / TOTAL_CLASS_DAYS) * 100
            if att_percent_display > 100: att_percent_display = 100

           
            
            is_high_risk = False # ডিফল্ট সেইফ
            risk_count = 0
            total_semesters = records.count()
            last_sem_status = "Safe"

            if model:
                
                for record in records:
                  
                    r_att = record.attendance if record.attendance else 0
                    r_pct = (r_att / TOTAL_CLASS_DAYS) * 100
                    if r_pct > 100: r_pct = 100

                    input_data = pd.DataFrame([{
                        'Attendance': r_pct,
                        'Assignment': record.assignment or 0,
                        'Quiz': record.quiz or 0,
                        
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
                
              
                if last_sem_status == "High Risk":
                    is_high_risk = True
                elif risk_count >= (total_semesters / 2):
                    is_high_risk = True
                else:
                    is_high_risk = False
            else:
               
                if avg_gpa < 2.5: is_high_risk = True

           
            if max_attendance and att_percent_display > float(max_attendance):
                continue 
            if max_gpa and avg_gpa > float(max_gpa):
                continue

           
            if risk_filter == 'High Risk' and not is_high_risk:
                continue
            elif risk_filter == 'Low Risk' and is_high_risk:
                continue 

          
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

   
    ai_actions = []
    
    
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
    
    
    low_att_count = len([s for s in report_data if s['att_percent'] < 50])
    if low_att_count > 0:
        ai_actions.append({
            'title': 'Attendance Warning',
            'desc': f'{low_att_count} students have critically low attendance (<50%).',
            'color': 'warning',
            'btn_text': 'Send Notice',
            'icon': 'fas fa-clock'
        })

   
    course_performance = StudentSubjectScore.objects.values('course__title').annotate(
        avg_marks=Avg('marks') 
    ).order_by('course__title')

    course_labels = [item['course__title'] for item in course_performance]
    course_data = [round(item['avg_marks'], 1) for item in course_performance]

    if not course_labels:
        course_labels = ['No Data']
        course_data = [0]

    import os
import json
import joblib
import pandas as pd
import numpy as np
import openpyxl
from io import BytesIO
from xhtml2pdf import pisa
import google.generativeai as genai

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Q, Count, Sum
from django.http import HttpResponse
from django.template.loader import get_template
from django.core.paginator import Paginator
from django.contrib.auth.forms import PasswordChangeForm


from .models import Student, AcademicRecord, Course, StudentSubjectScore
from .forms import StudentForm, CourseForm, AcademicRecordForm, SubjectScoreForm


GOOGLE_API_KEY = "AIzaSyBOlMr0jl8HX7eDRvQHmyJdMOo7p4ZD-Io" 
TOTAL_CLASS_DAYS = 24


model = None
model_path = os.path.join(settings.BASE_DIR, 'risk_model.pkl')

try:
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        print(f"✅ Model loaded successfully from: {model_path}")
    else:
        print(f"⚠️ Warning: Model not found at {model_path}")
except Exception as e:
    print(f"⚠️ Error loading model: {e}")




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




@login_required(login_url='login')
def dashboard(request):
  
    total_students = Student.objects.count()
    
    
    avg_att_days = AcademicRecord.objects.aggregate(Avg('attendance'))['attendance__avg'] or 0
    avg_attendance_percent = (avg_att_days / TOTAL_CLASS_DAYS) * 100
    if avg_attendance_percent > 100: avg_attendance_percent = 100
    
    overall_gpa = AcademicRecord.objects.aggregate(Avg('gpa'))['gpa__avg'] or 0

   
    risk_count = 0
    recent_records = []
    
    
    students = Student.objects.all()
    
    for student in students:
       
        record = AcademicRecord.objects.filter(student=student).last()
        
        if record:
            
            present_days = record.attendance if record.attendance else 0
            calculated_percent = (present_days / TOTAL_CLASS_DAYS) * 100
            if calculated_percent > 100: calculated_percent = 100
            
            record.att_percent = round(calculated_percent, 1)
            
            # --- AI Prediction Logic ---
            status = "Safe"
            if model:
                try:
                    input_data = pd.DataFrame([{
                        'Attendance': calculated_percent, 
                        'Assignment': record.assignment or 0,
                        'Quiz': record.quiz or 0,
                        'Final': record.final or 0,
                        'Previous_GPA': record.gpa
                    }])
                    status = model.predict(input_data)[0]
                except Exception as e:
                    pass
            else:
                # Fallback Logic
                if calculated_percent < 50 or record.gpa < 2.5:
                    status = "High Risk"

            
            if status == "High Risk" or status == "Risk":
                risk_count += 1
                record.ai_status = "High Risk"
            else:
                record.ai_status = "Safe"
                
            recent_records.append(record)

  
    safe_count = total_students - risk_count
    
    
    recent_records.sort(key=lambda x: x.id, reverse=True)
    recent_records = recent_records[:5]

    
    semester_data = AcademicRecord.objects.values('semester').annotate(avg_gpa=Avg('gpa')).order_by('semester')
    sem_labels = [data['semester'] for data in semester_data]
    sem_gpa = [round(data['avg_gpa'], 2) for data in semester_data]

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
        if subject_data:
            semester_performance[sem] = subject_data

    context = {
        'total_students': total_students,
        'avg_attendance': round(avg_attendance_percent, 1),
        'overall_gpa': round(overall_gpa, 2),
        'risk_count': risk_count,
        'safe_count': safe_count,
        'recent_records': recent_records,
        'sem_labels': json.dumps(sem_labels),
        'sem_gpa': json.dumps(sem_gpa),
        'risk_data': json.dumps([safe_count, risk_count]),
        'semester_performance': json.dumps(semester_performance),
    }

    return render(request, 'dashboard.html', context)




@login_required(login_url='login')
def student_list(request):
    students = Student.objects.all().order_by('student_id')

    
    batches = Student.objects.values_list('batch', flat=True).distinct().order_by('batch')
    selected_batch = request.GET.get('batch')
    
    if selected_batch:
        students = students.filter(batch=selected_batch)

  
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


@login_required(login_url='login')
def student_profile(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
    except (Student.DoesNotExist, ValueError):
        student = get_object_or_404(Student, student_id=student_id)
    
    records = AcademicRecord.objects.filter(student=student).order_by('semester')
    
    final_prediction = "Unknown"
    
    if records.exists():
      
        aggregates = records.aggregate(
            Avg('attendance'), Avg('assignment'), Avg('quiz'), Avg('final'), Avg('gpa')
        )
        
        avg_att_days = aggregates['attendance__avg'] or 0
        avg_att_percent = (avg_att_days / TOTAL_CLASS_DAYS) * 100
        if avg_att_percent > 100: avg_att_percent = 100

        if model:
            try:
                input_data = pd.DataFrame([{
                    'Attendance': avg_att_percent,
                    'Assignment': aggregates['assignment__avg'] or 0,
                    'Quiz': aggregates['quiz__avg'] or 0,
                    'Final': aggregates['final__avg'] or 0,
                    'Previous_GPA': aggregates['gpa__avg'] or 0
                }])
                final_prediction = model.predict(input_data)[0]
            except Exception:
                final_prediction = "Error"
    
    context = {
        'student': student,
        'records': records,
        'prediction': final_prediction,
        'total_semesters': records.count()
    }
    return render(request, 'student_profile.html', context)



from django.core.cache import cache
import google.generativeai as genai
from django.db.models import Avg

@login_required(login_url='login')
def reports(request):
  
    risk_filter = request.GET.get('risk_level')
    max_attendance = request.GET.get('max_attendance')
    max_gpa = request.GET.get('max_gpa')

    report_data = []
    total_gpa_sum = 0
    
  
    all_students = Student.objects.all().order_by('student_id')

    for student in all_students:
        records = AcademicRecord.objects.filter(student=student).order_by('semester')
        
        if not records.exists():
            continue

      
        aggregates = records.aggregate(Avg('gpa'), Avg('attendance'))
        avg_gpa = aggregates['gpa__avg'] or 0
        avg_att_days = aggregates['attendance__avg'] or 0
        
        
        TOTAL_CLASS_DAYS = 24
        att_percent_display = (avg_att_days / TOTAL_CLASS_DAYS) * 100
        if att_percent_display > 100: att_percent_display = 100

     
        is_high_risk = False
        
       
        if avg_gpa < 2.5 or att_percent_display < 50:
            is_high_risk = True

       
        if max_attendance and att_percent_display > float(max_attendance): continue
        if max_gpa and avg_gpa > float(max_gpa): continue
        if risk_filter == 'High Risk' and not is_high_risk: continue
        if risk_filter == 'Low Risk' and is_high_risk: continue

        report_data.append({
            'name': student.name,
            'student_id': student.student_id,
            'avg_gpa': round(avg_gpa, 2),
            'att_percent': round(att_percent_display, 1),
            'is_risk': is_high_risk
        })
        
        total_gpa_sum += avg_gpa

 
    total_students_count = len(report_data)
    high_risk_count = sum(1 for item in report_data if item['is_risk'])
    
    if total_students_count > 0:
        class_avg_gpa = round(total_gpa_sum / total_students_count, 2)
    else:
        class_avg_gpa = 0

   
    ai_response_text = ""
    
 
    cache_key = f"ai_report_v2_{total_students_count}_{high_risk_count}_{class_avg_gpa}"
    
    cached_summary = cache.get(cache_key)

    if cached_summary:
        ai_response_text = cached_summary
        print("✅ Using Cached AI Response")
    
    elif total_students_count > 0:
        try:
            
            genai.configure(api_key='AIzaSyAdi3YURePmybTCWGAu_nlkyDLIsPGUawE') 
            
          
            model_gemini = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
Act as a Senior Academic Advisor for a University Faculty.
Data Context:
- Class Average CGPA: {class_avg_gpa} (Scale: 4.00)
- Total Students: {total_students_count}
- Critical Risk Students: {high_risk_count} (Low attendance/grades)

Task: Provide 3 strategic, actionable steps for the teacher to improve this specific class performance.
Format: HTML <li> tags only. Keep it professional but direct.
"""
            
            response = model_gemini.generate_content(prompt)
            ai_response_text = response.text
            
            
            cache.set(cache_key, ai_response_text, 86400)
            
        except Exception as e:
            ai_response_text = "<li>AI Analysis unavailable temporarily.</li>"
            print(f"🔴 Gemini Error: {e}")
    else:
        ai_response_text = "<li>No student data found to analyze.</li>"

  
    course_performance = StudentSubjectScore.objects.values('course__title').annotate(avg_marks=Avg('marks')).order_by('course__title')
    course_labels = [item['course__title'] for item in course_performance]
    course_data = [round(item['avg_marks'], 1) for item in course_performance]
    
    if not course_labels:
        course_labels = ['No Data']
        course_data = [0]

    context = {
        'report_data': report_data,
        'course_labels': course_labels, 
        'course_data': course_data,
        'ai_response_text': ai_response_text,
        'selected_risk': risk_filter,
        
        'total_students': total_students_count,
        'risk_count': high_risk_count,
        'class_avg_gpa': class_avg_gpa
    }
    
    return render(request, 'reports.html', context)


# ==========================================
# 🧠 ৫. AI ড্যাশবোর্ড (Dedicated AI View)
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
            att_days = last_record.attendance if last_record.attendance else 0
            att_pct = (att_days / TOTAL_CLASS_DAYS) * 100
            if att_pct > 100: att_pct = 100

            risk_status = "Safe"
            color_class = "success"

            if model:
                try:
                    input_data = pd.DataFrame([{
                        'Attendance': att_pct,
                        'Assignment': last_record.assignment or 0,
                        'Quiz': last_record.quiz or 0,
                        'Final': last_record.final or 0,
                        'Previous_GPA': last_record.gpa or 0.0
                    }])
                    risk_status = model.predict(input_data)[0]
                except Exception:
                    pass
            
            if risk_status == "High Risk" or risk_status == "Risk":
                high_risk_count += 1
                color_class = "danger"
            
            student_risks.append({
                'id': student.id,
                'student_id': student.student_id,
                'name': student.name,
                'gpa': last_record.gpa,
                'attendance': f"{att_days}/{TOTAL_CLASS_DAYS} ({round(att_pct)}%)",
                'risk': risk_status,
                'color': color_class
            })
        else:
            student_risks.append({
                'id': student.id, 'student_id': student.student_id, 'name': student.name,
                'gpa': 'N/A', 'attendance': 'N/A', 'risk': 'Unknown', 'color': 'secondary'
            })

    context = {
        'student_risks': student_risks,
        'total_students': total_students,
        'high_risk_count': high_risk_count,
        'safe_count': total_students - high_risk_count
    }
    return render(request, 'ai_dashboard.html', context)


# ==========================================
# ➕ ৬. ডাটা এন্ট্রি এবং ফর্ম প্রসেসিং
# ==========================================

@login_required(login_url='login')
def add_data(request):
    # মেইন ফর্ম পেজ রেন্ডার
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
        else:
            messages.error(request, f'Error: {form.errors}')
    return redirect('add_data')

@login_required(login_url='login')
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Course added successfully!')
        else:
            messages.error(request, f'Error: {form.errors}')
    return redirect('add_data')

@login_required(login_url='login')
def add_academic_record(request):
    if request.method == 'POST':
        form = AcademicRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Academic Record added successfully!')
        else:
            messages.error(request, f'Error: {form.errors}')
    return redirect('add_data')

@login_required(login_url='login')
def add_subject_score(request):
    if request.method == 'POST':
        form = SubjectScoreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Subject Score added successfully!')
        else:
            messages.error(request, f'Error: {form.errors}')
    return redirect('add_data')


# ==========================================
# 📥 ৭. এক্সপোর্ট ফিচার (Excel/PDF)
# ==========================================

@login_required(login_url='login')
def export_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Academic_Report.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Student Report"
    headers = ['Student ID', 'Name', 'Semester', 'GPA', 'Attendance (%)', 'Risk Status']
    ws.append(headers)

    for student in Student.objects.all():
        latest = AcademicRecord.objects.filter(student=student).last()
        if latest:
            risk = "Low Risk"
            if latest.gpa < 2.5 or latest.attendance < 12: # <50% approx
                risk = "High Risk"
            ws.append([student.student_id, student.name, latest.semester, latest.gpa, latest.attendance, risk])

    wb.save(response)
    return response

@login_required(login_url='login')
def export_pdf(request):
    student_data = []
    for student in Student.objects.all():
        latest = AcademicRecord.objects.filter(student=student).last()
        risk = "Low"
        if latest and (latest.gpa < 2.5 or latest.attendance < 12):
            risk = "High"
        
        student_data.append({
            'name': student.name, 'id': student.student_id,
            'gpa': latest.gpa if latest else 0.0,
            'attendance': latest.attendance if latest else 0.0,
            'risk': risk
        })

    html = get_template('pdf_template.html').render({'students': student_data})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Academic_Report.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('PDF Error')
    return response


# ==========================================
# ⚙️ ৮. সেটিংস এবং অ্যাডমিন
# ==========================================

@login_required(login_url='login')
def admin_settings(request):
    user = request.user
    if request.method == 'POST':
        if 'change_password' in request.POST:
            form = PasswordChangeForm(user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('admin_settings')
            else:
                messages.error(request, 'Please correct the password errors.')
    else:
        form = PasswordChangeForm(user)

    return render(request, 'admin_settings.html', {'password_form': form})