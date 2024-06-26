from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import create_access_token, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash
from app.model.model import db, User
from app.main.validators.validators import Validators
from app.utils.send_mail import send_reset_password_email
from app.utils.login_mail import send_login_notification_email
from app.utils.error_response import error_response
from app.utils.success_response import success_response
from app.utils.otp import send_otp_sms
from app.utils.pagination import pagination
import base64
import random

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    validation_result = Validators.check_user_required_fields(data)
    if validation_result["status"] == 200:
        user = User.query.filter_by(username=data.get('username'), email=data.get('email'), phone_number=data.get('phone_number')).first()

        if user:
            return error_response(400,"User already registered")

        hashed_password = generate_password_hash(data.get('password'))

        new_user = User(
            username=data.get('username'),
            email=data.get('email'),
            password=hashed_password,
            phone_number=data.get('phone_number'),
            profile_picture=data.get('profile_picture')
        )

        db.session.add(new_user)
        db.session.commit()
        
        return success_response(201, 'success', "User registered successfully")
    else:
        return jsonify(validation_result), validation_result["status"]

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()

    if not user:
        return error_response(401, 'Invalid username or password')

    if user.is_active == False:
        return error_response(401, 'Account not active, please activate your account')

    if not check_password_hash(user.password, password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        db.session.commit()

        if user.failed_login_attempts <= 2:
            db.session.commit()
            return error_response(401, 'Invalid username or password')
                    
        if user.failed_login_attempts == 3:
            db.session.commit()
            return error_response(401, "You have one attempt left.")
        
        
        if user.failed_login_attempts >= 4:
            if user.notification_sent == False:
                reset_token = base64.b64encode(user.email.encode('utf-8')).decode('utf-8')
                link = current_app.config['DEACTIVATE_ACC']
                reset_link = f'{link}{reset_token}'
                user.notification_sent = 1
                db.session.commit()
                send_login_notification_email(user.email, reset_link)
            return error_response(401, '!!!Warnning!!!, mail sent to users account')
        else:
            user.failed_login_attempts = 0
            user.notification_sent = 0 
            db.session.commit()
                    
    access_token = create_access_token(identity=user.id)

    return jsonify(access_token=access_token), 200
    

@auth_bp.route('/deactivate_account/<token>', methods=['GET'])
def deactivate_account(token):
    email = base64.b64decode(token).decode('utf-8')
    user = User.query.filter_by(email=email).first()

    if user:
        user.is_active = False
        db.session.commit()

        return success_response(200, 'success', 'Account deactivated successfully')
    else:
        return error_response(404, 'User not found')
    

@auth_bp.route('/activate_account', methods=['POST'])
def activate_account():
    data = request.json
    phone_number = data.get('phone_number')
    otp_entered = data.get('activation_otp')

    user = User.query.filter_by(phone_number=phone_number).first()

    if user:
        if user.notification_sent == 1:
            if user.activation_otp == otp_entered:
                user.is_active = True
                user.notification_sent = 0
                db.session.commit()
                return success_response(200, 'success', 'Account activated successfully')
            else:
                return error_response(401, 'Invalid OTP. Please try again.')
        else:
            return error_response(401, 'Please request OTP first.')
    else:
        return error_response(404, 'User not found')

@auth_bp.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.json
    phone_number = data.get('phone_number')

    user = User.query.filter_by(phone_number=phone_number).first()

    if user:
        otp = ''.join(random.choices('0123456789', k=6))
        send_otp_sms(phone_number, otp)
        user.activation_otp = otp
        db.session.commit()
        return success_response(200, 'success', 'OTP sent for account activation')
    else:
        return error_response(404, 'User not found')

@auth_bp.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data['email']
    user = User.query.filter_by(email=email).first()

    if user:
        reset_token = base64.b64encode(email.encode('utf-8')).decode('utf-8')
        link = current_app.config['CHANGE_PASS']
        reset_link = f'{link}{reset_token}'
        send_reset_password_email(email, reset_link)
        user.is_password_changed = False
        db.session.commit()

        return success_response(201, 'success', 'Reset password link sent to your email')
    else:
        return error_response(404, 'User not found')

@auth_bp.route('/reset_password/<token>', methods=['POST'])
def reset_password(token):
    data = request.get_json()
    new_password = data['new_password']
    confirm_password = data['confirm_password']

    if new_password != confirm_password:
        return error_response(400, 'New password and confirm password do not match')

    email = base64.b64decode(token).decode('utf-8')
    user = User.query.filter_by(email=email).first()

    if not user:
        return error_response(404, 'User not found')

    if not user.is_password_changed:
        return error_response(400, "Link expired or used. Please wait for some time to generate a new link")

    user.password = generate_password_hash(new_password)
    user.is_password_changed = True
    db.session.commit()

    return success_response(200, 'success','Password reset successfully')


@auth_bp.route('/get_users/', methods=['GET'])
def get_users():
    users = User.query.all()
    data = [{"username": user.username, "email": user.email, "profile_picture": user.profile_picture, "phone_number": user.phone_number} for user in users]
    paginated_data = pagination(data, 10, 1)
    return paginated_data
