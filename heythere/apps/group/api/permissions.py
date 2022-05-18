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


class IsUserNotGroupLeader(permissions.BasePermission):
    message = "Permission denied. User is a group leader."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.user.is_group_leader:
            raise exceptions.PermissionDenied(detail=self.message)
        return True


class IsGroupRegisterAllowed(permissions.BasePermission):
    new_group_msg = "If you want to create new group, unregister the existing group."
    supported_urls = [
        "group-registration-step-1",
        "group-registration-step-2",
        "group-registration-step-3",
        "group-registration-step-4",
        "group-registration-step-confirm",
        "group-registration-unregister",
    ]

    def has_permission(self, request: Request, view: APIView):
        user = User.objects.get(id=request.user.id)
        joined_group = user.joined_group

        url_name = request.resolver_match.url_name

        if url_name not in self.supported_urls:
            raise exceptions.PermissionDenied(
                detail="Permission denied. Invalid url request."
            )

        # Permission check when step 1
        if url_name == self.supported_urls[0]:
            if joined_group:
                raise exceptions.PermissionDenied(
                    detail=f"Permission denied. User is under registration process of Group(id={joined_group.id})."
                    f" {self.new_group_msg}"
                )
            return True

        # Permission check rest of steps
        if not joined_group:
            if url_name == self.supported_urls[5]:
                raise exceptions.PermissionDenied(
                    detail="Permission denied. User is not registered to any group."
                )
            raise exceptions.PermissionDenied(
                detail="Permission denied. User should complete previous step first."
            )
        # Check if group_leader.
        if not user.is_group_leader:
            raise exceptions.PermissionDenied(
                detail="Permission denied. User is not a group leader."
            )

        step_2_cond = joined_group.register_step_1_completed
        step_3_cond = step_2_cond and joined_group.register_step_2_completed
        step_4_cond = step_3_cond and joined_group.register_step_3_completed
        step_confirm_cond = step_4_cond and joined_group.register_step_4_completed

        if url_name == self.supported_urls[1] and not step_2_cond:
            raise exceptions.PermissionDenied(
                detail="Permission denied. User should complete step1 first."
            )

        if url_name == self.supported_urls[2] and not step_3_cond:
            raise exceptions.PermissionDenied(
                detail="Permission denied. User should complete step2 first."
            )

        if url_name == self.supported_urls[3] and not step_4_cond:
            raise exceptions.PermissionDenied(
                detail="Permission denied. User should complete step3 first."
            )

        if url_name == self.supported_urls[4] and not step_confirm_cond:
            raise exceptions.PermissionDenied(
                detail="Permission denied. User should complete all 4 steps first."
            )
        return True
