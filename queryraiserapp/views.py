from django.shortcuts import render,redirect
from django.http import JsonResponse, HttpResponse 
from .models import Department,Faculty,TechnicianField,Technician,User,Complaint
import json
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Permission
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.hashers import make_password,check_password
from django.contrib.auth import logout
import uuid
from django.contrib.auth import authenticate, login
from .models import FailedLoginAttempts
from phonenumbers import format_number, PhoneNumberFormat
from django.core import serializers 
from django.utils import timezone 
from django.db.models import Avg 

def admin_required(view_func):
    return user_passes_test(
        lambda u: u.is_superuser or u.has_perm('queryraiserapp.is_admin'), 
        login_url='/adminlogin/' 
    )(view_func)
def faculty_required(view_func):
    return user_passes_test(
        lambda u: (u.is_active or u.has_perm('queryraiserapp.is_faculty')) and not(u.is_superuser) and not(u.has_perm('queryraiserapp.is_technician')), 
        login_url='/facultylogin/'
    )(view_func)

def technician_required(view_func):
    return user_passes_test(
        lambda u: (u.is_active or u.has_perm('queryraiserapp.is_technician')) and not(u.is_superuser) and not(u.has_perm('queryraiserapp.is_faculty')), 
        login_url='/technicianlogin/'
    )(view_func)

def index(request):
    return render(request,'index.html')

@admin_required
def adminpage(request):
    return render(request,'adminpage.html')

@admin_required
def admindashboard(request):
    return render(request,'admindashboard.html')

MAX_FAILED_ATTEMPTS = 3
def set_device_cookie(response, device_id):
    response.set_cookie('device_id', device_id, max_age=365*24*60*60)

def get_device_id(request):
    return request.COOKIES.get('device_id', str(uuid.uuid4()))

def is_device_blocked(device_id):
    try:
        failed_attempt = FailedLoginAttempts.objects.get(device_id=device_id)
        if failed_attempt.is_active:
            return True
    except FailedLoginAttempts.DoesNotExist:
        return False
    return False

def adminlogin(request):
    if request.method == 'POST':
        device_id = get_device_id(request)
        if is_device_blocked(device_id):
            return render(request, 'index.html', {'blocked': True, 'error_message': 'Your device is permanently blocked due to multiple failed login attempts.'})

        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_superuser or (user.is_staff and not user.is_active):
                FailedLoginAttempts.objects.filter(device_id=device_id).update(attempts=0, is_active=False)
                response = redirect('admindashboard')
                set_device_cookie(response, device_id)
                login(request, user)
                return response
            else:
                return render(request, 'index.html', {'error_message': 'You do not have permission to access the admin page.'})
        else:
            failed_attempt, created = FailedLoginAttempts.objects.get_or_create(device_id=device_id)
            if not created:
                failed_attempt.attempts += 1
                failed_attempt.save()
                if failed_attempt.attempts >= MAX_FAILED_ATTEMPTS:
                    failed_attempt.is_active = True
                    failed_attempt.save()
                    return render(request, 'index.html', {'blocked': True, 'error_message': 'Your device is permanently blocked due to multiple failed login attempts.'})
            else:
                failed_attempt.attempts = 1
                failed_attempt.save()
            return render(request, 'index.html', {'error_message': 'Invalid username or password'})
    else:
        response = render(request, 'index.html')
        if 'device_id' not in request.COOKIES:
            device_id = get_device_id(request)
            set_device_cookie(response, device_id)
        return response


@admin_required
def admin_logout_view(request):
    logout(request)
    return redirect('index')

@admin_required
def adddepartments(request):
    if request.method == 'POST':
        if request.POST.get('form_type') == 'adddepartmentsform':
            department_name = request.POST.get('departmentname')
            department_code = request.POST.get('departmentcode')
            department_image = request.FILES.get('departmentimage')
            try:
                check_department=Department.objects.filter(department_code=department_code)
                if check_department:
                    return JsonResponse({'success': False, 'error': f'Department with id {department_code} already exists'})
                department = Department.objects.create(
                    department_code=department_code,
                    department_name=department_name,
                    department_logo=department_image
                )
                if department:
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Failed to add department.'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method or form type.'})
@admin_required
@require_POST
@csrf_exempt
def get_departments(request):
    if request.method == 'POST':
        departments = Department.objects.all()
        department_data = []
        for department in departments:
            department_data.append({
                'name': department.department_name,
                'code': department.department_code,
                'logo': department.department_logo.url if department.department_logo else None,
            })
        return JsonResponse(department_data, safe=False)
    return JsonResponse({'success': False, 'error': 'Invalid request method or form type.'})
