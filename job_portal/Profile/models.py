from django.db import models
from jobs.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    skills = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Employer-specific fields
    company_name = models.CharField(max_length=100, blank=True)
    company_website = models.URLField(max_length=200, blank=True)
    about_company = models.TextField(blank=True)
    number_of_employees = models.IntegerField(null=True, blank=True)
    industry = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.first_name}'s Profile"
