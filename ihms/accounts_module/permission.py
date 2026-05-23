from rest_framework.permissions import BasePermission
from .constants import UserRole


class IsPHM(BasePermission):
    message = 'Access denied. PHM credentials required or account pending verification.'
    
    def has_permission(self, request, view) -> bool:
        return bool( 
            request.user.is_authenticated and
            hasattr(request.user, 'phm_profile') and
            request.user.phm_profile.is_verified and
            request.session.get('active_role') == UserRole.PHM
        )


class IsParent(BasePermission):
    message = 'Access denied. Parent credentials required.'

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user.is_authenticated and
            hasattr(request.user, 'guardian_profile') and
            request.session.get('active_role') == UserRole.PARENT
        )


class IsMOH(BasePermission):
    message = 'Access denied. MOH Officer credentials required.'

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user.is_authenticated and
            hasattr(request.user, 'moh_profile') and
            request.session.get('active_role') == UserRole.MOH
        )