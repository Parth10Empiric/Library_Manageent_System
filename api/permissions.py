from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        
        return bool(request.user and request.user.is_staff)

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and not request.user.is_staff)
    
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)
    
class IsAdminOrStudentRequest(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if view.action == 'request_issue':
            return request.user and request.user.is_authenticated
        return bool(request.user and request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_staff and view.action != 'request_issue':
            return True
        if view.action == 'request_issue':
            return not request.user.is_staff
        return False
    
