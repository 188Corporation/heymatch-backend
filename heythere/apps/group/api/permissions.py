from django.contrib.auth import get_user_model
from rest_framework import exceptions, permissions
from rest_framework.request import Request
from rest_framework.views import APIView

User = get_user_model()


class IsUserActivePermission(permissions.BasePermission):
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


class GroupRegistrationPermission(permissions.BasePermission):
    new_group_msg = "If you want to create new group, unregister the existing group."

    def has_permission(self, request: Request, view: APIView):
        if request.method == "POST":
            user = User.objects.get(id=request.user.id)
            # If user joined no group, good to go.
            joined_group = user.joined_group
            if not user.joined_group:
                return True

            # Check if group_leader.
            # Note that only group_leader can perform registration.
            if not user.is_group_leader:
                raise exceptions.PermissionDenied(
                    detail=f"Permission denied. User already created/joined a Group(id={user.joined_group.id} "
                    f"but is not a group_leader.))"
                )

            # Only Step1 should be blocked because it create new object.
            url_name = request.resolver_match.url_name
            if joined_group.register_step_1_completed:
                if url_name == "group-registration-step-1":
                    raise exceptions.PermissionDenied(
                        detail=f"Permission denied. User is under registration process of Group(id={joined_group.id})."
                        f" {self.new_group_msg}"
                    )

            # check step status
            # joined_group = user.joined_group
            # url_name = request.resolver_match.url_name
            # if not joined_group.register_step_2_completed:
            #     if url_name == "group-registration-step-2":
            #         return True
            #     else:
            #         raise exceptions.PermissionDenied(
            #             detail=f"Permission denied. User already created Group(id={joined_group.id}) and should "
            #                    f"complete step 2 of registration. {self.new_group_msg}"
            #         )
            # if not joined_group.register_step_3_completed:
            #     if url_name == "group-registration-step-3":
            #         return True
            #     else:
            #         raise exceptions.PermissionDenied(
            #             detail=f"Permission denied. User already created Group(id={joined_group.id}) and should "
            #                    f"complete step 3 of registration. {self.new_group_msg}"
            #         )
            # if not joined_group.register_step_4_completed:
            #     if url_name == "group-registration-step-4":
            #         return True
            #     else:
            #         raise exceptions.PermissionDenied(
            #             detail=f"Permission denied. User already created Group(id={joined_group.id}) and should "
            #                    f"complete step 4 of registration. {self.new_group_msg}"
            #         )
            # if not joined_group.register_step_all_confirmed:
            #     if url_name == "group-registration-step-confirm":
            #         return True
            # raise exceptions.PermissionDenied(
            #     detail=f"Permission denied. User already created Group(id={joined_group.id} and completed "
            #            f"all registration steps. {self.new_group_msg})"
            # )

            return True
