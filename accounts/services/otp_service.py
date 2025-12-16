import pyotp
from django.utils import timezone

OTP_INTERVAL = 300  # 5 minutes

def generate_otp_for_user(user):
    if not user.otp_secret:
        user.otp_secret = pyotp.random_base32()
        user.save(update_fields=["otp_secret"])

    totp = pyotp.TOTP(user.otp_secret, interval=OTP_INTERVAL)
    return totp.now()


def verify_user_otp(user, otp):
    if not user.otp_secret:
        return False, "OTP not initialized"

    totp = pyotp.TOTP(user.otp_secret, interval=OTP_INTERVAL)

    if not totp.verify(otp, valid_window=1):
        return False, "Invalid or expired OTP"

    user.is_verified = True

    user.otp_secret = pyotp.random_base32()

    user.save(update_fields=["is_verified", "otp_secret"])

    return True, "Email verified successfully"

