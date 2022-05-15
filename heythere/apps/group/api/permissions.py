from django.contrib.auth import get_user_model
from rest_framework import exceptions, permissions
from rest_framework.request import Request
from rest_framework.views import APIView

User = get_user_model()


class IsUserActive(permissions.BasePermission):
    message = "Permission denied. User is not active."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user.is_active:
            raise exceptions.PermissionDenied(detail=self.message)
        return True


class IsUserGroupLeader(permissions.BasePermission):
    message = "Permission denied. User is not a group leader."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user.is_group_leader:
            raise exceptions.PermissionDenied(detail=self.message)
        return True


class IsUserNotGroupLeader(permissions.BasePermission):
    message = "Permission denied. User is a group leader."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.user.is_group_leader:
            raise exceptions.PermissionDenied(detail=self.message)
        return True


class IsGroupRegisterAllowed(permissions.BasePermission):
    new_group_msg = "If you want to create new group, unregister the existing group."

    def has_permission(self, request: Request, view: APIView):
        user = User.objects.get(id=request.user.id)
        joined_group = user.joined_group

        url_name = request.resolver_match.url_name

        # Permission check when step 1
        if url_name == "group-registration-step-1":
            if joined_group:
                raise exceptions.PermissionDenied(
                    detail=f"Permission denied. User is under registration process of Group(id={joined_group.id})."
                    f" {self.new_group_msg}"
                )
            return True

        # Permission check when step 2
        if url_name == "group-registration-step-2":
            if not joined_group:
                raise exceptions.PermissionDenied(
                    detail="Permission denied. User should complete previous step first."
                )
            step_1_comp = joined_group.register_step_1_completed
            if not step_1_comp:
                raise exceptions.PermissionDenied(
                    detail="Permission denied. User should complete previous step first."
                )
            # Check if group_leader.
            if not user.is_group_leader:
                raise exceptions.PermissionDenied(
                    detail="Permission denied. User is not a group_leader.)"
                )
            return True

        # Permission check when step 3
        if url_name == "group-registration-step-3":
            if not joined_group:
                raise exceptions.PermissionDenied(
                    detail="Permission denied. User should complete previous step first."
                )
            step_1_comp = joined_group.register_step_1_completed
            step_2_comp = joined_group.register_step_2_completed
            if not (step_1_comp and step_2_comp):
                raise exceptions.PermissionDenied(
                    detail="Permission denied. User should complete previous step first."
                )
            # Check if group_leader.
            if not user.is_group_leader:
                raise exceptions.PermissionDenied(
                    detail="Permission denied. User is not a group_leader.)"
                )
            return True

        raise exceptions.PermissionDenied(
            detail="Permission denied. Invalid url request.)"
        )
