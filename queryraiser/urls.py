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
    path('facultylogin/',views.facultylogin,name='facultylogin'),
    path('facultydashboard/',views.facultydashboard,name='facultydashboard'),
    path('facultyraisecomplaint/',views.facultyraisecomplaint,name='facultyraisecomplaint'),
    path('raisecomplaint/',views.raisecomplaint,name='raisecomplaint'),
    path('technicianlogin/',views.technicianlogin,name='technicianlogin'),
    path('techniciandashboard/',views.techniciandashboard,name='techniciandashboard'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
