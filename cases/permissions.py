# cases/permissions.py
from rest_framework.permissions import BasePermission

from cases.models import Case, CaseLawyer
from firms.models import Firm
from lawyers.models import Lawyer
from base.constants.user_roles import UserRoles

def is_case_owner_lawyer(user, case: Case) -> bool:
    if user.role != UserRoles.LAWYER:
        return False
    return case.owner_type == "lawyer" and case.owner_lawyer.user_id == user.id

def is_case_owner_firm_admin(user, case: Case) -> bool:
    if user.role != UserRoles.FIRM:
        return False
    return case.owner_type == "firm" and case.owner_firm.user_id == user.id

def is_assigned_lawyer(user, case: Case, require_edit: bool = False) -> bool:
    if user.role != UserRoles.LAWYER:
        return False

    try:
        assignment = CaseLawyer.objects.get(
            case=case,
            lawyer__user=user
        )
    except CaseLawyer.DoesNotExist:
        return False

    if require_edit:
        return assignment.can_edit

    return True

def is_case_client(user, case: Case) -> bool:
    return case.client_user_id == user.id

class CanViewCase(BasePermission):
    def has_object_permission(self, request, view, obj: Case):
        user = request.user

        if not user.is_authenticated:
            return False

        return any([
            is_case_owner_lawyer(user, obj),
            is_case_owner_firm_admin(user, obj),
            is_assigned_lawyer(user, obj),
            is_case_client(user, obj),
        ])

class CanEditCase(BasePermission):
    def has_object_permission(self, request, view, obj: Case):
        user = request.user

        if not user.is_authenticated:
            return False

        return any([
            is_case_owner_lawyer(user, obj),
            is_case_owner_firm_admin(user, obj),
            is_assigned_lawyer(user, obj, require_edit=True),
        ])


class CanAssignCaseLawyers(BasePermission):
    def has_object_permission(self, request, view, obj: Case):
        user = request.user

        if not user.is_authenticated:
            return False

        return is_case_owner_firm_admin(user, obj)

class CanUploadCaseDocument(BasePermission):
    def has_object_permission(self, request, view, obj: Case):
        user = request.user

        if not user.is_authenticated:
            return False

        return any([
            is_case_owner_lawyer(user, obj),
            is_case_owner_firm_admin(user, obj),
            is_assigned_lawyer(user, obj),
            is_case_client(user, obj),
        ])

class CanViewCaseDocuments(BasePermission):
    def has_object_permission(self, request, view, obj: Case):
        return CanViewCase().has_object_permission(request, view, obj)

class CanManageCaseDates(BasePermission):
    def has_object_permission(self, request, view, obj: Case):
        user = request.user

        if not user.is_authenticated:
            return False

        return any([
            is_case_owner_lawyer(user, obj),
            is_assigned_lawyer(user, obj),
        ])
