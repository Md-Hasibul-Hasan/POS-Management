from rest_framework.permissions import BasePermission, SAFE_METHODS


def _is_admin(user):
    """Check if user is a superuser/admin"""
    return user.is_superuser or user.role == 'admin'


def _is_employee(user):
    """Check if user is any type of employee"""
    return user.role in ('owner', 'manager', 'salesman')


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
            and (_is_employee(request.user) or _is_admin(request.user))
        )


class IsEmployeeOrReadOnly(BasePermission):
    """
    Allow read access to any authenticated user, but write/create/delete
    operations only for employees (owner, manager, salesman) or admin.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return (
            request.user
            and request.user.is_authenticated
            and (_is_employee(request.user) or _is_admin(request.user))
        )


class IsPublicReadEmployeeWrite(BasePermission):
    """
    Allow read access to ANY user (even unauthenticated/public),
    but write/create/delete operations only for employees or admin.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True  # Anyone can read
        return (
            request.user
            and request.user.is_authenticated
            and (_is_employee(request.user) or _is_admin(request.user))
        )


class IsOwnerOrManagerOrReadOnly(BasePermission):
    """
    Allow read access to any authenticated user, but write/create/delete
    operations only for owners, managers, or admin.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role in ('owner', 'manager') or _is_admin(request.user))
        )


class IsPublicReadOwnerManagerWrite(BasePermission):
    """
    Allow read access to ANY user (even unauthenticated/public),
    but write/create/delete only for owners, managers, or admin.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True  # Anyone can read
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role in ('owner', 'manager') or _is_admin(request.user))
        )


class IsOwnerOrReadOnly(BasePermission):
    """
    Allow read access to any authenticated user, but write/create/delete
    operations only for owners or admin.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role == 'owner' or _is_admin(request.user))
        )