@admin_required
@require_POST
def savedepartmentchanges(request):
    try:
        data = json.loads(request.body)
        department_code = data.get('department_code')
        department_name = data.get('department_name')
        
        current_department = Department.objects.get(department_code=department_code)
        current_department.department_name = department_name
        current_department.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@admin_required
@require_POST
def deletedepartment(request):
    try:
        data=json.loads(request.body)
        department_code=data.get('department_code')
        current_department=Department.objects.get(department_code=department_code)
        current_department.delete()
        return JsonResponse({'success':True})
    except Department.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Department not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@admin_required
@csrf_exempt
def get_faculty(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        department_code = data.get('department_code')
        if Department.objects.filter(department_code=department_code).exists():
            faculties = Faculty.objects.filter(department__department_code=department_code)
            department = Department.objects.get(department_code=department_code)
            get_department_name = department.department_name  
            get_department_image=department.department_logo.url if department.department_logo else None,
            faculty_list = [
                {
                    'name': faculty.faculty_name,
                    'facultyid': faculty.faculty_id,
                    'departmentname': faculty.department.department_name,
                    'departmentcode': faculty.department.department_code,
                    'phone_number': format_number(faculty.faculty_phonenumber, PhoneNumberFormat.NATIONAL).lstrip("0"),
                    'img': faculty.faculty_image.url if faculty.faculty_image else None
                }
                for faculty in faculties
            ]
            return JsonResponse({
                'faculty': faculty_list, 
                'department_name': get_department_name,
                'department_image':get_department_image
            }, safe=False)
        else:
            return JsonResponse({'error': 'No faculty found for this department.'}, status=404)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)
@admin_required
@csrf_exempt
def addfaculty(request):
    if request.method=='POST':
        if request.POST.get('form_type') == 'addfacultyform':
            facultyname=request.POST.get('facultyname')
            registenumber=request.POST.get('registernumber')
            department=request.POST.get('department')
            faculty_image=request.POST.get('facultyimage')
            phone_number=request.POST.get('phone')
            try:
                check_faculty=Faculty.objects.filter(faculty_id =registenumber)
                if check_faculty:
                    return JsonResponse({'success': False, 'error': f'Faculty with id {registenumber} already exists'})
                try:
                    department = Department.objects.get(department_code=department) 
                except Department.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Invalid department selected.'})
                hashed_password = make_password(registenumber)
                faculty = Faculty.objects.create(
                    faculty_id=registenumber,
                    faculty_name=facultyname,
                    department=department,
                    faculty_phonenumber=phone_number,
                    faculty_image=faculty_image,
                    username=registenumber, 
                    password=hashed_password,
                    role='faculty'
                )
                faculty_permission = Permission.objects.get(codename='is_faculty')
                faculty.user_permissions.add(faculty_permission) 
                if faculty:
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Failed to add Faculty.'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method or form type.'})

@admin_required
@require_POST
def savefacultychanges(request):
    try:
        data = json.loads(request.body)
        facultyid = data.get('faculty_id')
        faculty_name = data.get('faculty_name')
        faculty_number=data.get('faculty_number')
        current_faculty = Faculty.objects.get(faculty_id=facultyid)
        current_faculty.faculty_name=faculty_name
        current_faculty.faculty_phonenumber=faculty_number
        current_faculty.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@admin_required
@require_POST
def deletefaculty(request):
    try:
        data=json.loads(request.body)
        facultyid = data.get('faculty_id')
        current_faculty = Faculty.objects.get(faculty_id=facultyid)
        if current_faculty:
            current_faculty.delete()
            return JsonResponse({'success':True})
    except Department.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Faculty not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@admin_required
def admintechnician(request):
    return render(request,'admintechnician.html')

@admin_required
@require_POST
def getfields(request):
    technician_fields = list(TechnicianField.objects.values('field_name')) 
    return JsonResponse(technician_fields, safe=False)

@admin_required
@require_POST
def gettechnicians(request):
    if request.method == 'POST':
        technicians = list(Technician.objects.values(
            'technician_name', 
            'technician_number',
            'technician_field__field_name' 
        ))
        for technician in technicians:
            technician['technician_number'] = format_number(technician['technician_number'], PhoneNumberFormat.NATIONAL)
            technician['technician_number'] = technician['technician_number'].lstrip("0") 

        return JsonResponse(technicians, safe=False)
    
