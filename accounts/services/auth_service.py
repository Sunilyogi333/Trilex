from django.contrib.auth import get_user_model, authenticate
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

from accounts.constants import UserRoles
from accounts.services.otp_service import generate_otp_for_user, verify_user_otp
from accounts.services.email_service import (
    send_signup_otp_email,
    send_verification_link_email,
    send_forgot_password_otp
)
from accounts.services.token_service import create_secure_token, decode_secure_token
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
FRONTEND_URL = settings.FRONTEND_URL


class AuthService:

    @staticmethod
    def signup(email, password, client_type):
        user = User.objects.create_user(
            email=email,
            password=password,
            role=UserRoles.CLIENT,
            is_verified=False,
        )
    
        if client_type == "mobile":
            otp = generate_otp_for_user(user)
            send_signup_otp_email(user.email, otp)
    
        else:
            token = create_secure_token({"email": user.email}, minutes=30)
            link = f"{FRONTEND_URL}/verify-email?token={token}"
            send_verification_link_email(user.email, link)
    
    @staticmethod
    def signup_mobile(email, password):
        if User.objects.filter(email=email).exists():
            return {"message": "User already exists"}, 400
    
        user = User.objects.create_user(
            email=email,
            password=password,
            role=UserRoles.GUEST,
            is_verified=False,
        )
    
        otp = generate_otp_for_user(user)
        send_signup_otp_email(user.email, otp)
    
        return {"message": "OTP sent to email"}, 201


    @staticmethod
    def signup_web(email, password):
        if User.objects.filter(email=email).exists():
            return {"message": "User already exists"}, 400
    
        user = User.objects.create_user(
            email=email,
            password=password,
            role=UserRoles.GUEST,
            is_verified=False,
        )
    
        token = create_secure_token({"email": user.email}, minutes=30)
        link = f"{FRONTEND_URL}/verify-email?token={token}"
    
        send_verification_link_email(user.email, link)
        return {"message": "Verification link sent"}, 201


    @staticmethod
    def verify_otp(email, otp):
        user = User.objects.get(email=email)
        return verify_user_otp(user, otp)

    @staticmethod
    def verify_link(token):
        data = decode_secure_token(token)
        user = User.objects.get(email=data["email"])
        user.is_verified = True
        user.save(update_fields=["is_verified"])
        return True, "Email verified successfully"

    @staticmethod
    def resend_otp(email):
        user = User.objects.get(email=email)
        otp = generate_otp_for_user(user)
        send_signup_otp_email(user.email, otp)
        return {"message": "OTP resent"}, 200

    @staticmethod
    def resend_verification_link(email):
        token = create_secure_token({"email": email}, minutes=30)
        link = f"{FRONTEND_URL}/verify-email?token={token}"
        send_verification_link_email(email, link)
        return {"message": "Verification link resent"}, 200

    @staticmethod
    def login(email, password):
        user = authenticate(username=email, password=password)

        if not user:
            return {"message": "Invalid credentials"}, 400

        if not user.is_verified:
            return {"message": "Email not verified"}, 403

        refresh = RefreshToken.for_user(user)

        return {
            "message": "Login successful",
            "role": user.role,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, 200


    @staticmethod
    def forgot_password(email):
        user = User.objects.filter(email=email).first()
        if not user:
            return {"error": "No user with this email."}, 404

        otp = generate_otp_for_user(user)
        send_forgot_password_otp(email, otp)

        return {"message": "OTP sent successfully"}, 200

    @staticmethod
    def verify_forgot_password_otp(email, otp):
        user = User.objects.filter(email=email).first()
        if not user:
            return {"error": "User not found"}, 404

        success, msg = verify_user_otp(user, otp)
        if not success:
            return {"error": msg}, 400

        token = create_secure_token(
            {
                "email": user.email,
                "type": "reset_password",
            },
            minutes=10,
        )

        return {
            "message": "OTP verified",
            "reset_token": token,
        }, 200

    @staticmethod
    def reset_password(token, new_password):
        payload = decode_secure_token(token)

        if payload.get("type") != "reset_password":
            raise AuthenticationFailed("Invalid token type")

        email = payload.get("email")
        user = User.objects.filter(email=email).first()

        if not user:
            return {"error": "User not found"}, 404

        user.set_password(new_password)
        user.otp_secret = None
        user.save(update_fields=["password", "otp_secret"])

        return {"message": "Password reset successfully"}, 200
