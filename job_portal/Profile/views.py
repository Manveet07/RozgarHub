from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.contrib import messages
from django.urls import path
from . import views
import json
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import os

def validate_image_file(file):
    """Validate uploaded image file"""
    if file:
        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("File size must be no more than 5MB")
        
        # Check file extension
        ext = os.path.splitext(file.name)[1].lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        if ext not in valid_extensions:
            raise ValidationError("Only .jpg, .jpeg, .png, and .gif files are allowed")
    return True

def validate_profile_data(data, user_type):
    """Validate profile form data"""
    errors = []
    
    # Common validations
    if not data.get('bio', '').strip():
        errors.append("Bio is required")
    if not data.get('phone', '').strip():
        errors.append("Phone number is required")
    if len(data.get('bio', '')) > 1000:
        errors.append("Bio must be less than 1000 characters")
        
    # User type specific validations
    if user_type == 'jobseeker':
        if not data.get('skills', '').strip():
            errors.append("Skills are required")
            
        # Validate experience entries
        exp_titles = data.getlist('experience_title[]')
        exp_descs = data.getlist('experience_description[]')
        if len(exp_titles) != len(exp_descs):
            errors.append("Invalid experience data")
        for title, desc in zip(exp_titles, exp_descs):
            if title and not desc:
                errors.append("Experience description is required")
            if desc and not title:
                errors.append("Experience title is required")
                
        # Validate education entries
        edu_degrees = data.getlist('education_degree[]')
        edu_descs = data.getlist('education_description[]')
        if len(edu_degrees) != len(edu_descs):
            errors.append("Invalid education data")
        for degree, desc in zip(edu_degrees, edu_descs):
            if degree and not desc:
                errors.append("Education description is required")
            if desc and not degree:
                errors.append("Degree title is required")
                
    else:  # employer validations
        if not data.get('company_name', '').strip():
            errors.append("Company name is required")
        if not data.get('about_company', '').strip():
            errors.append("Company description is required")
        
        # Validate company website URL
        website = data.get('company_website', '').strip()
        if website:
            try:
                URLValidator()(website)
            except ValidationError:
                errors.append("Invalid company website URL")
                
        employees = data.get('number_of_employees', '')
        if employees:
            try:
                num_employees = int(employees)
                if num_employees < 1:
                    errors.append("Number of employees must be positive")
            except ValueError:
                errors.append("Invalid number of employees")
    
    return errors

@login_required
def profile_display(request):
    """Display user profile"""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    context = {'profile': profile}
    
    if request.user.user_type == 'jobseeker':
        try:
            experiences = json.loads(profile.experience) if profile.experience else []
        except json.JSONDecodeError:
            experiences = []
            messages.error(request, "Error loading experience data")
            
        try:
            educations = json.loads(profile.education) if profile.education else []
        except json.JSONDecodeError:
            educations = []
            messages.error(request, "Error loading education data")
            
        context.update({
            'experiences': experiences,
            'educations': educations
        })
    
    return render(request, 'profile/profile_display.html', context)

@login_required
def profile_update(request):
    """Update user profile"""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Validate form data
        errors = validate_profile_data(request.POST, request.user.user_type)
        
        # Validate profile picture if uploaded
        if 'profile_picture' in request.FILES:
            try:
                validate_image_file(request.FILES['profile_picture'])
            except ValidationError as e:
                errors.extend(e.messages)
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'profile/profile_update.html', {'profile': profile})
        
        try:
            # Update profile information
            profile.bio = request.POST.get('bio', '').strip()
            profile.location = request.POST.get('location', '').strip()
            profile.phone = request.POST.get('phone', '').strip()
            
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            
            # Handle user type specific fields
            if request.user.user_type == 'jobseeker':
                profile.skills = request.POST.get('skills', '').strip()
                
                # Handle experience as JSON array
                experiences = []
                exp_titles = request.POST.getlist('experience_title[]')
                exp_descs = request.POST.getlist('experience_description[]')
                for title, desc in zip(exp_titles, exp_descs):
                    if title.strip() and desc.strip():
                        experiences.append({
                            'title': title.strip(),
                            'description': desc.strip()
                        })
                profile.experience = json.dumps(experiences) if experiences else ''
                
                # Handle education as JSON array
                educations = []
                edu_degrees = request.POST.getlist('education_degree[]')
                edu_descs = request.POST.getlist('education_description[]')
                for degree, desc in zip(edu_degrees, edu_descs):
                    if degree.strip() and desc.strip():
                        educations.append({
                            'degree': degree.strip(),
                            'description': desc.strip()
                        })
                profile.education = json.dumps(educations) if educations else ''
                
            else:  # employer fields
                profile.company_name = request.POST.get('company_name', '').strip()
                profile.company_website = request.POST.get('company_website', '').strip()
                profile.about_company = request.POST.get('about_company', '').strip()
                profile.industry = request.POST.get('industry', '').strip()
                employees = request.POST.get('number_of_employees', '').strip()
                profile.number_of_employees = int(employees) if employees.isdigit() else None
            
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_display')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
            return render(request, 'profile/profile_update.html', {'profile': profile})
    
    # If GET request or error in POST, show the form
    return render(request, 'profile/profile_update.html', {'profile': profile})