@admin_required
@require_POST
@csrf_exempt
def adminaddtechnicianfield(request):
    if request.method=='POST':
        if request.POST.get('form_type') != 'addfieldform':
            return JsonResponse({'success': False, 'error': 'Invalid form type.'})
        fieldname = request.POST.get('fieldname')
        if not fieldname:
            return JsonResponse({'success': False, 'error': 'Field name is required.'})
        if TechnicianField.objects.filter(field_name=fieldname).exists():
            return JsonResponse({'success': False, 'error': 'A field with this name already exists.'})
        field = TechnicianField.objects.create(field_name=fieldname)
        if field:
            return JsonResponse({'success': True}) 
        else: 
            return JsonResponse({'success': False, 'error': 'An error occurred while creating the field.'})
    return JsonResponse({'success':False,'message':'Invalid form request.'})

@admin_required
@require_POST
@csrf_exempt
def admindeletefield(request):
    if request.method=='POST':
        data=json.loads(request.body)
        field_name=data.get('field_name')
        if not(field_name):
            return JsonResponse({'success':False,'error':'Required missing fields.'})
        if not(TechnicianField.objects.filter(field_name=field_name).exists()):
            return JsonResponse({'success':False,'error':'Field not found.'})
        try:
            field=TechnicianField.objects.get(field_name=field_name).delete()
            return JsonResponse({'success':True})
        except Exception as e:
            return JsonResponse({'success':False,'error':str(e)})
    return JsonResponse({'success':False,'error':'Invalid request method.'})
        
@admin_required
def adminfield(request):
    return render(request,'adminfield.html')

@admin_required
@require_POST
@csrf_exempt
def addtechnician(request):
    if request.method == 'POST':
        technician_name = request.POST.get('technicianname')
        technician_field_name = request.POST.get('technicianfield') 
        technician_phone = request.POST.get('phone')
        print(technician_field_name, technician_name, technician_phone)
        try:
            if Technician.objects.filter(technician_number=technician_phone, technician_field__field_name=technician_field_name).exists():
                return JsonResponse({'success': False, 'error': f'Technician with Phone number {technician_phone} and Field {technician_field_name} already exists'})
            try:
                technician_field = TechnicianField.objects.get(field_name=technician_field_name) 
            except TechnicianField.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Invalid Technician Field selected.'})
            hashed_password = make_password(technician_phone)
            technician = Technician.objects.create(
                technician_name=technician_name,
                technician_number=technician_phone,
                technician_field=technician_field, 
                username=technician_phone,
                password=hashed_password,
                role='technician',
            )
            technician_permission = Permission.objects.get(codename='is_technician')
            technician.user_permissions.add(technician_permission)
            if technician:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Failed to add Technician.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method or form type.'})

