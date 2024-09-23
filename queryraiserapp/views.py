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
from phonenumbers import format_number, PhoneNumberFormat, parse, NumberParseException
from django.core import serializers 
from django.utils import timezone 
from django.db.models import Avg 
import re
from django.db.models import Q

def admin_required(view_func):
    return user_passes_test(
        lambda u: u.is_superuser or u.has_perm('queryraiserapp.is_admin'), 
        login_url='/adminlogin/'
    )(view_func)

def faculty_required(view_func):
    return user_passes_test(
        lambda u: u.is_active and not u.is_superuser and u.role == 'faculty',  
        login_url='/facultylogin/'
    )(view_func)

def technician_required(view_func):
    return user_passes_test(
        lambda u: u.is_active and not u.is_superuser and u.role == 'technician', 
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
                faculty = Faculty.objects.get(pk=faculty.pk)
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
            technician = Technician.objects.get(pk=technician.pk) 
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
                'total':Complaint.objects.all().count(),
                'new': Complaint.objects.filter(status='new').count(),
                'assigned': Complaint.objects.filter(status='assigned').count(),
                'pending': Complaint.objects.filter(status='pending').count(),
                'resolved': Complaint.objects.filter(status='pending_review').count(),
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
            recent_complaints = Complaint.objects.filter().values(
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
                resolved = Complaint.objects.filter(technician=technician, status='pending_review').count()
                pending = Complaint.objects.filter(technician=technician,technician_status='pending').count()
                closed=Complaint.objects.filter(technician=technician,status='closed').count()
                ratings = Complaint.objects.filter(technician=technician, rating__isnull=False)
                average_rating = ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
                if average_rating is None:
                    average_rating = "N/A" 

                technician_performance.append({
                    'name': technician.technician_name,
                    'assigned': assigned,
                    'resolved': resolved,
                    'pending': pending,
                    'rating': average_rating,
                    'closed':closed,
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

@admin_required
def adminassigntechnician(request):
    return render(request,'adminassigntechnician.html')

@admin_required
@require_POST
@csrf_exempt
def get_technicians_by_field(request):
    if request.method == 'POST':
        data=json.loads(request.body)
        field_name=data.get('field_name')
        if field_name:
            try:
                technicianfield=TechnicianField.objects.get(field_name=field_name)
                technicians = Technician.objects.filter(technician_field=technicianfield).values('technician_number', 'technician_name')
                for technician in technicians:
                    technician['technician_number'] = str(technician['technician_number'])
                return JsonResponse({'success': True, 'technicians': list(technicians)})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            return JsonResponse({'success': False, 'error': 'Field name is required.'}, status=400)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@admin_required
@require_POST
@csrf_exempt
def assigntechnician(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        complaint_id = data.get('complaint_id')
        technician_number = data.get('technician') 
        if not (complaint_id and technician_number): 
            return JsonResponse({'success': False, 'error': 'Missing complaint_id or technician.'}, status=400)
        try:
            complaint = Complaint.objects.get(id=complaint_id)
            technician = Technician.objects.get(technician_number=technician_number) 
            complaint.technician = technician
            complaint.status = 'assigned' 
            complaint.assigned_time=timezone.now()
            complaint.save()
            return JsonResponse({'success': True, 'message': 'Technician assigned successfully.'})
        except Complaint.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Complaint with ID {complaint_id} does not exist.'}, status=404)
        except Technician.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Technician with number {technician_number} does not exist.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500) 

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@admin_required
def adminassignedcomplaints(request):
    return render(request,'adminassignedcomplaints.html')

@admin_required
def getassignedcomplaints(request):
    if request.method=='POST':
        try:
            assigned_complaints = Complaint.objects.filter(status='assigned').values(
                'id',
                'title',
                'created_at',
                'faculty__faculty_name',
                'department__department_name',
                'description',
                'technician__technician_name',
                'technician__technician_number',
            ).order_by('-created_at')

            for complaint in assigned_complaints:
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()  


            return JsonResponse(list(assigned_complaints), safe=False)

        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)        

@admin_required
def adminclosedcomplaintspage(request):
    return render(request,'adminclosedcomplaints.html')

@admin_required
@require_POST
@csrf_exempt
def admin_get_closed_complaints(request):
    if request.method=='POST':
        try:
            closed_complaints=Complaint.objects.filter(technician_status='resolved',faculty_status='resolved').values(
            'id',
            'title',
            'faculty__faculty_name',
            'department__department_name',
            'technician__technician_name',
            'technician__technician_number',
            'created_at',
            'assigned_time',
            'technician_resolve_time',
            'description',
            'technician_comments',
            'faculty_comments',
            'rating',
            'closed_time',
            'faculty_feedback_time'
            ).order_by('-created_at')
            for complaint in closed_complaints:
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['faculty_feedback_time']=timezone.localtime(complaint['faculty_feedback_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician_resolve_time'] = timezone.localtime(complaint['technician_resolve_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['closed_time'] = timezone.localtime(complaint['closed_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['assigned_time'] = timezone.localtime(complaint['assigned_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()  
                if complaint['technician_comments'] == "":
                    complaint['technician_comments']='--'
                if complaint['faculty_comments']=="":
                    complaint['faculty_comments']=='--'
                if complaint['rating'] is None:
                    complaint['rating']='N/A'
            return JsonResponse(list(closed_complaints), safe=False)
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
@admin_required
def adminfacultypendingpage(request):
    return render(request,'adminfacultypending.html')

@admin_required
def admintechnicianreports(request):
    return render(request,'admintechnicianreports.html')

@admin_required
@require_POST
@csrf_exempt
def adminfacultypending(request):
    if request.method=='POST':
        try:
            pending_complaints=Complaint.objects.filter(technician_status='resolved',faculty_status='pending').values(
            'id',
            'title',
            'faculty__faculty_name',
            'department__department_name',
            'technician__technician_name',
            'technician__technician_number',
            'created_at',
            'assigned_time',
            'technician_status',
            'faculty_status',
            'technician_resolve_time',
            'description',
            'technician_comments',
            'faculty_comments',
            ).order_by('-created_at')
            for complaint in pending_complaints:
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician_resolve_time'] = timezone.localtime(complaint['technician_resolve_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()  
            return JsonResponse(list(pending_complaints), safe=False)
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@admin_required
def admintechnicianpendingpage(request):
    return render(request,'admintechnicianpending.html')

@admin_required
@require_POST
@csrf_exempt
def admintechnicianpending(request):
    if request.method=='POST':
        try:
            pending_complaints=Complaint.objects.filter(technician_status='pending',faculty_status=None).values(
            'id',
            'title',
            'faculty__faculty_name',
            'department__department_name',
            'technician__technician_name',
            'technician__technician_number',
            'created_at',
            'assigned_time',
            'technician_status',
            'description',
            'technician_comments',
            ).order_by('-created_at')
            for complaint in pending_complaints:
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician_resolve_time'] = timezone.localtime(complaint['technician_resolve_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()  
            return JsonResponse(list(pending_complaints), safe=False)
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@admin_required
def adminresolvedpage(request):
    return render(request,'adminresolvedcomplaints.html')

@admin_required
@require_POST
@csrf_exempt
def adminresolvedcomplaints(request):
    if request.method=='POST':
        try:
            resolved_complaints=Complaint.objects.filter(status='pending_review').values(
            'id',
            'title',
            'faculty__faculty_name',
            'department__department_name',
            'technician__technician_name',
            'technician__technician_number',
            'created_at',
            'assigned_time',
            'technician_status',
            'description',
            'technician_comments',
            'faculty_status',
            'technician_resolve_time',
            ).order_by('-created_at')
            for complaint in resolved_complaints:
                if complaint['faculty_status'] is None:
                    complaint['faculty_status']='Pending_Review'
                    complaint['assigned_time']=timezone.localtime(complaint['assigned_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician_resolve_time'] = timezone.localtime(complaint['technician_resolve_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()  
                if complaint['technician_comments']=="":
                    complaint['technician_comments']='No Comments'
            return JsonResponse(list(resolved_complaints), safe=False)
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@admin_required
def adminallcomplaintspage(request):
    return render(request,'adminallcomplaints.html')

@admin_required
@require_POST
@csrf_exempt
def adminallcomplaints(request):
    if request.method=='POST':
        try:
            all_complaints=Complaint.objects.all().values(
            'id',
            'title',
            'faculty__faculty_name',
            'department__department_name',
            'technician__technician_name',
            'technician__technician_number',
            'created_at',
            'status',
            'faculty_status',
            'technician_status',
            'description',
            'assigned_time',
            ).order_by('-created_at')
            for complaint in all_complaints:
                complaint['status'] = complaint['status'].capitalize()
                complaint['faculty_status'] = complaint['faculty_status'].capitalize()
                complaint['technician_status'] = complaint['technician_status'].capitalize()
                complaint['title'] = complaint['title'].capitalize()
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                if complaint['assigned_time']is not None:
                    complaint['assigned_time'] = timezone.localtime(complaint['assigned_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip() 
                if complaint['status']=='new':
                    complaint['technician__technician_number']='Not Assigned'
                    complaint['technician__technician_name']='Not Assigned'
                    complaint['technician__technician_status']='--'
                    complaint['assigned_time']=='Not Assigned'
                if complaint['faculty_status'] is None:
                    complaint['faculty_status']='--'
                if complaint['technician_status']=='Resolved' and complaint['faculty_status'] is None:
                    complaint['faculty_status']='Pending_Review'
                if complaint['technician_status'] is None:
                    complaint['technician_status']='--'
            return JsonResponse(list(all_complaints), safe=False)
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@admin_required
def admindepartmentreportpage(request):
    return render(request,'admindepartmentreports.html')  

@admin_required
@require_POST
@csrf_exempt
def getdepartmentcomplaintscount(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        department_code = data.get('department_code')
        if not Department.objects.filter(department_code=department_code).exists():
            return JsonResponse({'success': False, 'error': f'Department with code {department_code} does not exist.'})
        try:
            department = Department.objects.get(department_code=department_code)
            complaint_counts = {
                'total': Complaint.objects.filter(department=department).count(), 
                'new': Complaint.objects.filter(status='new', department=department).count(), 
                'assigned': Complaint.objects.filter(status='assigned', department=department).count(), 
                'pending': Complaint.objects.filter(status='pending', department=department).count(),  
                'resolved': Complaint.objects.filter(status='pending_review', department=department).count(), 
                'closed': Complaint.objects.filter(status='closed', department=department).count(),  
                'reopened': Complaint.objects.filter(status='reopened', department=department).count(),
            }
            return JsonResponse({'success': True, 'complaint_counts': complaint_counts})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@admin_required
@require_POST
@csrf_exempt
def admingetdepartmentcomplaints(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            department_code = data.get('department_code')
            if not Department.objects.filter(department_code=department_code).exists():
                return JsonResponse({'success': False, 'error': f'Department with code {department_code} does not exist.'})
            department = Department.objects.get(department_code=department_code)
            get_department_name = department.department_name
            get_department_image = department.department_logo.url if department.department_logo else None
            complaints = Complaint.objects.filter(department__department_code=department_code).values(
                'id', 'title', 'created_at',
                'faculty__faculty_name',
                'faculty__faculty_phonenumber',
                'technician__technician_name',
                'status'
            ).order_by('-created_at')[:]
            for complaint in complaints:
                complaint['status'] = complaint['status'].capitalize()
                if complaint['technician__technician_name'] is None:
                    complaint['technician__technician_name'] = "Not Assigned"
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['faculty__faculty_phonenumber'] = format_number(
                    complaint['faculty__faculty_phonenumber'],
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()
            response_data = {
                'success': True,
                'complaints': list(complaints),
                'department_name': get_department_name,
                'department_image': get_department_image
            }
            return JsonResponse(response_data)

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

@faculty_required
@require_POST
@csrf_exempt
def facultycomplaintcount(request):
    if request.method=='POST':
        faculty_id=request.session.get('register_number')
        if not(faculty_id):
            return JsonResponse({'success':False,'error':'Require Faculty Id.'})
        try:
            faculty=Faculty.objects.filter(faculty_id=faculty_id).first()
            complaint_counts={
                'all':Complaint.objects.all().count(),
                'assigned': Complaint.objects.filter(status='assigned',faculty=faculty).count(),
                'pending': Complaint.objects.filter(status='pending',faculty=faculty).count(),
                'resolved': Complaint.objects.filter(status='pending_review',faculty=faculty).count(),
                'closed': Complaint.objects.filter(status='closed',faculty=faculty).count(),
                }
            return JsonResponse({'success': True, 'complaint_counts': complaint_counts})
        except Faculty.DoesNotExist:
            return JsonResponse({'success':False,'error':f'Faculty with Id {faculty_id} does not exists.'})
        except Exception as e:
            return JsonResponse({'success':False,'error':str(e)})
    return JsonResponse({'success':False,'error':'Invalid request method.'})

@faculty_required
@require_POST
def facultyrecentcomplaints(request):
    if request.method == 'POST':
        faculty_id=request.session.get('register_number')
        try:
            faculty=Faculty.objects.filter(faculty_id=faculty_id).first()
            recent_complaints = Complaint.objects.filter(faculty=faculty).values(
                'id',
                'title',
                'created_at',
                'technician__technician_name',
                'status'
            ).order_by('-created_at')[:10]

            for complaint in recent_complaints:
                complaint['status'] = complaint['status'].capitalize()
                if complaint['technician__technician_name'] is None:
                    complaint['technician__technician_name'] = "Not Assigned"
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')  

            return JsonResponse(list(recent_complaints), safe=False)
        except Faculty.DoesNotExist:
            return JsonResponse({'success':False,'error':f'Faculty with ID {faculty_id}does not exists.'})
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@faculty_required
def faculty_assigned_tech_page(request):
    return render(request,'facultyassignedcomplaints.html')

@faculty_required
@require_POST
@csrf_exempt
def faculty_assigned_complaints(request):
    if request.method=='POST':
        faculty_id=request.session.get('register_number')
        try:
            faculty=Faculty.objects.filter(faculty_id=faculty_id).first()
            recent_complaints = Complaint.objects.filter(faculty=faculty,status='assigned').values(
                'id',
                'title',
                'created_at',
                'technician__technician_name',
                'technician__technician_number',
                'description',
            ).order_by('-created_at')[:]

            for complaint in recent_complaints:
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()
                if complaint['technician__technician_name'] is None:
                    complaint['technician__technician_name'] = "Not Assigned"
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')  

            return JsonResponse(list(recent_complaints), safe=False)
        except Faculty.DoesNotExist:
            return JsonResponse({'success':False,'error':f'Faculty with ID {faculty_id}does not exists.'})
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@faculty_required
def faculty_all_complaints_page(request):
    return render(request,'facultyallcomplaints.html')

@faculty_required
@require_POST
@csrf_exempt
def facultyallcomplaints(request):
    if request.method == 'POST':
        faculty_id=request.session.get('register_number')
        try:
            faculty=Faculty.objects.filter(faculty_id=faculty_id).first()
            recent_complaints = Complaint.objects.filter(faculty=faculty).values(
                'id',
                'title',
                'created_at',
                'technician__technician_name',
                'status',
                'technician__technician_number',
            ).order_by('-created_at')[:]

            for complaint in recent_complaints:
                complaint['status'] = complaint['status'].capitalize()
                if complaint['technician__technician_name'] is None:
                    complaint['technician__technician_name'] = "Not Assigned"
                if complaint['technician__technician_number'] is None:
                    complaint['technician__technician_number']="Not Assigned"
                else:
                    complaint['technician__technician_number'] = format_number(
                        complaint['technician__technician_number'], 
                        PhoneNumberFormat.NATIONAL
                    ).lstrip('0').strip()
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')  

            return JsonResponse(list(recent_complaints), safe=False)
        except Faculty.DoesNotExist:
            return JsonResponse({'success':False,'error':f'Faculty with ID {faculty_id}does not exists.'})
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@faculty_required
def faculty_closed_complaints_page(request):
    return render(request,'facultyclosedcomplaints.html')

@faculty_required
@require_POST
@csrf_exempt
def faculty_get_closed_complaints(request):
    if request.method=='POST':
        faculty_id=request.session.get('register_number')
        try:
            faculty=Faculty.objects.filter(faculty_id=faculty_id).first()
            closed_complaints=Complaint.objects.filter(technician_status='resolved',faculty_status='resolved',faculty=faculty).values(
            'id',
            'title',
            'faculty__faculty_name',
            'department__department_name',
            'technician__technician_name',
            'technician__technician_number',
            'created_at',
            'assigned_time',
            'technician_resolve_time',
            'description',
            'technician_comments',
            'faculty_comments',
            'rating',
            'closed_time',
            'faculty_feedback_time'
            ).order_by('-created_at')
            for complaint in closed_complaints:
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician_resolve_time'] = timezone.localtime(complaint['technician_resolve_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['closed_time'] = timezone.localtime(complaint['closed_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['faculty_feedback_time'] = timezone.localtime(complaint['faculty_feedback_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()  
                if complaint['faculty_comments']=="":
                    complaint['faculty_comments']='No Comments'
                if complaint['technician_comments']=="":
                    complaint['technician_comments']='No Comments'
                if complaint['rating'] is None:
                    complaint['rating']='Not Given'
            return JsonResponse(list(closed_complaints), safe=False)
        except Faculty.DoesNotExist:
            return JsonResponse({'success':False,'error':f'Faculty with ID {faculty_id}does not exists.'})
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@faculty_required
def facultynewcomplaintspage(request):
    return render(request,'facultynewcomplaints.html')

@faculty_required
@require_POST
@csrf_exempt
def facultynewcomplaints(request):
    if request.method=='POST':
        faculty_id=request.session.get('register_number')
        try:
            faculty=Faculty.objects.filter(faculty_id=faculty_id).first()
            new_complaints=Complaint.objects.filter(status='new',faculty=faculty).values(
            'id',
            'title',
            'created_at',
            'status',
            'description',
            ).order_by('-created_at')
            for complaint in new_complaints:
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['status']=complaint['status'].capitalize()
            return JsonResponse(list(new_complaints), safe=False)
        except Faculty.DoesNotExist:
            return JsonResponse({'success':False,'error':f'Faculty with ID {faculty_id}does not exists.'})
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@faculty_required
def facultyresolvedpage(request):
    return render(request,'facultyresolvedcomplaints.html')

@faculty_required
@require_POST
@csrf_exempt
def facultyresolvedcomplaints(request):
    if request.method=='POST':
        faculty_id=request.session.get('register_number')
        try:
            faculty=Faculty.objects.filter(faculty_id=faculty_id).first()
            closed_complaints=Complaint.objects.filter(technician_status='resolved',faculty_status=None,faculty=faculty).values(
            'id',
            'title',
            'technician__technician_name',
            'technician__technician_number',
            'created_at',
            'assigned_time',
            'technician_resolve_time',
            'description',
            'technician_comments',
            ).order_by('-created_at')
            for complaint in closed_complaints:
                if complaint['technician_comments']=="":
                    complaint['technician_comments']='No Comments'
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician_resolve_time'] = timezone.localtime(complaint['technician_resolve_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()  
            return JsonResponse(list(closed_complaints), safe=False)
        except Faculty.DoesNotExist:
            return JsonResponse({'success':False,'error':f'Faculty with ID {faculty_id}does not exists.'})
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@faculty_required
def facultyupdatesstatus(request):
    return render(request,'facultyupdatestatus.html')

@faculty_required
@require_POST
@csrf_exempt
def facultygetupdates(request):
    if request.method == 'POST':
        faculty_id = request.session.get('register_number') 
        try:
            faculty = Faculty.objects.filter(faculty_id=faculty_id).first()
            if not faculty:
                return JsonResponse({'success': False, 'error': f'Faculty with {faculty_id} number does not exist.'})

            complaints = Complaint.objects.filter(faculty=faculty,technician_status='resolved').filter(Q(faculty_status='pending') | Q(faculty_status=None)
            ).values(
                'id',
                'title',
                'created_at',
                'technician__technician_name',
                'technician__technician_number',
                'technician_resolve_time',
                'technician_status',
                'technician_comments',
                'faculty_status',
                'faculty_comments'
            ).order_by('-created_at') 

            complaints = list(complaints)
            for complaint in complaints:
                complaint['technician_comments'] = complaint.get('technician_comments') or 'No Comments'
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician_resolve_time'] = timezone.localtime(complaint['technician_resolve_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()  
                complaint['technician_status']=complaint['technician_status'].capitalize()
            return JsonResponse(complaints, safe=False)

        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@faculty_required
@require_POST
@csrf_exempt
def facultyupdate(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status = data.get('status')
            complaint_id = data.get('complaint_id')
            comment = data.get('comment') 
            if not complaint_id:
                return JsonResponse({'success': False, 'error': 'Complaint ID is required.'})
            if not status:
                return JsonResponse({'success': False, 'error': 'Status is required.'})
            complaint = Complaint.objects.get(id=complaint_id)
            if complaint.faculty != request.user.faculty:
                return JsonResponse({'success': False, 'error': 'Unauthorized to update this complaint.'}) 

            complaint.faculty_status = status  
            complaint.faculty_comments = comment
            complaint.save()

            return JsonResponse({'success': True, 'message': 'Status updated successfully.'})

        except Complaint.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Complaint with id {complaint_id} not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@faculty_required
def facultypendingpage(request):
    return render(request,'facutlypendingcomplaints.html')

@faculty_required
@require_POST
@csrf_exempt
def facultypendigncomplaints(request):
    if request.method=='POST':
        faculty_id=request.session.get('register_number')
        try:
            faculty=Faculty.objects.filter(faculty_id=faculty_id).first()
            pending_complaints=Complaint.objects.filter(technician_status='pending',faculty_status=None,faculty=faculty).values(
            'id',
            'title',
            'technician__technician_name',
            'technician__technician_number',
            'created_at',
            'assigned_time',
            'description',
            'technician_status',
            'technician_comments',
            ).order_by('-created_at')
            for complaint in pending_complaints:
                if complaint['technician_comments'] is None:
                    complaint['technician_comments']='No Comments'
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician_resolve_time'] = timezone.localtime(complaint['technician_resolve_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()  
            return JsonResponse(list(pending_complaints), safe=False)
        except Faculty.DoesNotExist:
            return JsonResponse({'success':False,'error':f'Faculty with ID {faculty_id}does not exists.'})
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
@faculty_required
def facultyfeedbackpage(request):
    return render(request,'facultyfeedback.html')

@faculty_required
@require_POST
@csrf_exempt
def facultyfeedbacktable(request):
    if request.method == 'POST':
        faculty_id = request.session.get('register_number')
        try:
            faculty = Faculty.objects.filter(faculty_id=faculty_id).first()
            unrated_complaints = Complaint.objects.filter(
                status='closed', rating=None
            ).values(
                'id',
                'title',
                'technician__technician_name',
                'technician__technician_number',
                'created_at',
                'closed_time'
            ).order_by('-created_at')

            rated_complaints = Complaint.objects.filter(
                status='closed', rating__isnull=False
            ).values(
                'id',
                'title',
                'technician__technician_name',
                'technician__technician_number',
                'created_at',
                'closed_time',
                'rating'
            ).order_by('-created_at')

            for complaint in unrated_complaints:
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime(
                    '%Y-%m-%d %H:%M:%S'
                )
                complaint['closed_time'] = timezone.localtime(complaint['closed_time']).strftime(
                    '%Y-%m-%d %H:%M:%S'
                )
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()

            for complaint in rated_complaints:
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime(
                    '%Y-%m-%d %H:%M:%S'
                )
                complaint['closed_time'] = timezone.localtime(complaint['closed_time']).strftime(
                    '%Y-%m-%d %H:%M:%S'
                )
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()

            return JsonResponse({
                'unrated_complaints': list(unrated_complaints),
                'rated_complaints': list(rated_complaints)
            }, safe=False)

        except Faculty.DoesNotExist:
            return JsonResponse(
                {'success': False, 'error': f'Faculty with ID {faculty_id} does not exist.'}
            )
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


@faculty_required
@require_POST
@csrf_exempt
def save_rating(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            complaint_id = data.get('complaint_id')
            rating = data.get('rating')

            complaint = Complaint.objects.get(id=complaint_id)
            complaint.rating = rating
            complaint.save()

            return JsonResponse({'success': True})
        except Complaint.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Complaint not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
@faculty_required
def faculty_logout_view(request):
    logout(request)
    return redirect('index')

#technicianlogin

@technician_required
@csrf_exempt
def techniciandashboard(request):
    technician_name= request.session.get('technician_name')
    technician_number = request.session.get('technician_number')
    print(technician_number)
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
                    technician=Technician.objects.get(technician_number=username)
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

@technician_required
@require_POST
@csrf_exempt
def techniciancomplaintcount(request):
    technician_number = request.session.get('technician_number')
    if not technician_number:
        return JsonResponse({'success': False, 'error': 'Require Technician number.'})
    try:
        technician_number = re.sub(r"[^0-9+]", "", technician_number) 
        technician = Technician.objects.filter(technician_number=technician_number).first()
        if not technician:  
            return JsonResponse({'success':False,'error':f'Technician with {technician_number} number does not exist.'})

        complaint_counts = {
            'assigned': Complaint.objects.filter(status='assigned', technician=technician).count(),
            'resolved': Complaint.objects.filter(status='pending_review', technician=technician).count(),
            'pending': Complaint.objects.filter(status='pending', technician=technician).count(),
            'closed': Complaint.objects.filter(status='closed', technician=technician).count(),
        }
        return JsonResponse({'success': True, 'complaint_counts': complaint_counts})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@technician_required
@require_POST
def technicianrecentcomplaints(request):
    technician_number = request.session.get('technician_number')
    if not technician_number:
        return JsonResponse({'success': False, 'error': 'Require Technician number.'})
    try:
        technician_number = re.sub(r"[^0-9+]", "", technician_number) 
        technician = Technician.objects.filter(technician_number=technician_number).first()
        if not technician:
            return JsonResponse({'success':False,'error':f'Technician with {technician_number} number does not exist.'})

        recent_complaints = Complaint.objects.filter(technician=technician).values(
            'id',
            'title',
            'created_at',
            'faculty__faculty_name',
            'department__department_name',
            'status'
        ).order_by('-created_at')[:10]

        for complaint in recent_complaints:
            complaint['status'] = complaint['status'].capitalize()
            complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')

        return JsonResponse(list(recent_complaints), safe=False)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@technician_required
def technicianassignedcomplaints(request):
    return render(request,'technicianassignedcomplaints.html')

@technician_required
@require_POST
@csrf_exempt
def get_assigned_complaints_at_technician(request):
    if request.method=='POST':
        technician_number = request.session.get('technician_number')
        if not technician_number:
            return JsonResponse({'success': False, 'error': 'Require Technician number.'})
        try:
            technician_number = re.sub(r"[^0-9+]", "", technician_number) 
            technician = Technician.objects.filter(technician_number=technician_number).first()
            if not technician:
                return JsonResponse({'success':False,'error':f'Technician with {technician_number} number does not exist.'})
            assigned_complaints = Complaint.objects.filter(status='assigned',technician=technician).values(
                'id',
                'title',
                'created_at',
                'faculty__faculty_name',
                'department__department_name',
                'description',
                'faculty__faculty_phonenumber'
            ).order_by('-created_at') 
            for complaint in assigned_complaints:
                complaint['faculty__faculty_phonenumber'] = format_number(
                    complaint['faculty__faculty_phonenumber'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')  
            return JsonResponse(list(assigned_complaints), safe=False)

        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@technician_required
def technicianupdatepage(request):
    return render(request,'technicianupdatestatus.html')

@technician_required
@require_POST
@csrf_exempt
def techniciangetupdatestatus(request):
    if request.method=='POST':
        technician_number = request.session.get('technician_number')
        if not technician_number:
            return JsonResponse({'success': False, 'error': 'Require Technician number.'})
        try:
            technician_number = re.sub(r"[^0-9+]", "", technician_number) 
            technician = Technician.objects.filter(technician_number=technician_number).first()
            if not technician:
                return JsonResponse({'success':False,'error':f'Technician with {technician_number} number does not exist.'})
            complaints = Complaint.objects.filter(technician=technician).filter(Q(technician_status='pending') | Q(technician_status=None)
            ).values(
                'id',
                'title',
                'created_at',
                'faculty__faculty_name',
                'department__department_name',
                'description',
                'status',
                'technician_status',
                'technician_comments'
            ).order_by('-created_at')

            for complaint in complaints:
                complaint['status'] = complaint['status'].capitalize()
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')  
            return JsonResponse(list(complaints), safe=False)

        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
@technician_required
@require_POST
@csrf_exempt
def technicianupdatestatus(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status = data.get('status')
            complaint_id = data.get('complaint_id')
            comment = data.get('comment')

            if not complaint_id:
                return JsonResponse({'success': False, 'error': 'Complaint ID is required.'})
            if not status:
                return JsonResponse({'success': False, 'error': 'Status is required.'})

            complaint = Complaint.objects.get(id=complaint_id)
            complaint.technician_status = status
            complaint.technician_comments = comment 
            complaint.save()

            return JsonResponse({'success': True, 'message': 'Status updated successfully.'})
        except Complaint.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Complaint with id {complaint_id} not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@technician_required
def technicianresolvedpage(request):
    return render(request,'technicianresolvedcomplaints.html')

@technician_required
@require_POST
@csrf_exempt
def technicianresolvedcomplaints(request):
    if request.method=='POST':
        technician_number = request.session.get('technician_number')
        if not technician_number:
            return JsonResponse({'success': False, 'error': 'Require Technician number.'})
        try:
            technician_number = re.sub(r"[^0-9+]", "", technician_number) 
            technician = Technician.objects.filter(technician_number=technician_number).first()
            if not technician:
                return JsonResponse({'success':False,'error':f'Technician with {technician_number} number does not exist.'})
            assigned_complaints = Complaint.objects.filter(technician=technician,status='pending_review').values(
                'id',
                'title',
                'created_at',
                'faculty__faculty_name',
                'department__department_name',
                'description',
                'technician_resolve_time',
                'faculty__faculty_phonenumber',
                'status'
            ).order_by('-created_at') 
            for complaint in assigned_complaints:
                complaint['faculty__faculty_phonenumber'] = format_number(
                    complaint['faculty__faculty_phonenumber'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')  
                complaint['status'] = complaint['status'].capitalize()
            return JsonResponse(list(assigned_complaints), safe=False)

        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@technician_required
def technician_all_complaints_page(request):
    return render(request,'technicianallcomplaints.html')

@technician_required
def technician_all_complaints(request):
    if request.method=='POST':
        technician_number = request.session.get('technician_number')
        if not technician_number:
            return JsonResponse({'success': False, 'error': 'Require Technician number.'})
        try:
            technician_number = re.sub(r"[^0-9+]", "", technician_number) 
            technician = Technician.objects.filter(technician_number=technician_number).first()
            if not technician:
                return JsonResponse({'success':False,'error':f'Technician with {technician_number} number does not exist.'})
            assigned_complaints = Complaint.objects.filter(technician=technician).values(
                'id',
                'title',
                'created_at',
                'faculty__faculty_name',
                'department__department_name',
                'description',
                'faculty__faculty_phonenumber',
                'status'
            ).order_by('-created_at') 
            for complaint in assigned_complaints:
                complaint['faculty__faculty_phonenumber'] = format_number(
                    complaint['faculty__faculty_phonenumber'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')  
                complaint['status'] = complaint['status'].capitalize()
            return JsonResponse(list(assigned_complaints), safe=False)

        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
@technician_required
def technicianclosedpage(request):
    return render(request,'technicianclosedcomplaints.html')

@technician_required
@require_POST
@csrf_exempt
def technicianclosedcomplaints(request):
    if request.method=='POST':
        technician_number = request.session.get('technician_number')
        if not technician_number:
            return JsonResponse({'success': False, 'error': 'Require Technician number.'})
        try:
            technician_number = re.sub(r"[^0-9+]", "", technician_number) 
            technician = Technician.objects.filter(technician_number=technician_number).first()
            if not technician:
                return JsonResponse({'success':False,'error':f'Technician with {technician_number} number does not exist.'})
            closed_complaints=Complaint.objects.filter(technician=technician,technician_status='resolved',faculty_status='resolved').values(
            'id',
            'title',
            'faculty__faculty_name',
            'department__department_name',
            'created_at',
            'assigned_time',
            'technician_resolve_time',
            'description',
            'technician_comments',
            'faculty_comments',
            'rating',
            'technician__technician_number',
            'closed_time',
            'faculty_feedback_time'
            ).order_by('-created_at')
            for complaint in closed_complaints:
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician_resolve_time'] = timezone.localtime(complaint['technician_resolve_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician__technician_number'] = format_number(
                    complaint['technician__technician_number'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()  
                complaint['faculty_feedback_time']=timezone.localtime(complaint['faculty_feedback_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['closed_time'] = timezone.localtime(complaint['closed_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['assigned_time'] = timezone.localtime(complaint['assigned_time']).strftime('%Y-%m-%d %H:%M:%S')
                if complaint['technician_comments'] == "":
                    complaint['technician_comments']='--'
                if complaint['faculty_comments']=="":
                    complaint['faculty_comments']=='--'
                if complaint['rating'] is None:
                    complaint['rating']='N/A'
            return JsonResponse(list(closed_complaints), safe=False)
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
@technician_required
def technicianratingpage(request):
    return render(request,'technicianrating.html')

@technician_required
@require_POST
@csrf_exempt
def technicianrating(request):
    if request.method == 'POST':
        technician_number = request.session.get('technician_number')
        if not technician_number:
            return JsonResponse({'success': False, 'error': 'Require Technician number.'})

        try:
            technician_number = re.sub(r"[^0-9+]", "", technician_number)
            technician = Technician.objects.filter(technician_number=technician_number).first()
            if not technician:
                return JsonResponse({'success': False, 'error': f'Technician with {technician_number} number does not exist.'})

            technician_performance = Complaint.objects.filter(
                technician=technician,
                technician_status='resolved',
                faculty_status='resolved',
                status='closed',
            ).values(
                'id',
                'title',
                'faculty__faculty_name',
                'department__department_name',
                'created_at',
                'assigned_time',
                'rating',
                'closed_time'
            ).annotate(
                avg_rating=Avg('rating')  
            ).order_by('-created_at')
            for complaint in technician_performance:
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['assigned_time'] = timezone.localtime(complaint['assigned_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['closed_time'] = timezone.localtime(complaint['closed_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['rating'] = complaint.get('rating', 'N/A') 
                complaint['avg_rating'] = complaint.get('avg_rating', 'N/A')
                if complaint['rating'] is None:
                    complaint['rating']='Not Given'

            return JsonResponse(list(technician_performance), safe=False)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
@technician_required
def technicianprofilepage(request):
    return render(request,'technicianprofile.html')

@technician_required
def technicianprofile(request):
    if request.method == 'POST':
        technician_number = request.session.get('technician_number')
        if not technician_number:
            return JsonResponse({'success': False, 'error': 'Require Technician number.'})
        try:
            technician_number = re.sub(r"[^0-9+]", "", technician_number)
            technician = Technician.objects.filter(technician_number=technician_number).first()
            if not technician:
                return JsonResponse({'success': False, 'error': f'Technician with {technician_number} number does not exist.'})
            technician_number=technician.technician_number
            technician_number=format_number(
                    technician_number, 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()  
            technician_name=technician.technician_name
            technician_field=technician.technician_field
            ratings = Complaint.objects.filter(technician=technician, rating__isnull=False)
            average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] 
            if average_rating is not None:
                average_rating = round(average_rating, 1) 
            else:
                average_rating = 0
            complaint_counts={
                'all': Complaint.objects.all().count(),
                'pending': Complaint.objects.filter(technician_status='pending',faculty_status='pending', technician=technician).count(),
                'closed': Complaint.objects.filter(status='closed', technician=technician).count(),
                'average_rating': average_rating, 
            }  
            return JsonResponse({'success': True, 'technician_number': technician_number, 
                                'technician_name': technician_name, 'technician_field': str(technician_field), 
                                'complaint_counts': complaint_counts})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@technician_required
def technicianpendingpage(request):
    return render(request,'technicianpending.html')

@technician_required
@require_POST
@csrf_exempt
def technicianpendingcomplaints(request):
    if request.method=='POST':
        technician_number = request.session.get('technician_number')
        if not technician_number:
            return JsonResponse({'success': False, 'error': 'Require Technician number.'})
        try:
            technician_number = re.sub(r"[^0-9+]", "", technician_number)
            technician = Technician.objects.filter(technician_number=technician_number).first()
            if not technician:
                return JsonResponse({'success': False, 'error': f'Technician with {technician_number} number does not exist.'})
            closed_complaints=Complaint.objects.filter(technician_status='resolved',faculty_status='pending',technician=technician).values(
            'id',
            'title',
            'faculty__faculty_name',
            'faculty__faculty_phonenumber',
            'department__department_name',
            'technician_resolve_time',
            'created_at',
            'assigned_time',
            'description',
            'faculty_status',
            'faculty_comments',
            ).order_by('-created_at')
            for complaint in closed_complaints:
                if complaint['faculty_comments'] is None:
                    complaint['faculty_comments']='No Comments'
                complaint['created_at'] = timezone.localtime(complaint['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['technician_resolve_time'] = timezone.localtime(complaint['technician_resolve_time']).strftime('%Y-%m-%d %H:%M:%S')
                complaint['faculty__faculty_phonenumber'] = format_number(
                    complaint['faculty__faculty_phonenumber'], 
                    PhoneNumberFormat.NATIONAL
                ).lstrip('0').strip()  
            return JsonResponse(list(closed_complaints), safe=False)
        except Faculty.DoesNotExist:
            return JsonResponse({'success':False,'error':f'Technician with ID {technician_number}does not exists.'})
        except Exception as e: 
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
  
@technician_required
def technician_logout_view(request):
    logout(request)
    return redirect('index')
    
