from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, login
from .services import JobPortalService
from django.http import JsonResponse, FileResponse
import os
from django.conf import settings
from .models import Application, Job
import requests
import json

def index(request):
    jobs = JobPortalService.get_jobs()
    return render(request, 'index.html', {'jobs': jobs})

def about(request):
    return render(request, 'about.html')

def rojgarhub(request):
    return redirect('index')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Email and password are required')
            return render(request, 'login.html')
        
        try:
            # Make API call to Flask backend
            response = requests.post(
                'http://localhost:5000/api/auth/login',
                json={'email': email, 'password': password},
                headers={'Content-Type': 'application/json'},
                verify=False  # Only for development
            )
            
            print(f"Login response status: {response.status_code}")  # Debug
            print(f"Login response content: {response.content}")  # Debug
            
            if response.status_code == 200:
                data = response.json()
                
                # Store in session
                request.session['user_token'] = str(data.get('id'))  # Convert to string
                request.session['user_type'] = data.get('user_type')
                request.session['user_email'] = email
                request.session.set_expiry(86400)  # 24 hours
                
                # Create or get Django user
                User = get_user_model()
                user, created = User.objects.get_or_create(
                    username=email,
                    defaults={
                        'email': email,
                        'user_type': data.get('user_type'),
                        'is_active': True
                    }
                )
                
                if not created:
                    # Update user_type in case it changed
                    user.user_type = data.get('user_type')
                    user.save()
                
                login(request, user)
                
                print(f"User type: {data.get('user_type')}")  # Debug
                print(f"Session data: {dict(request.session)}")  # Debug
                
                if data.get('user_type') == 'employer':
                    return redirect('employer_dashboard')
                else:
                    return redirect('dashboard')
            else:
                error_data = response.json()
                messages.error(request, error_data.get('error', 'Invalid credentials'))
                
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {str(e)}")  # Debug
            messages.error(request, 'Error connecting to authentication server')
        except Exception as e:
            print(f"Unexpected error: {str(e)}")  # Debug
            messages.error(request, f'An unexpected error occurred: {str(e)}')
            
    return render(request, 'login.html')

