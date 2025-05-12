import requests
import json
from django.conf import settings

API_BASE_URL = 'http://localhost:5000/api'  # Flask API base URL

class JobPortalService:
    @staticmethod
    def get_jobs():
        response = requests.get(f'{API_BASE_URL}/jobs')
        return response.json() if response.ok else []

    @staticmethod
    def get_job_details(job_id):
        response = requests.get(f'{API_BASE_URL}/jobs/{job_id}')
        return response.json() if response.ok else None

    @staticmethod
    def get_job(job_id):
        response = requests.get(f'{API_BASE_URL}/jobs/{job_id}')
        return response.json() if response.ok else None

    @staticmethod
    def create_job(token, data):
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(f'{API_BASE_URL}/jobs', json=data, headers=headers)
        return response.json() if response.ok else None

    @staticmethod
    def update_job(token, job_id, data):
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.put(f'{API_BASE_URL}/jobs/{job_id}', json=data, headers=headers)
        return response.json() if response.ok else None

    @staticmethod
    def delete_job(token, job_id):
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.delete(f'{API_BASE_URL}/jobs/{job_id}', headers=headers)
        return response.ok

    @staticmethod
    def get_applications(token):
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f'{API_BASE_URL}/applications', headers=headers)
        return response.json() if response.ok else []

    @staticmethod
    def create_application(token, data, resume_file):
        headers = {'Authorization': f'Bearer {token}'}
        files = {'resume': resume_file}
        response = requests.post(f'{API_BASE_URL}/applications', data=data, files=files, headers=headers)
        return response.json() if response.ok else None

    @staticmethod
    def update_application(token, application_id, data, resume_file=None):
        headers = {'Authorization': f'Bearer {token}'}
        files = {'resume': resume_file} if resume_file else None
        response = requests.put(f'{API_BASE_URL}/applications/{application_id}', 
                              data=data, 
                              files=files, 
                              headers=headers)
        return response.json() if response.ok else None

    @staticmethod
    def delete_application(token, application_id):
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.delete(f'{API_BASE_URL}/applications/{application_id}', headers=headers)
        return response.ok

    @staticmethod
    def login(email, password):
        data = {'email': email, 'password': password}
        response = requests.post(f'{API_BASE_URL}/auth/login', json=data)
        return response.json() if response.ok else None

    @staticmethod
    def signup(email, password, user_type):
        data = {
            'email': email,
            'password': password,
            'user_type': user_type
        }
        response = requests.post(f'{API_BASE_URL}/auth/signup', json=data)
        return response.json() if response.ok else None