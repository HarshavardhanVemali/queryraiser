from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password
from phonenumbers import (
    PhoneNumber,
    parse,
    is_valid_number,
    format_number,
    PhoneNumberFormat,
)
from phonenumbers.phonenumberutil import NumberParseException

class PhoneNumberField(models.CharField):
    """
    Custom model field for storing and validating phone numbers.
    """

    def __init__(self, *args, region=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.region = region

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['region'] = self.region
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return parse(value, self.region)
        except NumberParseException:
            return value

    def get_prep_value(self, value):
        if isinstance(value, PhoneNumber):
            return format_number(value, PhoneNumberFormat.E164)
        elif value is None:
            return value
        else:
            try:
                parsed_number = parse(value, self.region)
                if is_valid_number(parsed_number):
                    return format_number(parsed_number, PhoneNumberFormat.E164)
                else:
                    raise ValueError("Invalid phone number")
            except NumberParseException:
                raise ValueError("Invalid phone number")

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return str(value) if value else ''
    
class FailedLoginAttempts(models.Model):
    device_id = models.CharField(max_length=255, unique=True)
    attempts = models.PositiveBigIntegerField(default=0)
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.device_id} - Attempts: {self.attempts}'
    
class User(AbstractUser):
    
    ROLES = (
        ('technician', 'Technician'),
        ('faculty', 'Faculty'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLES)
    def save(self, *args, **kwargs):
        if self.password and not self.has_usable_password():
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

class Department(models.Model):
    department_code = models.CharField(max_length=50, unique=True)
    department_name = models.CharField(max_length=250)
    department_logo = models.ImageField(upload_to='department_logo/', blank=True, null=True)
    
    def __str__(self):
        return self.department_name

class Faculty(User):
    faculty_id = models.CharField(max_length=20, unique=True)
    faculty_name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    faculty_image = models.ImageField(upload_to='faculty_images/', blank=True, null=True)
    faculty_phonenumber=PhoneNumberField(max_length=10, region='IN',null=True)
    def __str__(self):
        return self.faculty_name

class TechnicianField(models.Model):
    field_name=models.CharField(null=True,max_length=100,unique=True)
    def __str__(self):
        return self.field_name
    
class Technician(User):
    technician_name=models.CharField(max_length=100)
    technician_number=PhoneNumberField(max_length=13, region='IN')
    technician_field=models.ForeignKey(TechnicianField,on_delete=models.CASCADE)
    class Meta:
        unique_together = ('technician_number','technician_field')
    def __str__(self):
        return self.technician_name
    
class Complaint(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('pending_review', 'Pending Review'),
        ('closed', 'Closed'),
        ('reopened', 'Reopened'),
    ]
    id = models.AutoField(primary_key=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    technician_comments = models.TextField(null=True, blank=True)
    technician_resolve_time = models.DateTimeField(null=True, blank=True)
    faculty_feedback = models.CharField(
        max_length=100, 
        choices=[('resolved', 'Resolved'), ('pending', 'Pending')],
        null=True, blank=True
    )
    faculty_feedback_time = models.DateTimeField(null=True, blank=True) 
    rating=models.IntegerField(null=True)
    def __str__(self):
        return f"Complaint #{self.id} - {self.title}"