def signup(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        user_type = request.POST['user_type']
        
        # Check if passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'signup.html')
            
        try:
            # Make API call to Flask backend
            response = requests.post('http://localhost:5000/api/auth/signup', 
                json={
                    'email': email,
                    'password': password,
                    'user_type': user_type
                },
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                # Create Django user to ensure user_type is synchronized
                User = get_user_model()
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    user_type=user_type
                )
                messages.success(request, 'Account created successfully. Please log in.')
                return redirect('login')
            else:
                error_data = response.json()
                messages.error(request, error_data.get('error', 'Error creating account'))
        except requests.exceptions.RequestException:
            messages.error(request, 'Error connecting to server')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            
    return render(request, 'signup.html')

@login_required
def dashboard(request):
    user_token = request.session.get('user_token')
    user_type = request.session.get('user_type')
    
    if not user_token or not user_type:
        messages.error(request, 'Please log in to access the dashboard')
        return redirect('login')
    
    try:
        # Common headers for API requests
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if user_type == 'jobseeker':
            # Get jobs from Flask API - no auth needed for GET
            try:
                jobs_response = requests.get(
                    'http://localhost:5000/api/jobs',
                    headers=headers,
                    timeout=10,
                    verify=False  # Only for development
                )
                
                print(f"Jobs API Response Status: {jobs_response.status_code}")  # Debug
                print(f"Jobs API Response Headers: {jobs_response.headers}")  # Debug
                print(f"Jobs API Response Content: {jobs_response.content}")  # Debug
                
                if jobs_response.status_code == 200:
                    try:
                        jobs = jobs_response.json()
                        print(f"Successfully parsed jobs data: {jobs}")  # Debug
                    except json.JSONDecodeError as e:
                        print(f"JSON parsing error: {str(e)}")  # Debug
                        print(f"Raw response content: {jobs_response.content}")  # Debug
                        messages.error(request, 'Error parsing jobs data')
                        jobs = []
                else:
                    print(f"Error response from jobs API: {jobs_response.status_code}")  # Debug
                    messages.error(request, 'Error fetching jobs')
                    jobs = []
            except requests.exceptions.RequestException as e:
                print(f"Request error: {str(e)}")  # Debug
                messages.error(request, 'Error connecting to jobs server')
                jobs = []
            
            # Get user's applications from Flask API - auth needed
            try:
                applications_response = requests.get(
                    'http://localhost:5000/api/applications',
                    headers={
                        **headers,
                        'Authorization': f'Bearer {user_token}'
                    },
                    timeout=10,
                    verify=False  # Only for development
                )
                
                print(f"Applications API Response Status: {applications_response.status_code}")  # Debug
                print(f"Applications API Response Headers: {applications_response.headers}")  # Debug
                print(f"Applications API Response Content: {applications_response.content}")  # Debug
                
                if applications_response.status_code == 200:
                    try:
                        applications = applications_response.json()
                        print(f"Successfully parsed applications data: {applications}")  # Debug
                    except json.JSONDecodeError as e:
                        print(f"JSON parsing error: {str(e)}")  # Debug
                        print(f"Raw response content: {applications_response.content}")  # Debug
                        messages.error(request, 'Error parsing applications data')
                        applications = []
                else:
                    print(f"Error response from applications API: {applications_response.status_code}")  # Debug
                    messages.error(request, 'Error fetching applications')
                    applications = []
            except requests.exceptions.RequestException as e:
                print(f"Request error: {str(e)}")  # Debug
                messages.error(request, 'Error connecting to applications server')
                applications = []
            
            context = {
                'jobs': jobs,
                'applications': applications,
                'user_token': user_token,
                'user_type': user_type
            }
            
            return render(request, 'jobseeker_dashboard.html', context)
            
        elif user_type == 'employer':
            # Get employer's jobs from Flask API - auth needed
            try:
                jobs_response = requests.get(
                    'http://localhost:5000/api/jobs/employer',
                    headers={
                        **headers,
                        'Authorization': f'Bearer {user_token}'
                    },
                    timeout=10,
                    verify=False  # Only for development
                )
                
                print(f"Employer Jobs API Response Status: {jobs_response.status_code}")  # Debug
                print(f"Employer Jobs API Response Headers: {jobs_response.headers}")  # Debug
                print(f"Employer Jobs API Response Content: {jobs_response.content}")  # Debug
                
                if jobs_response.status_code == 200:
                    try:
                        employer_jobs = jobs_response.json()
                        print(f"Successfully parsed employer jobs data: {employer_jobs}")  # Debug
                    except json.JSONDecodeError as e:
                        print(f"JSON parsing error: {str(e)}")  # Debug
                        print(f"Raw response content: {jobs_response.content}")  # Debug
                        messages.error(request, 'Error parsing jobs data')
                        employer_jobs = []
                else:
                    print(f"Error response from employer jobs API: {jobs_response.status_code}")  # Debug
                    messages.error(request, 'Error fetching jobs')
                    employer_jobs = []
            except requests.exceptions.RequestException as e:
                print(f"Request error: {str(e)}")  # Debug
                messages.error(request, 'Error connecting to jobs server')
                employer_jobs = []
            
            context = {
                'jobs': employer_jobs,
                'user_token': user_token,
                'user_type': user_type
            }
            
            return render(request, 'employer_dashboard.html', context)
            
        else:
            messages.error(request, 'Invalid user type')
            return redirect('login')
            
    except Exception as e:
        print(f"Unexpected error in dashboard: {str(e)}")  # Debug
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('login')

@login_required
def post_job(request):
    if request.method == 'POST':
        # Verify user is an employer
        user_type = request.session.get('user_type')
        user_token = request.session.get('user_token')
        
        if user_type != 'employer':
            messages.error(request, 'Only employers can post jobs')
            return redirect('dashboard')
            
        if not user_token:
            messages.error(request, 'Please log in to post a job')
            return redirect('login')

        try:
            # Prepare job data
            job_data = {
                'title': request.POST['title'],
                'company': request.POST['company'],
                'description': request.POST['description'],
                'location': request.POST['location'],
                'employer_id': user_token
            }

            # Make API call to Flask backend
            response = requests.post(
                'http://localhost:5000/api/jobs',
                json=job_data,
                headers={
                    'Authorization': f'Bearer {user_token}',
                    'Content-Type': 'application/json'
                }
            )

            if response.status_code == 200:
                messages.success(request, 'Job posted successfully!')
                return redirect('employer_dashboard')
            else:
                try:
                    error_data = response.json()
                    messages.error(request, error_data.get('error', 'Error posting job'))
                except ValueError:
                    messages.error(request, 'Error posting job: Invalid response from server')
                return redirect('employer_dashboard')

        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error connecting to server: {str(e)}')
            return redirect('employer_dashboard')
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')
            return redirect('employer_dashboard')
    
    return render(request, 'post_job.html')

@login_required
def apply_job(request, job_id):
    if request.method == 'POST' and request.session.get('user_type') == 'jobseeker':
        try:
            user_token = request.session.get('user_token')
            if not user_token:
                return JsonResponse({
                    'error': 'Authentication required',
                    'details': 'Please log in to apply for jobs'
                }, status=401)

            # Validate file
            if 'resume' not in request.FILES:
                return JsonResponse({
                    'error': 'Missing file',
                    'details': 'Resume file is required'
                }, status=400)

            resume = request.FILES['resume']
            allowed_types = ('.pdf', '.doc', '.docx', '.png')
            if not resume.name.lower().endswith(allowed_types):
                return JsonResponse({
                    'error': 'Invalid file type',
                    'details': f'Allowed file types are: {", ".join(t[1:] for t in allowed_types)}'
                }, status=400)

            # Validate cover letter
            cover_letter = request.POST.get('cover_letter', '').strip()
            if not cover_letter:
                return JsonResponse({
                    'error': 'Missing cover letter',
                    'details': 'Please provide a cover letter'
                }, status=400)

            # Prepare multipart form data
            files = {'resume': resume}
            data = {
                'job_id': job_id,
                'cover_letter': cover_letter
            }

            # Make API call to Flask backend
            try:
                response = requests.post(
                    'http://localhost:5000/api/applications',
                    files=files,
                    data=data,
                    headers={'Authorization': f'Bearer {user_token}'},
                    timeout=10
                )

                # Parse response
                if response.headers.get('content-type', '').lower().startswith('application/json'):
                    try:
                        response_data = response.json()
                    except ValueError:
                        return JsonResponse({
                            'error': 'Invalid JSON response',
                            'details': 'The server returned an invalid JSON response',
                            'response_text': response.text[:500]
                        }, status=500)
                else:
                    return JsonResponse({
                        'error': 'Invalid response type',
                        'details': f'Expected JSON response but got {response.headers.get("content-type")}',
                        'response_text': response.text[:500]
                    }, status=500)

                if response.ok:
                    return JsonResponse({
                        'success': True,
                        'message': response_data.get('message', 'Application submitted successfully'),
                        'data': response_data.get('data', {})
                    })
                else:
                    return JsonResponse({
                        'error': response_data.get('error', 'Error submitting application'),
                        'details': response_data.get('details', 'Unknown error occurred')
                    }, status=response.status_code)

            except requests.exceptions.ConnectionError:
                return JsonResponse({
                    'error': 'Connection error',
                    'details': 'Could not connect to the application server. Please try again later.'
                }, status=503)
            except requests.exceptions.Timeout:
                return JsonResponse({
                    'error': 'Timeout error',
                    'details': 'The server took too long to respond. Please try again.'
                }, status=504)
            except requests.exceptions.RequestException as e:
                return JsonResponse({
                    'error': 'Request error',
                    'details': str(e)
                }, status=500)

        except Exception as e:
            import traceback
            return JsonResponse({
                'error': 'Server error',
                'details': str(e),
                'traceback': traceback.format_exc()
            }, status=500)

    return JsonResponse({
        'error': 'Invalid request',
        'details': 'This endpoint only accepts POST requests from job seekers'
    }, status=400)

@login_required
def delete_application(request, application_id):
    try:
        user_token = request.session.get('user_token')
        if not user_token:
            return JsonResponse({
                'error': 'Authentication required',
                'details': 'Please log in to delete applications'
            }, status=401)

        # Make API call to Flask backend
        response = requests.delete(
            f'http://localhost:5000/api/applications/{application_id}',
            headers={'Authorization': f'Bearer {user_token}'},
            timeout=10
        )

        if response.ok:
            return JsonResponse({
                'success': True,
                'message': 'Application deleted successfully'
            })
        else:
            error_data = response.json() if response.headers.get('content-type', '').lower().startswith('application/json') else {}
            return JsonResponse({
                'error': error_data.get('error', 'Failed to delete application'),
                'details': error_data.get('details', response.text[:500])
            }, status=response.status_code)

    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'error': 'Connection error',
            'details': 'Could not connect to the application server'
        }, status=503)
    except requests.exceptions.Timeout:
        return JsonResponse({
            'error': 'Timeout error',
            'details': 'The server took too long to respond'
        }, status=504)
    except Exception as e:
        return JsonResponse({
            'error': 'Server error',
            'details': str(e)
        }, status=500)

