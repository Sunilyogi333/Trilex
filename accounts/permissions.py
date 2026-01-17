from rest_framework.permissions import BasePermission
from accounts.constants import UserRoles


class HasRole(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )

class IsClientUser(HasRole):
    allowed_roles = [UserRoles.CLIENT]


class IsLawyerUser(HasRole):
    allowed_roles = [UserRoles.LAWYER]


class IsFirmAdminUser(HasRole):
    allowed_roles = [UserRoles.FIRM]


class IsAdminUser(HasRole):
    allowed_roles = [UserRoles.ADMIN]