from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # Storing plaintext passwords
    role = db.Column(db.String(10), nullable=False)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    photo_filename = db.Column(db.String(120), nullable=True)

    user = db.relationship('User', backref='submissions')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username, password=password).first()  # No password hashing
    if user:
        login_user(user)
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    else:
        flash('Invalid credentials!')
        return redirect(url_for('home'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    return render_template('screen1.html')

@app.route('/user')
@login_required
def user_dashboard():
    if current_user.role != 'user':
        return redirect(url_for('home'))
    return render_template('screen2.html')

@app.route('/submit_data', methods=['POST'])
@login_required
def submit_data():
    descriptions = []
    for i in range(5):
        description = request.form.get(f'description{i}')
        if description:
            descriptions.append(description)

    if not descriptions:
        flash('At least one description is required.')
        return redirect(url_for('user_dashboard'))

    submission = Submission(user_id=current_user.id, description=', '.join(descriptions))
    db.session.add(submission)

    photo = request.files.get('photo')
    if photo:
        upload_folder = 'uploads'
        os.makedirs(upload_folder, exist_ok=True)
        filename = f"{current_user.username}_photo.jpg"
        photo.save(os.path.join(upload_folder, filename))
        submission.photo_filename = filename
    else:
        submission.photo_filename = None

    db.session.commit()
    flash('Data submitted successfully!')
    return redirect(url_for('user_dashboard'))

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/admin/review')
@login_required
def admin_review():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    submissions = Submission.query.order_by(Submission.id.desc()).all()  # Get all submissions
    return render_template('admin_review.html', submissions=submissions)

@app.route('/evaluate_submission/<int:submission_id>', methods=['POST'])
@login_required
def evaluate_submission(submission_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    submission = Submission.query.get_or_404(submission_id)

    action = request.form.get('action')
    if action == 'accept':
        flash(f'Submission {submission_id} accepted!')
    elif action == 'reject':
        flash(f'Submission {submission_id} rejected!')

    return redirect(url_for('admin_review'))

@app.route('/clear_submissions', methods=['POST'])
@login_required
def clear_submissions():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    Submission.query.delete()  # Clear all submissions
    db.session.commit()
    flash('All submissions cleared successfully!')
    return redirect(url_for('admin_review'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
        if not User.query.first():
            admin = User(username='admin', password='admin1234', role='admin')
            user = User(username='user1as', password='user123', role='user')
            db.session.add(admin)
            db.session.add(user)
            db.session.commit()

    app.run(debug=True)