@login_required
def delete_job(request, job_id):
    try:
        # Get user token from session
        user_token = request.session.get('user_token')
        if not user_token:
            return JsonResponse({'error': 'Please log in to delete jobs'}, status=401)

        # Make API call to Flask backend
        response = requests.delete(
            f'http://localhost:5000/api/jobs/{job_id}',
            headers={
                'Authorization': f'Bearer {user_token}',
                'Content-Type': 'application/json'
            }
        )

        if response.status_code == 200:
            return JsonResponse({
                'success': True,
                'message': 'Job deleted successfully'
            })
        else:
            error_data = response.json() if response.headers.get('content-type', '').lower().startswith('application/json') else {}
            return JsonResponse({
                'error': error_data.get('error', 'Error deleting job'),
                'details': error_data.get('details', 'Unknown error occurred')
            }, status=response.status_code)

    except requests.exceptions.RequestException:
        return JsonResponse({'error': 'Error connecting to server'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def feedback(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you for your feedback!')
        return redirect('index')
    return render(request, 'feedback.html')

@login_required
def logout_view(request):
    request.session.flush()
    return redirect('index')

@login_required
def dashboard_home(request):
    return render(request, 'dashboard_home.html')

def uploads(request, filename):
    """Serve uploaded files from Flask server."""
    try:
        # Get the file from Flask server
        response = requests.get(
            f'http://localhost:5000/uploads/{filename}',
            stream=True,
            verify=False  # Only for development
        )
        
        print(f"File download response status: {response.status_code}")  # Debug
        print(f"File download response headers: {response.headers}")  # Debug
        
        if response.status_code == 200:
            # Create a FileResponse with the content
            file_response = FileResponse(
                response.raw,
                content_type=response.headers.get('content-type', 'application/octet-stream')
            )
            file_response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return file_response
        else:
            print(f"Error downloading file: {response.text}")  # Debug
            messages.error(request, 'File not found')
            return redirect('dashboard')
            
    except Exception as e:
        print(f"Error downloading file: {str(e)}")  # Debug
        messages.error(request, 'Error downloading file')
        return redirect('dashboard')

@login_required
def application_details(request, application_id):
    try:
        user_token = request.session.get('user_token')
        if not user_token:
            return JsonResponse({
                'error': 'Authentication required',
                'details': 'Please log in to view application details'
            }, status=401)

        # Get application details from Flask API
        response = requests.get(
            f'http://localhost:5000/api/applications/{application_id}',
            headers={'Authorization': f'Bearer {user_token}'},
            timeout=10
        )

        if not response.ok:
            error_data = response.json() if response.headers.get('content-type', '').lower().startswith('application/json') else {}
            return JsonResponse({
                'error': error_data.get('error', 'Failed to fetch application details'),
                'details': error_data.get('details', response.text[:500])
            }, status=response.status_code)

        try:
            application_data = response.json()
            return JsonResponse(application_data)
        except ValueError:
            return JsonResponse({
                'error': 'Invalid JSON response',
                'details': 'The server returned an invalid JSON response'
            }, status=500)

    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'error': 'Connection error',
            'details': 'Could not connect to the application server'
        }, status=503)
    except requests.exceptions.Timeout:
        return JsonResponse({
            'error': 'Timeout error',
            'details': 'The server took too long to respond'
        }, status=504)
    except Exception as e:
        return JsonResponse({
            'error': 'Server error',
            'details': str(e)
        }, status=500)

@login_required
def job_details(request, job_id):
    try:
        # Get job details from Flask API
        response = requests.get(f'http://localhost:5000/api/jobs/{job_id}')
        
        # Always return JSON response
        if not response.ok:
            return JsonResponse({
                'error': 'Failed to fetch job details',
                'details': response.text[:500],
                'status': response.status_code
            }, status=response.status_code)

        # Ensure response is JSON
        try:
            job_data = response.json()
            return JsonResponse(job_data)
        except ValueError:
            return JsonResponse({
                'error': 'Invalid JSON response from server',
                'details': response.text[:500]
            }, status=500)
            
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'error': 'Connection error',
            'details': str(e)
        }, status=503)
    except Exception as e:
        return JsonResponse({
            'error': 'Unexpected error',
            'details': str(e)
        }, status=500)

