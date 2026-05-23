from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from config import Config
from models import db, User
import os

# ─────────────────────────────────────────────
# Fix PostgreSQL URL for Render
# ─────────────────────────────────────────────
db_url = os.environ.get('DATABASE_URL', '')

if db_url.startswith('postgres://'):
    os.environ['DATABASE_URL'] = db_url.replace(
        'postgres://',
        'postgresql://',
        1
    )

mail = Mail()

# ─────────────────────────────────────────────
# Create Flask App
# ─────────────────────────────────────────────
def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    # Ensure uploads folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)

    # ─────────────────────────────────────────
    # Login Manager
    # ─────────────────────────────────────────
    login_manager = LoginManager()
    login_manager.init_app(app)

    login_manager.login_view = 'login'
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ─────────────────────────────────────────
    # AUTH ROUTES
    # ─────────────────────────────────────────

    @app.route('/register', methods=['GET', 'POST'])
    def register():

        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':

            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            state = request.form.get('state', '').strip()

            password = request.form.get('password', '')
            confirm = request.form.get('confirm_password', '')

            # Validation
            if not all([name, email, password, confirm]):
                flash('All fields are required.', 'danger')
                return render_template('register.html')

            if password != confirm:
                flash('Passwords do not match.', 'danger')
                return render_template('register.html')

            if len(password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return render_template('register.html')

            # Check existing user
            existing_user = User.query.filter_by(email=email).first()

            if existing_user:
                flash('Email already registered.', 'danger')
                return render_template('register.html')

            # Create user
            user = User(
                name=name,
                email=email,
                phone=phone,
                state=state
            )

            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash('Registration successful! Please login.', 'success')

            return redirect(url_for('login'))

        return render_template('register.html')

    # ─────────────────────────────────────────
    # LOGIN
    # ─────────────────────────────────────────

    @app.route('/login', methods=['GET', 'POST'])
    def login():

        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':

            email = request.form.get('email', '').strip().lower()
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

    # ─────────────────────────────────────────
    # LOGOUT
    # ─────────────────────────────────────────

    @app.route('/logout')
    @login_required
    def logout():

        logout_user()

        flash('You have been logged out.', 'info')

        return redirect(url_for('login'))

    # ─────────────────────────────────────────
    # FORGOT PASSWORD
    # ─────────────────────────────────────────

    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():

        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':

            email = request.form.get('email', '').strip().lower()

            user = User.query.filter_by(email=email).first()

            if user:

                token = user.generate_reset_token()

                db.session.commit()

                reset_url = url_for(
                    'reset_password',
                    token=token,
                    _external=True
                )

                try:

                    msg = Message(
                        subject='Kisaan Sahyog — Password Reset',
                        recipients=[email]
                    )

                    msg.html = f"""
                    <h2>Password Reset</h2>
                    <p>Hello {user.name},</p>

                    <p>
                    Click the button below to reset your password.
                    This link is valid for 1 hour.
                    </p>

                    <a href="{reset_url}">
                        Reset Password
                    </a>
                    """

                    mail.send(msg)

                    flash(
                        'Password reset link sent to your email!',
                        'success'
                    )

                except Exception as e:
                    print("MAIL ERROR:", e)

                    flash(
                        'Could not send email. Check mail settings.',
                        'danger'
                    )

            else:
                flash(
                    'If this email is registered, a reset link has been sent.',
                    'info'
                )

            return redirect(url_for('forgot_password'))

        return render_template('forgot_password.html')

    # ─────────────────────────────────────────
    # RESET PASSWORD
    # ─────────────────────────────────────────

    @app.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_password(token):

        if current_user.is_authenticated:
            return redirect(url_for('index'))

        user = User.query.filter_by(reset_token=token).first()

        if not user or not user.is_reset_token_valid(token):

            flash(
                'Invalid or expired reset link.',
                'danger'
            )

            return redirect(url_for('forgot_password'))

        if request.method == 'POST':

            password = request.form.get('password', '')
            confirm = request.form.get('confirm_password', '')

            if len(password) < 6:
                flash(
                    'Password must be at least 6 characters.',
                    'danger'
                )

                return render_template(
                    'reset_password.html',
                    token=token
                )

            if password != confirm:

                flash('Passwords do not match.', 'danger')

                return render_template(
                    'reset_password.html',
                    token=token
                )

            user.set_password(password)

            user.clear_reset_token()

            db.session.commit()

            flash(
                'Password reset successful! Please login.',
                'success'
            )

            return redirect(url_for('login'))

        return render_template(
            'reset_password.html',
            token=token
        )

    # ─────────────────────────────────────────
    # LANGUAGE TOGGLE
    # ─────────────────────────────────────────

    @app.route('/set_language/<lang>')
    def set_language(lang):

        if lang in ['en', 'hi']:
            session['lang'] = lang

        return redirect(request.referrer or url_for('index'))

    # ─────────────────────────────────────────
    # MAIN ROUTES
    # ─────────────────────────────────────────

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

    # ─────────────────────────────────────────
    # API ROUTES
    # ─────────────────────────────────────────

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

    # ─────────────────────────────────────────
    # ERROR HANDLERS
    # ─────────────────────────────────────────

    @app.errorhandler(500)
    def internal_error(error):
        return f"<h1>500 Error</h1><p>{str(error)}</p>", 500

    @app.errorhandler(404)
    def not_found(error):
        return redirect(url_for('index'))

    return app

# ─────────────────────────────────────────────
# Create App
# ─────────────────────────────────────────────
app = create_app()

# ─────────────────────────────────────────────
# Run App
# ─────────────────────────────────────────────
if __name__ == '__main__':

    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully.")

    app.run(
        debug=False,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )