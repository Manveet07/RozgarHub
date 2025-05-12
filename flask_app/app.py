from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import re
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Allow all origins during development
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization", "X-CSRFToken"],
        "supports_credentials": True
    },
    r"/uploads/*": {  # Add CORS for uploads endpoint
        "origins": "*",
        "methods": ["GET"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    applications = db.relationship('Application', backref='user', lazy=True)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    applications = db.relationship('Application', backref='job', lazy=True, cascade="all, delete-orphan")

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resume = db.Column(db.Text, nullable=False)
    cover_letter = db.Column(db.Text, nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rojgarhub')
def rojgarhub():
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        print(f"Error serving file {filename}: {str(e)}")  # Debug
        return jsonify({'error': 'File not found'}), 404

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            session['user_email'] = user.email
            session.permanent = True  # Make the session persistent
            
            # Redirect based on user type
            if user.user_type == 'jobseeker':
                return redirect(url_for('jobseeker_dashboard'))
            else:
                return redirect(url_for('employer_dashboard'))
        else:
            flash('Invalid email or password')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        
        # Password validation
        if len(password) < 8 or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            flash('Password must be at least 8 characters long and contain at least one special character.')
            return render_template('signup.html')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists')
        else:
            new_user = User(email=email, password=generate_password_hash(password), user_type=user_type)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully. Please log in.')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/jobseeker_dashboard')
def jobseeker_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    if not user or user.user_type != 'jobseeker':
        session.clear()
        return redirect(url_for('login'))
        
    jobs = Job.query.all()
    applications = Application.query.filter_by(user_id=user.id).all()
    return render_template('jobseeker_dashboard.html', jobs=jobs, applications=applications, current_user=user)

@app.route('/employer_dashboard')
def employer_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    if not user or user.user_type != 'employer':
        session.clear()
        return redirect(url_for('login'))
        
    # Get employer's jobs
    employer_jobs = Job.query.filter_by(employer_id=user.id).all()
    
    # Get applications for all employer's jobs
    job_ids = [job.id for job in employer_jobs]
    applications = Application.query.filter(Application.job_id.in_(job_ids)).all()
    
    # Add applications to each job
    for job in employer_jobs:
        job.applications = [app for app in applications if app.job_id == job.id]
    
    return render_template('employer_dashboard.html', jobs=employer_jobs, current_user=user)

@app.route('/post_job', methods=['POST'])
def post_job():
    if 'user_id' not in session:
        flash('Please log in to post a job')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title')
            company = request.form.get('company')
            description = request.form.get('description')
            location = request.form.get('location')
            
            # Validate required fields
            if not all([title, company, description, location]):
                flash('All fields are required')
                return redirect(url_for('employer_dashboard'))
            
            # Create new job
            new_job = Job(
                title=title,
                company=company,
                description=description,
                location=location,
                employer_id=session['user_id']  # Use the logged-in user's ID
            )
            
            db.session.add(new_job)
            db.session.commit()
            
            flash('Job posted successfully')
            return redirect(url_for('employer_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error posting job: {str(e)}')
            return redirect(url_for('employer_dashboard'))
            
    return redirect(url_for('employer_dashboard'))

@app.route('/apply_job/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    if request.method == 'POST':
        resume = request.files['resume']
        cover_letter = request.form['cover_letter']
        
        if 'UPLOAD_FOLDER' in app.config:
            resume_filename = secure_filename(resume.filename)
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
            resume.save(resume_path)
            
            new_application = Application(
                job_id=job_id,
                user_id=request.form['user_id'],
                resume=resume_filename,
                cover_letter=cover_letter
            )
            db.session.add(new_application)
            db.session.commit()
            return jsonify(success=True)
        else:
            flash('Error: Upload folder is not configured correctly.')
            return jsonify(success=False)
    return jsonify(success=False)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        # Process the submitted feedback
        # You can save it to the database or send an email
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('index'))
    return render_template('feedback.html')

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/delete_job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Please log in to delete jobs'}), 401

        job = Job.query.get_or_404(job_id)
        
        # Check if user is the employer who posted the job
        if job.employer_id != session['user_id']:
            return jsonify({'error': 'Unauthorized to delete this job'}), 403

        # Delete all applications for this job first
        Application.query.filter_by(job_id=job_id).delete()
        
        # Delete the job
        db.session.delete(job)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Job deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/application_details/<int:application_id>', methods=['GET'])
def application_details(application_id):
    application = Application.query.get_or_404(application_id)
    return jsonify(
        job_title=application.job.title,
        company=application.job.company,
        location=application.job.location,
        description=application.job.description,
        resume=application.resume,
        cover_letter=application.cover_letter
    )

@app.route('/job_details/<int:job_id>', methods=['GET'])
def job_details(job_id):
    try:
        job = Job.query.get(job_id)
        if not job:
            return jsonify({
                'error': 'Job not found',
                'details': f'No job found with ID {job_id}'
            }), 404
            
        return jsonify({
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'description': job.description,
            'employer_id': job.employer_id,
            'created_at': job.created_at.isoformat() if hasattr(job, 'created_at') else None
        })
    except Exception as e:
        # Log the error server-side
        import traceback
        app.logger.error(f'Error fetching job details: {str(e)}\n{traceback.format_exc()}')
        
        return jsonify({
            'error': 'Server error',
            'details': 'An unexpected error occurred while fetching job details'
        }), 500

@app.route('/edit_application/<int:application_id>', methods=['POST'])
def edit_application(application_id):
    application = Application.query.get_or_404(application_id)
    if application.user_id != request.form['user_id']:
        return jsonify(success=False), 403

    cover_letter = request.form['cover_letter']
    resume = request.files.get('resume')

    if resume:
        resume_filename = secure_filename(resume.filename)
        resume.save(os.path.join(app.config['UPLOAD_FOLDER'], resume_filename))
        application.resume = resume_filename

    application.cover_letter = cover_letter
    db.session.commit()
    return jsonify(success=True)

@app.route('/delete_application/<int:application_id>', methods=['POST'])
def delete_application_view(application_id):
    """Regular web route for deleting applications"""
    application = Application.query.get_or_404(application_id)
    if application.user_id != request.form['user_id']:
        flash('Unauthorized')
        return redirect(url_for('dashboard'))

    db.session.delete(application)
    db.session.commit()
    flash('Application deleted successfully')
    return redirect(url_for('dashboard'))

@app.route('/employer_application_details/<int:application_id>', methods=['GET'])
def employer_application_details(application_id):
    # Get user token from request headers
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No authorization token provided'}), 401
            
    user_id = auth_header.split(' ')[1]
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'employer':
        return jsonify({'error': 'Unauthorized access'}), 403
        
    application = Application.query.get_or_404(application_id)
    job = Job.query.get_or_404(application.job_id)
    
    if job.employer_id != user.id:
        return jsonify({'error': 'Unauthorized to view this application'}), 403

    return jsonify(
        job_title=application.job.title,
        company=application.job.company,
        location=application.job.location,
        description=application.job.description,
        resume=application.resume,
        cover_letter=application.cover_letter,
        applicant_email=application.user.email
    )

# API Endpoints
@app.route('/api/jobs', methods=['GET', 'POST'])
def api_jobs():
    if request.method == 'GET':
        jobs = Job.query.all()
        return jsonify([{
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'description': job.description,
            'location': job.location,
            'employer_id': job.employer_id
        } for job in jobs])
    elif request.method == 'POST':
        try:
            # Verify authorization
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'No authorization token provided'}), 401
            
            user_token = auth_header.split(' ')[1]
            user = User.query.get(user_token)
            
            if not user or user.user_type != 'employer':
                return jsonify({'error': 'Unauthorized access'}), 403
            
            data = request.json
            if not all(key in data for key in ['title', 'company', 'description', 'location']):
                return jsonify({'error': 'Missing required fields'}), 400
                
            new_job = Job(
                title=data['title'],
                company=data['company'],
                description=data['description'],
                location=data['location'],
                employer_id=user.id
            )
            
            db.session.add(new_job)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Job posted successfully',
                'job_id': new_job.id
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Server error',
                'details': str(e)
            }), 500