@login_required
def employer_application_details(request, application_id):
    try:
        user_token = request.session.get('user_token')
        user_type = request.session.get('user_type')
        
        if not user_token or user_type != 'employer':
            return JsonResponse({'error': 'Unauthorized access'}, status=403)
        
        # Make API call to Flask backend
        response = requests.get(
            f'http://localhost:5000/employer_application_details/{application_id}',
            headers={
                'Authorization': f'Bearer {user_token}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        if not response.ok:
            return JsonResponse({
                'error': 'Error fetching application details',
                'details': response.text
            }, status=response.status_code)
            
        return JsonResponse(response.json())
            
        return JsonResponse({
            'id': application.id,
            'job': {
                'id': application.job.id,
                'title': application.job.title,
                'company': application.job.company,
                'location': application.job.location,
                'description': application.job.description
            },
            'applicant': {
                'id': application.user.id,
                'email': application.user.email,
                'user_type': application.user.user_type
            },
            'resume': application.resume.url if application.resume else None,
            'cover_letter': application.cover_letter,
            'created_at': application.created_at.isoformat() if hasattr(application, 'created_at') else None
        })
    except Application.DoesNotExist:
        return JsonResponse({'error': 'Application not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def employer_dashboard(request):
    user_token = request.session.get('user_token')
    user_type = request.session.get('user_type')
    
    if not user_token:
        messages.error(request, 'Please log in to access the dashboard')
        return redirect('login')
        
    if user_type != 'employer':
        messages.error(request, 'Access denied. Employer account required.')
        return redirect('dashboard')
    
    try:
        # Get jobs posted by this employer
        headers = {
            'Authorization': f'Bearer {user_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        response = requests.get(
            'http://localhost:5000/api/jobs/employer',
            headers=headers,
            verify=False  # Only for development
        )
        
        print(f"API Response Status: {response.status_code}")  # Debug
        try:
            print(f"API Response Content: {response.content}")  # Debug
        except:
            pass
        
        if response.ok:
            try:
                jobs = response.json()
                print(f"Parsed jobs: {jobs}")  # Debug
                return render(request, 'employer_dashboard.html', {
                    'jobs': jobs,
                    'user_type': user_type
                })
            except ValueError as e:
                print(f"JSON parsing error: {str(e)}")  # Debug
                messages.error(request, 'Error parsing job data')
                jobs = []
        else:
            error_message = 'Error fetching jobs'
            try:
                error_data = response.json()
                error_message = error_data.get('error', error_message)
            except:
                pass
            messages.error(request, error_message)
            jobs = []
            
        return render(request, 'employer_dashboard.html', {
            'jobs': jobs,
            'user_type': user_type
        })
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")  # Debug
        messages.error(request, 'Error connecting to server')
        return render(request, 'employer_dashboard.html', {'jobs': [], 'user_type': user_type})
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug
        messages.error(request, f'Error: {str(e)}')
        return render(request, 'employer_dashboard.html', {'jobs': [], 'user_type': user_type})

@login_required
def download_resume(request, filename):
    """Download resume file from Flask server."""
    try:
        # Get the file from Flask server
        response = requests.get(
            f'http://localhost:5000/uploads/{filename}',
            stream=True,
            verify=False  # Only for development
        )
        
        print(f"Resume download response status: {response.status_code}")  # Debug
        print(f"Resume download response headers: {response.headers}")  # Debug
        
        if response.status_code == 200:
            # Create a FileResponse with the content
            file_response = FileResponse(
                response.raw,
                content_type=response.headers.get('content-type', 'application/octet-stream')
            )
            file_response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return file_response
        else:
            print(f"Error downloading resume: {response.text}")  # Debug
            messages.error(request, 'Resume file not found')
            return redirect('dashboard')
            
    except Exception as e:
        print(f"Error downloading resume: {str(e)}")  # Debug
        messages.error(request, 'Error downloading resume')
        return redirect('dashboard')
