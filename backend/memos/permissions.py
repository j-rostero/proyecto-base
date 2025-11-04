from rest_framework import permissions


class IsSecondaryUser(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol SECONDARY_USER.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'SECONDARY_USER'
        )


class IsDirector(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol DIRECTOR.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'DIRECTOR'
        )


class IsRecipientOrInvolved(permissions.BasePermission):
    """
    Permiso que permite ver memos APPROVED donde el usuario es recipient o author.
    """
    def has_object_permission(self, request, view, obj):
        if obj.status != 'APPROVED':
            return False
        return (
            request.user in obj.recipients.all() or
            request.user == obj.author
        )


class CanEditDraft(permissions.BasePermission):
    """
    Permiso que permite editar solo memos en estado DRAFT y solo si es el autor.
    """
    def has_object_permission(self, request, view, obj):
        if obj.status != 'DRAFT':
            return False
        return request.user == obj.author