@app.route('/api/jobs', methods=['POST'])
def create_job():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['title', 'company', 'description', 'location', 'employer_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Create new job
        new_job = Job(
            title=data['title'],
            company=data['company'],
            description=data['description'],
            location=data['location'],
            employer_id=data['employer_id']
        )
        
        db.session.add(new_job)
        db.session.commit()
        
        return jsonify({
            'id': new_job.id,
            'message': 'Job created successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    job = Job.query.get_or_404(job_id)
    return jsonify({
        'id': job.id,
        'title': job.title,
        'company': job.company,
        'description': job.description,
        'location': job.location,
        'employer_id': job.employer_id
    })

@app.route('/api/jobs/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    if request.method == 'PUT':
        job = Job.query.get_or_404(job_id)
        if job.employer_id != request.json['employer_id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        job.title = request.json.get('title', job.title)
        job.company = request.json.get('company', job.company)
        job.description = request.json.get('description', job.description)
        job.location = request.json.get('location', job.location)
        db.session.commit()
        return jsonify({'message': 'Job updated successfully'})
    return jsonify({'error': 'Invalid request method'}), 405

@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def api_delete_job(job_id):
    try:
        # Get user token from request headers
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authorization token provided'}), 401
            
        user_token = auth_header.split(' ')[1]
        user = User.query.get(user_token)
        
        if not user:
            return jsonify({'error': 'Invalid user token'}), 401

        job = Job.query.get_or_404(job_id)
        
        # Check if user is the employer who posted the job
        if job.employer_id != user.id:
            return jsonify({'error': 'Unauthorized to delete this job'}), 403

        # Delete all applications for this job first
        Application.query.filter_by(job_id=job_id).delete()
        
        # Delete the job
        db.session.delete(job)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Job deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications', methods=['GET'])
def get_applications():
    try:
        # Get user token from request headers
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authorization token provided'}), 401
            
        user_token = auth_header.split(' ')[1]
        user = User.query.get(user_token)
        
        if not user:
            return jsonify({'error': 'Invalid user token'}), 401
            
        if user.user_type == 'jobseeker':
            applications = Application.query.filter_by(user_id=user.id).all()
        else:
            # For employers, get applications for their jobs
            employer_jobs = Job.query.filter_by(employer_id=user.id).all()
            job_ids = [job.id for job in employer_jobs]
            applications = Application.query.filter(Application.job_id.in_(job_ids)).all()
        
        return jsonify([{
            'id': app.id,
            'job_id': app.job_id,
            'user_id': app.user_id,
            'resume': app.resume,
            'cover_letter': app.cover_letter,
            'job_title': app.job.title,
            'company': app.job.company
        } for app in applications])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications', methods=['POST'])
def create_application():
    try:
        # Get user token from request headers
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authorization token provided'}), 401
            
        user_token = auth_header.split(' ')[1]
        user = User.query.get(user_token)
        
        if not user:
            return jsonify({'error': 'Invalid user token'}), 401
            
        if user.user_type != 'jobseeker':
            return jsonify({'error': 'Only jobseekers can apply for jobs'}), 403

        # Get form data
        job_id = request.form.get('job_id')
        cover_letter = request.form.get('cover_letter')
        resume = request.files.get('resume')

        if not all([job_id, cover_letter, resume]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate resume file
        if not allowed_file(resume.filename):
            return jsonify({'error': 'Invalid file type. Allowed types are: pdf, doc, docx, png'}), 400

        # Validate job exists
        job = Job.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        # Save resume file
        resume_filename = secure_filename(resume.filename)
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
        resume.save(resume_path)

        # Create application
        new_application = Application(
            job_id=job_id,
            user_id=user.id,
            resume=resume_filename,
            cover_letter=cover_letter
        )
        
        db.session.add(new_application)
        db.session.commit()
        
        return jsonify({
            'id': new_application.id,
            'message': 'Application submitted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications/<int:application_id>', methods=['GET'])
def get_application(application_id):
    try:
        # Get user token from request headers
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authorization token provided'}), 401
            
        user_token = auth_header.split(' ')[1]
        user = User.query.filter_by(id=user_token).first()
        
        if not user:
            return jsonify({'error': 'Invalid user token'}), 401

        application = Application.query.get_or_404(application_id)
        
        # Check if user is either the applicant or the employer
        if application.user_id != user.id and application.job.employer_id != user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({
            'id': application.id,
            'job': {
                'id': application.job.id,
                'title': application.job.title,
                'company': application.job.company,
                'location': application.job.location,
                'description': application.job.description
            },
            'resume': application.resume,
            'cover_letter': application.cover_letter,
            'created_at': application.id  # Using ID as a timestamp proxy
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications/<int:application_id>', methods=['DELETE'])
def api_delete_application(application_id):
    try:
        # Get user token from request headers
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authorization token provided'}), 401
            
        user_token = auth_header.split(' ')[1]
        user = User.query.get(user_token)
        
        if not user:
            return jsonify({'error': 'Invalid user token'}), 401

        application = Application.query.get_or_404(application_id)
        
        # Check if user is the applicant
        if application.user_id != user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Delete the resume file if it exists
        if application.resume:
            try:
                resume_path = os.path.join(app.config['UPLOAD_FOLDER'], application.resume)
                if os.path.exists(resume_path):
                    os.remove(resume_path)
            except Exception as e:
                print(f"Error deleting resume file: {str(e)}")
        
        db.session.delete(application)
        db.session.commit()
        return jsonify({'message': 'Application deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    return jsonify({
        'id': request.json['user_id'],
        'email': User.query.get(request.json['user_id']).email,
        'user_type': User.query.get(request.json['user_id']).user_type
    })

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({
            'error': 'Invalid request format',
            'details': 'Request must be in JSON format'
        }), 400
        
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({
            'error': 'Missing credentials',
            'details': 'Email and password are required'
        }), 400
    
    try:
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            response_data = {
                'id': user.id,
                'email': user.email,
                'user_type': user.user_type,
                'message': 'Login successful'
            }
            return jsonify(response_data), 200
        else:
            return jsonify({
                'error': 'Invalid credentials',
                'details': 'Email or password is incorrect'
            }), 401
            
    except Exception as e:
        print(f"Login error: {str(e)}")  # For debugging
        return jsonify({
            'error': 'Server error',
            'details': str(e)
        }), 500

@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type')
    
    if not all([email, password, user_type]):
        return jsonify({'error': 'All fields are required'}), 400
        
    # Password validation
    if len(password) < 8 or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return jsonify({'error': 'Password must be at least 8 characters long and contain at least one special character'}), 400
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'Email already exists'}), 400
        
    new_user = User(email=email, password=generate_password_hash(password), user_type=user_type)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'Account created successfully'}), 200

@app.route('/api/jobs/employer', methods=['GET'])
def get_employer_jobs():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authentication token provided'}), 401
            
        user_id = auth_header.split(' ')[1]
        user = User.query.get(user_id)
        
        if not user or user.user_type != 'employer':
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Get employer's jobs
        employer_jobs = Job.query.filter_by(employer_id=user.id).all()
        
        # Get applications for all employer's jobs
        job_ids = [job.id for job in employer_jobs]
        applications = Application.query.filter(Application.job_id.in_(job_ids)).all()
        
        # Format jobs with their applications
        jobs_data = []
        for job in employer_jobs:
            job_applications = [
                {
                    'id': app.id,
                    'user_email': app.user.email,
                    'resume': app.resume,
                    'cover_letter': app.cover_letter
                }
                for app in applications if app.job_id == job.id
            ]
            
            jobs_data.append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'description': job.description,
                'location': job.location,
                'applications': job_applications
            })
        
        return jsonify(jobs_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add a catch-all dashboard route that redirects to the appropriate dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
        
    if user.user_type == 'jobseeker':
        return redirect(url_for('jobseeker_dashboard'))
    else:
        return redirect(url_for('employer_dashboard'))

# Add this near your other routes
@app.route('/setup/add-sample-jobs')
def add_sample_jobs():
    try:
        # Create sample jobs
        jobs = [
            Job(
                title='Full Stack Developer',
                company='Microsoft',
                description='Seeking a Full Stack Developer with 3+ years of experience in Python/Django and React. Must have strong understanding of web technologies and database design.',
                location='Bangalore, India',
                employer_id=2
            ),
            Job(
                title='Data Scientist',
                company='Google',
                description='Looking for an experienced Data Scientist with strong background in machine learning, statistical analysis, and big data technologies. PhD in related field preferred.',
                location='Hyderabad, India',
                employer_id=2
            ),
            Job(
                title='UX Designer',
                company='Amazon',
                description='Creative UX Designer needed with 3+ years experience in user interface design, wireframing, and prototyping. Experience with Figma and Adobe Creative Suite required.',
                location='Mumbai, India',
                employer_id=2
            ),
            Job(
                title='DevOps Engineer',
                company='Netflix',
                description='DevOps Engineer with expertise in AWS, Docker, Kubernetes, and CI/CD pipelines. Must have experience with microservices architecture.',
                location='Delhi, India',
                employer_id=2
            ),
            Job(
                title='Mobile App Developer',
                company='Apple',
                description='iOS Developer with strong knowledge of Swift and UIKit. Experience with SwiftUI and Core Data is a plus.',
                location='Pune, India',
                employer_id=2
            )
        ]

        # Add all jobs to the database
        for job in jobs:
            db.session.add(job)

        # Commit the changes
        db.session.commit()

        return jsonify({
            'message': 'Sample jobs added successfully!',
            'count': len(jobs)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to add sample jobs',
            'details': str(e)
        }), 500

# End of routes

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)