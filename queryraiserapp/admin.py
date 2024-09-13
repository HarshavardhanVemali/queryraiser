from django.contrib import admin
from .models import Department,Faculty,TechnicianField,Technician,Complaint
from django.utils.safestring import mark_safe
from .models import FailedLoginAttempts

class FailedLoginAttemptsAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'attempts', 'is_active')
    list_filter = ('device_id', 'attempts', 'is_active')
    search_fields = ('device_id', 'attempts', 'is_active')
class DepartmentsAdmin(admin.ModelAdmin):
    list_display = ('department_code', 'department_name', 'preview_image')
    readonly_fields = ('preview_image',)

    def preview_image(self, obj):
        if obj.department_logo:
            return mark_safe(f'<img src="{obj.department_logo.url}" style="max-width: 200px; max-height: 150px;">')
        else:
            return 'No image found'

    list_filter = ('department_code', 'department_name')
    search_fields = ('department_code', 'department_name')

class FacultyAdmin(admin.ModelAdmin):
    list_display = ('faculty_id', 'faculty_name', 'department', 'preview_image')
    readonly_fields = ('preview_image',)

    def preview_image(self, obj):
        if obj.faculty_image:
            return mark_safe(f'<img src="{obj.faculty_image.url}" style="max-width: 200px; max-height: 150px;">')
        else:
            return 'No image found'

    list_filter = ('faculty_id', 'faculty_name','department')
    search_fields = ('faculty_id', 'faculty_name', 'department__department_name')

class TechnicianFieldAdmin(admin.ModelAdmin):
    list_display=('field_name',)

class TechnicianAdmin(admin.ModelAdmin):
    list_display=('technician_name','technician_number','technician_field')
    search_fields=('technician_name','technician_number','technician_field')
    list_filter=('technician_name','technician_number','technician_field')

class ComplaintAdmin(admin.ModelAdmin):
    list_display=('id','faculty','department','technician','title','description','created_at','updated_at','status','technician_comments','faculty_status','rating')
    search_fields=('id','faculty','department','technician','status')
    list_filter=('id','faculty','department','technician','status')

admin.site.register(FailedLoginAttempts,FailedLoginAttemptsAdmin)
admin.site.register(Department, DepartmentsAdmin)
admin.site.register(Faculty, FacultyAdmin)
admin.site.register(TechnicianField,TechnicianFieldAdmin)
admin.site.register(Technician,TechnicianAdmin)
admin.site.register(Complaint,ComplaintAdmin)