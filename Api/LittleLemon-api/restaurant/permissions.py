from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit objects.
    Regular users can only read (GET, HEAD, OPTIONS).
    """
    def has_permission(self, request, view):
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions are only allowed to admin/staff users
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admin to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Admin users can do anything
        if request.user and request.user.is_staff:
            return True
        
        # Regular users can only access their own reservations
        return obj.user == request.user


class IsManager(permissions.BasePermission):
    """
    Custom permission to only allow managers.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.groups.filter(name='Manager').exists() or request.user.is_staff
        )


class IsDeliveryCrew(permissions.BasePermission):
    """
    Custom permission to only allow delivery crew members.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.groups.filter(name='Delivery crew').exists() or 
            request.user.groups.filter(name='Manager').exists() or 
            request.user.is_staff
        )


class IsCustomer(permissions.BasePermission):
    """
    Custom permission for customers (authenticated users who are not managers or delivery crew).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Customers are authenticated users who are not in special groups
        return not request.user.groups.filter(name__in=['Manager', 'Delivery crew']).exists() or request.user.is_staff
