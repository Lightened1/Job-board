from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import bcrypt
import os
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import random
import string
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import time


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.app_context().push()
migrate = Migrate(app, db)


class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    resume = db.Column(db.String(255), nullable=False)
    cover_letter = db.Column(db.Text, nullable=False)

    
    def __init__(self,job_id, name, email, phone, resume,cover_letter):
        self.job_id = job_id
        self.name = name
        self.email = email
        self.phone = phone
        self.resume = resume
        self.cover_letter = cover_letter


class Employer(db.Model):
    __tablename__ = 'employers'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    jobs = db.relationship('Job', backref='employer', lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password.decode('utf-8')


class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    employer_id = db.Column(db.Integer, db.ForeignKey('employers.id'), nullable=False)
    photo_url = db.Column(db.String(200))

    
    def __init__(self, title, description, photo_url, employer):
        self.title = title
        self.description = description
        self.photo_url = photo_url
        self.employer = employer

app.config['SECRET_KEY'] = 'AMIAMI'


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/jobs', methods=['GET'])
def jobs():
    query = request.args.get('query')
    if query:
        filtered_jobs = Job.query.filter(
            or_(
                Job.title.ilike(f'%{query}%'),
                Job.employer.has(Employer.username.ilike(f'%{query}%'))
            )
        ).all()
        return render_template('jobs.html', jobs=filtered_jobs, query=query)
    else:
        all_jobs = Job.query.all()
        return render_template('jobs.html', jobs=all_jobs, query=None)

@app.route('/employer')
def employer_dashboard():
    # Check if employer is logged in
    if 'employer_id' in session:
        employer_id = session['employer_id']
        # Fetch the employer's name from the database using the employer ID
        employer = db.session.get(Employer, employer_id)
        if employer:
            employer_name = employer.username
            # Render the employer dashboard template and pass the employer_name variable
            return render_template('Employers.html', employer_name=employer_name, employer_id=employer_id)
        else:
            # Handle case where employer is not found in the database
            return "Error: Employer not found"
    else:
        # Redirect to the login page if employer is not logged in
        return redirect('/login_employer')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create_job', methods=['GET', 'POST'])
def create_job():
    if 'employer_id' not in session:
        return redirect('/login_employer')

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        photo = request.files.get('photo')
        photo_url = request.form.get('photo_url')

        employer = Employer.query.get(session['employer_id'])

        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo_url = f"{request.host_url}{app.config['UPLOAD_FOLDER']}/{filename}"
        elif not photo_url:
            return render_template('create_job.html', error_message='Please provide a photo or photo URL')

        job = Job(title=title, description=description, photo_url=photo_url, employer=employer)
        db.session.add(job)
        db.session.commit()

        return redirect('/employer')

    return render_template('create_job.html')

@app.route('/dashboard')
def dashboard():
    if 'employer_id' not in session:
        return redirect('/login_employer')

    employer = Employer.query.get(session['employer_id'])
    jobs = employer.jobs

    return render_template('dashboard.html', employer=employer, jobs=jobs)


@app.route('/register_employer', methods=['GET', 'POST'])
def register_employer():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        employer = Employer(username=username, password=hashed_password)
        db.session.add(employer)
        db.session.commit()

        return redirect('/login_employer')

    return render_template('register_employer.html')

@app.route('/login_employer', methods=['GET', 'POST'])
def login_employer():
    if 'employer_id' in session:
        return redirect('/employer')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        employer = Employer.query.filter_by(username=username).first()

        
        if employer and bcrypt.checkpw(password.encode('utf-8'), employer.password.decode('utf-8').encode('utf-8')):
            session['employer_id'] = employer.id
            return redirect('/employer')
        else:
            flash('Invalid username or password', 'error')

    return render_template('login_employer.html')



@app.route('/apply')
def apply():
    job_id = request.args.get('job_id')
    job = Job.query.get(job_id)
    return render_template('apply.html', job=job)

@app.route('/submit_application', methods=['POST'])
def submit_application():
    # Get the form data
    job_id = request.form['job_id']
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    resume = request.files['resume']
    cover_letter = request.form['cover_letter']

    # Create the uploads directory if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Save the uploaded resume file
    filename = secure_filename(resume.filename)
    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    resume.save(resume_path)

    # Create a new application instance
    application = Application(job_id=job_id, name=name, email=email, phone=phone,
                              resume=resume_path, cover_letter=cover_letter)

    # Add the application to the database
    db.session.add(application)
    db.session.commit()

    # Render the success message
    return render_template('success.html')

@app.route('/applications')
def applications():
    if 'employer_id' not in session:
        return redirect('/login_employer')

    employer_id = session['employer_id']
    employer = Employer.query.get(employer_id)
    jobs = Job.query.filter_by(employer_id=employer_id).all()

    applications = Application.query.filter(Application.job_id.in_([job.id for job in jobs])).all()

    return render_template('applications.html', jobs=jobs, applications=applications)

@app.route('/logout')
def logout():
    session.pop('employer_id', None)
    return redirect('/')


if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'AMIAMI'
    app.run()