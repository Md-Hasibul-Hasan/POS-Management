from rest_framework.permissions import BasePermission


def _is_admin(user):
    """Check if user is a superuser/admin"""
    return user.is_superuser or user.role == 'admin'


class IsOwner(BasePermission):
    """Only allow owners or admin to access the view"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role == 'owner' or _is_admin(request.user))
        )


class IsOwnerOrManager(BasePermission):
    """Allow owners, managers, and admin to access the view"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role in ('owner', 'manager') or _is_admin(request.user))
        )


class IsEmployee(BasePermission):
    """Allow any employee (owner, manager, salesman) or admin to access the view"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role in ('owner', 'manager', 'salesman') or _is_admin(request.user))
        )