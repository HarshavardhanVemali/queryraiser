from django.contrib import admin
from django.urls import path
from queryraiserapp import views 
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.index,name='index'),
    path('adminlogin/',views.adminlogin,name='adminlogin'),
    path('admindashboard/',views.admindashboard,name='admindashboard'),
    path('adminpage/',views.adminpage,name='adminpage'),
    path('adminlogout/',views.admin_logout_view,name='adminlogout'),
    path('adminpage/', views.adminpage, name='adminpage'),
    path('adminfield/',views.adminfield,name='adminfield'),
    path('adddepartments/',views.adddepartments,name='adddepartments'),
    path('getdepartments/',views.get_departments,name='getdepartments'),
    path('savedepartmentchanges/',views.savedepartmentchanges,name='savedepartmentchanges'),
    path('deletedepartment/',views.deletedepartment,name='deletedepartment'),
    path('getfaculty/',views.get_faculty,name='getfaculty'),
    path('subadminfaculty.html', TemplateView.as_view(template_name='subadminfaculty.html'), name='subadminfaculty'),
    path('addfaculty/',views.addfaculty,name='addfaculty'),
    path('savefacultychanges/',views.savefacultychanges,name='savefacultychanges'),
    path('deletefaculty/',views.deletefaculty,name='deletefaculty'),
    path('admintechnician/',views.admintechnician,name='admintechnician'),
    path('getfields/',views.getfields,name='getfields'),
    path('gettechnicians/',views.gettechnicians,name='gettechnicians'),
    path('adminaddtechnicianfield/',views.adminaddtechnicianfield,name='adminaddtechnicianfield'),
    path('deletefield/',views.admindeletefield,name='deletefield'),
    path('addtechnician/',views.addtechnician,name='addtechnician'),
    path('deletetechnician/',views.deletetechnician,name='deletetechnician'),
    path('savetechnician/',views.savetechnician,name='savetechnician'),
    path('adminrecentcomplaints/',views.adminrecentcomplaints,name='adminrecentcomplaints'),
    path('admincomplaintscount/',views.admincomplaintscount,name='admincomplaintscount'),
    path('admintechnicianperformance/',views.admintechnicianperformance,name='admintechnicianperformance'),
    path('adminnewcomplaints/',views.adminnewcomplaints,name='adminnewcomplaints'),
    path('adminnewcomplaintstable/',views.adminnewcomplaintstable,name='adminnewcomplaintstable'),
    path('adminassigntechnician/',views.adminassigntechnician,name='adminassigntechnician'),
    path('get_technicians_by_field/', views.get_technicians_by_field, name='get_technicians_by_field'),
    path('assigntechnician/',views.assigntechnician,name='assigntechnician'),
    path('adminassignedcomplaints/',views.adminassignedcomplaints,name='adminassignedcomplaints'),
    path('getassignedcomplaints/',views.getassignedcomplaints,name='getassignedcomplaints'),
    path('adminclosedcomplaintspage/',views.adminclosedcomplaintspage,name='adminclosedcomplaintspage'),
    path('admin_get_closed_complaints/',views.admin_get_closed_complaints,name='admin_get_closed_complaints'),
    path('admintechnicianreports/',views.admintechnicianreports,name='admintechnicianreports'),
    path('adminfacultypendingpage/',views.adminfacultypendingpage,name='adminfacultypendingpage'),
    path('adminfacultypending/',views.adminfacultypending,name='adminfacultypending'),
    path('admintechnicianpendingpage/',views.admintechnicianpendingpage,name='admintechnicianpendingpage'),
    path('admintechnicianpending/',views.admintechnicianpending,name='admintechnicianpending'),
    path('adminresolvedpage/',views.adminresolvedpage,name='adminresolvedpage'),
    path('adminresolvedcomplaints/',views.adminresolvedcomplaints,name='adminresolvedcomplaints'),
    path('adminallcomplaintspage/',views.adminallcomplaintspage,name='adminallcomplaintspage'),
    path('adminallcomplaints/',views.adminallcomplaints,name='adminallcomplaints'),
    path('facultylogin/',views.facultylogin,name='facultylogin'),
    path('facultydashboard/',views.facultydashboard,name='facultydashboard'),
    path('facultyraisecomplaint/',views.facultyraisecomplaint,name='facultyraisecomplaint'),
    path('facultycomplaintcount/',views.facultycomplaintcount,name='facultycomplaintcount'),
    path('facultyrecentcomplaints/',views.facultyrecentcomplaints,name='facultyrecentcomplaints'),
    path('faculty_assigned_tech_page/',views.faculty_assigned_tech_page,name='faculty_assigned_tech_page'),
    path('faculty_assigned_complaints/',views.faculty_assigned_complaints,name='faculty_assigned_complaints'),
    path('raisecomplaint/',views.raisecomplaint,name='raisecomplaint'),
    path('faculty_all_complaints_page/',views.faculty_all_complaints_page,name='faculty_all_complaints_page'),
    path('facultyallcomplaints/',views.facultyallcomplaints,name='facultyallcomplaints'),
    path('faculty_closed_complaints_page/',views.faculty_closed_complaints_page,name='faculty_closed_complaints_page'),
    path('faculty_get_closed_complaints/',views.faculty_get_closed_complaints,name='faculty_get_closed_complaints'),
    path('facultynewcomplaintspage/',views.facultynewcomplaintspage,name='facultynewcomplaintspage'),
    path('facultynewcomplaints/',views.facultynewcomplaints,name='facultynewcomplaints'),
    path('facultyresolvedpage/',views.facultyresolvedpage,name='facultyresolvedpage'),
    path('facultyresolvedcomplaints/',views.facultyresolvedcomplaints,name='facultyresolvedcomplaints'),
    path('facultypendingpage/',views.facultypendingpage,name='facultypendingpage'),
    path('technicianlogin/',views.technicianlogin,name='technicianlogin'),
    path('techniciandashboard/',views.techniciandashboard,name='techniciandashboard'),
    path('techniciancomplaintcount/',views.techniciancomplaintcount,name='techniciancomplaintcount'),
    path('technicianrecentcomplaints/',views.technicianrecentcomplaints,name='technicianrecentcomplaints'),
    path('technicianassignedcomplaints/',views.technicianassignedcomplaints,name='technicianassignedcomplaints'),
    path('get_assigned_complaints_at_technician/',views.get_assigned_complaints_at_technician,name='get_assigned_complaints_at_technician'),
    path('techniciangetupdatestatus/',views.techniciangetupdatestatus,name='techniciangetupdatestatus'),
    path('technicianupdatepage/',views.technicianupdatepage,name='technicianupdatepage'),
    path('technicianupdatestatus/',views.technicianupdatestatus,name='technicianupdatestatus'),
    path('technician_all_complaints_page/',views.technician_all_complaints_page,name='technician_all_complaints_page'),
    path('technician_all_complaints/',views.technician_all_complaints,name='technician_all_complaints'),
    path('technicianclosedpage/',views.technicianclosedpage,name='technicianclosedpage'),
    path('technicianclosedcomplaints/',views.technicianclosedcomplaints,name='technicianclosedcomplaints'),
    path('technicianratingpage/',views.technicianratingpage,name='technicianratingpage'),
    path('technicianrating/',views.technicianrating,name='technicianrating'),
    path('technicianprofilepage/',views.technicianprofilepage,name='technicianprofilepage'),
    path('technicianprofile/',views.technicianprofile,name='technicianprofile')
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

