# accounts/permissions.py

from rest_framework.permissions import BasePermission
from base.constants.user_roles import UserRoles
from base.constants.verification import VerificationStatus


# -------------------------------------------------
# BASE PERMISSIONS
# -------------------------------------------------

class IsAuthenticatedUser(BasePermission):
    """
    Ensures user is authenticated.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsEmailVerified(BasePermission):
    """
    Ensures user's email is verified.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_email_verified
        )


class HasRole(BasePermission):
    """
    Base role permission.
    """
    allowed_roles = []

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )


# -------------------------------------------------
# ROLE PERMISSIONS
# -------------------------------------------------

class IsClientUser(HasRole):
    allowed_roles = [UserRoles.CLIENT]


class IsLawyerUser(HasRole):
    allowed_roles = [UserRoles.LAWYER]


class IsFirmUser(HasRole):
    allowed_roles = [UserRoles.FIRM]


class IsAdminUser(HasRole):
    allowed_roles = [UserRoles.ADMIN]


# -------------------------------------------------
# VERIFICATION-BASED PERMISSIONS
# -------------------------------------------------

class IsClientVerified(BasePermission):
    """
    Client must have VERIFIED ID verification.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        verification = getattr(
            request.user,
            "client_verification",
            None
        )
        return (
            verification
            and verification.status == VerificationStatus.VERIFIED
        )


class IsLawyerVerified(BasePermission):
    """
    Lawyer must have VERIFIED bar verification.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        verification = getattr(
            request.user,
            "bar_verification",
            None
        )
        return (
            verification
            and verification.status == VerificationStatus.VERIFIED
        )


class IsFirmVerified(BasePermission):
    """
    Firm must have VERIFIED firm verification.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        verification = getattr(
            request.user,
            "firm_verification",
            None
        )
        return (
            verification
            and verification.status == VerificationStatus.VERIFIED
        )

class IsVerifiedLawyerOrFirm(BasePermission):
    """
    Allows access only to VERIFIED lawyers or VERIFIED firms.
    """
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.role == UserRoles.LAWYER:
            verification = getattr(user, "bar_verification", None)
        elif user.role == UserRoles.FIRM:
            verification = getattr(user, "firm_verification", None)
        else:
            return False

        return (
            verification
            and verification.status == VerificationStatus.VERIFIED
        )