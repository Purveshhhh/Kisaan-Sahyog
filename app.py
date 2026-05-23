from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from config import Config
from models import db, User
import os

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    mail.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── Auth Routes ────────────────────────────────

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        if request.method == 'POST':
            name     = request.form.get('name', '').strip()
            email    = request.form.get('email', '').strip().lower()
            phone    = request.form.get('phone', '').strip()
            state    = request.form.get('state', '').strip()
            password = request.form.get('password', '')
            confirm  = request.form.get('confirm_password', '')

            if not all([name, email, password, confirm]):
                flash('All fields are required.', 'danger')
                return render_template('register.html')
            if password != confirm:
                flash('Passwords do not match.', 'danger')
                return render_template('register.html')
            if len(password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return render_template('register.html')
            if User.query.filter_by(email=email).first():
                flash('Email already registered.', 'danger')
                return render_template('register.html')

            user = User(name=name, email=email, phone=phone, state=state)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        if request.method == 'POST':
            email    = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            remember = request.form.get('remember', False)

            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user, remember=bool(remember))
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(next_page or url_for('index'))
            else:
                flash('Invalid email or password.', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    # ── Forgot Password ────────────────────────────

    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            user  = User.query.filter_by(email=email).first()

            if user:
                token = user.generate_reset_token()
                db.session.commit()

                reset_url = url_for('reset_password', token=token, _external=True)

                try:
                    msg = Message(
                        subject='Kisaan Sahyog — Password Reset Request',
                        recipients=[email]
                    )
                    msg.html = f"""
                    <div style="font-family:Arial,sans-serif; max-width:500px; margin:0 auto;
                                background:#f9f9f9; border-radius:12px; overflow:hidden;">
                      <div style="background:linear-gradient(135deg,#1a4731,#2d6a4f);
                                  padding:24px; text-align:center;">
                        <h1 style="color:white; margin:0; font-size:1.5rem;">🌾 किसान सहयोग</h1>
                        <p style="color:#b7e4c7; margin:4px 0 0;">Kisaan Sahyog</p>
                      </div>
                      <div style="padding:32px;">
                        <h2 style="color:#1a4731;">Password Reset Request</h2>
                        <p style="color:#555; line-height:1.6;">
                          Hello <strong>{user.name}</strong>,<br><br>
                          We received a request to reset your password.
                          Click the button below to reset it.
                          This link is valid for <strong>1 hour</strong>.
                        </p>
                        <div style="text-align:center; margin:28px 0;">
                          <a href="{reset_url}"
                             style="background:linear-gradient(135deg,#2d6a4f,#1a4731);
                                    color:white; padding:14px 32px; border-radius:25px;
                                    text-decoration:none; font-weight:700; font-size:1rem;">
                            🔑 Reset My Password
                          </a>
                        </div>
                        <p style="color:#999; font-size:0.85rem;">
                          If you didn't request this, please ignore this email.
                          Your password will remain unchanged.
                        </p>
                      </div>
                      <div style="background:#f0f0f0; padding:16px; text-align:center;">
                        <p style="color:#999; font-size:0.8rem; margin:0;">
                          © 2024 Kisaan Sahyog — Built for Indian Farmers
                        </p>
                      </div>
                    </div>
                    """
                    mail.send(msg)
                    flash('Password reset link sent to your email! Check your inbox.', 'success')
                except Exception as e:
                    flash('Could not send email. Please check mail settings.', 'danger')
            else:
                # Don't reveal if email exists
                flash('If this email is registered, a reset link has been sent.', 'info')

            return redirect(url_for('forgot_password'))

        return render_template('forgot_password.html')

    @app.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        user = User.query.filter_by(reset_token=token).first()

        if not user or not user.is_reset_token_valid(token):
            flash('Invalid or expired reset link. Please request a new one.', 'danger')
            return redirect(url_for('forgot_password'))

        if request.method == 'POST':
            password = request.form.get('password', '')
            confirm  = request.form.get('confirm_password', '')

            if len(password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return render_template('reset_password.html', token=token)
            if password != confirm:
                flash('Passwords do not match.', 'danger')
                return render_template('reset_password.html', token=token)

            user.set_password(password)
            user.clear_reset_token()
            db.session.commit()
            flash('Password reset successful! Please login.', 'success')
            return redirect(url_for('login'))

        return render_template('reset_password.html', token=token)

    # ── Language Toggle ────────────────────────────

    @app.route('/set_language/<lang>')
    def set_language(lang):
        if lang in ['en', 'hi']:
            session['lang'] = lang
        return redirect(request.referrer or url_for('index'))

    # ── Main Pages ─────────────────────────────────

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/weather')
    @login_required
    def weather():
        return render_template('weather.html')

    @app.route('/disease')
    @login_required
    def disease():
        return render_template('disease.html')

    @app.route('/mandi')
    @login_required
    def mandi():
        return render_template('mandi.html')

    @app.route('/crop-suggest')
    @login_required
    def crop_suggest():
        return render_template('crop_suggest.html')

    # ── API Routes ─────────────────────────────────

    @app.route('/api/weather')
    @login_required
    def api_weather():
        from routes.weather_routes import get_weather
        return get_weather()

    @app.route('/api/disease', methods=['POST'])
    @login_required
    def api_disease():
        from routes.disease_routes import detect_disease
        return detect_disease()

    @app.route('/api/mandi')
    @login_required
    def api_mandi():
        from routes.mandi_routes import get_mandi_rates
        return get_mandi_rates()

    @app.route('/api/crop-suggest', methods=['POST'])
    @login_required
    def api_crop_suggest():
        from routes.crop_routes import suggest_crop
        return suggest_crop()
    
    @app.errorhandler(500)
    def internal_error(error):
        return f"<h1>500 Error</h1><p>{str(error)}</p>", 500

    @app.errorhandler(404)
    def not_found(error):
        return redirect(url_for('index'))
  
    return app
    

app = create_app()

# Fix PostgreSQL URL for Render
import re
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    os.environ['DATABASE_URL'] = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database tables created.")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)