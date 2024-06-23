from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'abhi@123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'html', 'css', 'js'}

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Create database tables (run this once to create tables)
with app.app_context():
    db.create_all()

# Function to get list of files in user's upload directory
def get_uploaded_files(username):
    user_upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
    if os.path.exists(user_upload_folder):
        files = os.listdir(user_upload_folder)
        return files
    return []

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
        else:
            # Create new user
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            flash('Login successful.', 'success')
            return redirect(url_for('upload'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        # Check if the file extension is allowed
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)
            file.save(os.path.join(user_folder, filename))
            flash('File uploaded successfully', 'success')
            return redirect(url_for('uploaded_files'))
        else:
            flash('File type not allowed. Allowed file types are html, css, js.', 'danger')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/uploaded_files')
def uploaded_files():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    files = get_uploaded_files(session['username'])
    return render_template('uploaded_files.html', files=files)

@app.route('/uploads/<username>/<filename>')
def uploaded_file(username, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], username), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0' , debug=True)
