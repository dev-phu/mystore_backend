from rest_framework import permissions


class IsSeller(permissions.BasePermission):
    """
    Allows access only to seller users.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "SELLER"
        )


class IsBuyer(permissions.BasePermission):
    """
    Allows access only to buyer users.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "BUYER"
        )