@admin_required
@csrf_exempt
@require_POST
def savetechnician(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        technician_number = data.get('technician_number')
        technician_name = data.get('technician_name')
        technician_field_name = data.get('technician_field')
        change_technician_number=data.get('change_technician_number') 
        if not (technician_number and technician_name and technician_field_name):
            return JsonResponse({'success': False, 'error': 'Required fields are missing.'})
        try:
            technician_field = TechnicianField.objects.get(field_name=technician_field_name)
            technician = Technician.objects.get(
                technician_number=technician_number,
                technician_field=technician_field 
            )
            technician.technician_name = technician_name
            technician.technician_number=change_technician_number
            technician.save()
            return JsonResponse({'success': True})
        except TechnicianField.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid Technician Field selected.'})
        except Technician.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Technician not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error saving Technician: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@admin_required
@csrf_exempt
@require_POST
def deletetechnician(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        technician_number = data.get('technician_number')
        technician_field = data.get('technician_field')
        if not (technician_field and technician_number):
            return JsonResponse({'success': False, 'error': 'Required fields are missing.'})
        try:
            technician_field = TechnicianField.objects.get(field_name=technician_field)
            technician = Technician.objects.get(
                technician_number=technician_number,
                technician_field=technician_field
            )
            technician.delete()
            return JsonResponse({'success': True})

        except TechnicianField.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid Technician Field selected.'})
        except Technician.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Technician not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error deleting Technician: {str(e)}'})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@admin_required
@require_POST
def admincomplaintscount(request):
    if request.method == 'POST':
        try:
            complaint_counts = {
                'new': Complaint.objects.filter(status='new').count(),
                'assigned': Complaint.objects.filter(status='assigned').count(),
                'resolved': Complaint.objects.filter(status='resolved').count(),
                'pending_review': Complaint.objects.filter(status='pending_review').count(),
                'closed': Complaint.objects.filter(status='closed').count(),
                'reopened': Complaint.objects.filter(status='reopened').count(),
            }
            return JsonResponse({'success': True, 'complaint_counts': complaint_counts})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
@admin_required
@require_POST
def adminrecentcomplaints(request):
    if request.method == 'POST':
        try:
            recent_complaints = Complaint.objects.filter(status='new').values(
                'id','title','created_at', 
                'faculty__faculty_name',
                'department__department_name',
                'technician__technician_name',
                'status'
            ).order_by('-created_at')[:10]

            for complaint in recent_complaints:
                complaint['status'] = complaint['status'].capitalize()
                if complaint['technician__technician_name'] is None:
                    complaint['technician__technician_name'] = "Not Assigned"
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')  

            return JsonResponse(list(recent_complaints), safe=False)

        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@admin_required
@require_POST
def admintechnicianperformance(request):
    if request.method == 'POST':
        try:
            technician_performance = []
            for technician in Technician.objects.all():
                assigned = Complaint.objects.filter(technician=technician).count()
                resolved = Complaint.objects.filter(technician=technician, status='resolved').count()
                pending = Complaint.objects.filter(technician=technician, status__in=['new', 'assigned', 'in_progress', 'pending_review', 'reopened']).count()
                ratings = Complaint.objects.filter(technician=technician, rating__isnull=False)
                average_rating = ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
                if average_rating is None:
                    average_rating = "N/A" 

                technician_performance.append({
                    'name': technician.technician_name,
                    'assigned': assigned,
                    'resolved': resolved,
                    'pending': pending,
                    'rating': average_rating
                })

            return JsonResponse({'success': True, 'technician_performance': technician_performance})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@admin_required
def adminnewcomplaints(request):
    return render(request,'adminnewcomplaints.html')          

@admin_required
@require_POST
@csrf_exempt
def adminnewcomplaintstable(request):
    if request.method=='POST':
        try:
            recent_complaints = Complaint.objects.filter(status='new').values(
                'id',
                'title',
                'created_at', 
                'faculty__faculty_name',
                'department__department_name',
                'description',
            ).order_by('-created_at')[:]

            for complaint in recent_complaints:
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')  

            return JsonResponse(list(recent_complaints), safe=False)

        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)        

#facultylogin

@faculty_required
@csrf_exempt
def facultydashboard(request):
    faculty_name = request.session.get('faculty_name')
    register_number = request.session.get('register_number')
    context = {
        'faculty_name': faculty_name,
        'register_number': register_number,

    }
    return render(request, 'facultydashboard.html', context)

def facultylogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
            if user.role == 'faculty':
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    faculty = Faculty.objects.get(faculty_id=username)
                    request.session['faculty_name'] = faculty.faculty_name
                    request.session['register_number'] = faculty.faculty_id
                    return redirect('facultydashboard')
                else:
                    return render(request, 'index.html', {'faculty_error_message': 'Invalid username or password'})
            else:
                return render(request, 'index.html', {'faculty_error_message': 'Invalid User.'})
        except User.DoesNotExist:
            return render(request, 'index.html', {'faculty_error_message': 'User does not exist.'})

    return render(request, 'index.html')

@faculty_required
def facultyraisecomplaint(request):
    return render(request,'facultyraisecomplaint.html')

@faculty_required 
@csrf_exempt 
def raisecomplaint(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        faculty_id = request.session.get('register_number')  
        if not title or not description or not faculty_id: 
            return JsonResponse({'success': False, 'message': 'All fields are required.'}, status=400)
        try: 
            faculty = Faculty.objects.get(faculty_id=faculty_id)
            department = faculty.department  
        except Faculty.DoesNotExist: 
            return JsonResponse({'success': False, 'message': 'Faculty not found.'}, status=400) 
        complaint = Complaint.objects.create(
            faculty=faculty,
            department=department, 
            title=title,
            description=description,
        )
        return JsonResponse({'success': True, 'message': 'Complaint raised successfully!'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


#technicianlogin

@technician_required
@csrf_exempt
def techniciandashboard(request):
    technician_name= request.session.get('technician_name')
    technician_number = request.session.get('technician_number')
    context = {
        'technician_name': technician_name,
        'technician_number': technician_number,
    }
    return render(request, 'techniciandashboard.html', context)

def technicianlogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
            if user.role == 'technician': 
                try:
                    technician=Technician.objects.get('technician_number=username')
                except Technician.DoesNotExist:
                    return render(request,'index.html',{'technician_error_message':'Invalid User'})
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    technician = Technician.objects.get(technician_number=username)
                    request.session['technician_number'] = str(technician.technician_number) 
                    request.session['technician_name'] = technician.technician_name
                    return redirect('techniciandashboard') 
                else:
                    return render(request, 'index.html', {'technician_error_message': 'Invalid username or password'})
            else:
                return render(request, 'index.html', {'technician_error_message': 'Invalid User.'})
        except User.DoesNotExist:
            return render(request, 'index.html', {'technician_error_message': 'User does not exist.'})

    return render(request, 'index.html')