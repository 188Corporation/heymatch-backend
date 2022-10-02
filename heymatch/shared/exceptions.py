from rest_framework.exceptions import APIException


class BasePermissionDeniedException(APIException):
    default_code = "error"

    def __init__(self, detail, status_code=None):
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code


class UserNotActiveException(BasePermissionDeniedException):
    status_code = 460


class UserNotJoinedGroupException(BasePermissionDeniedException):
    status_code = 461


class UserJoinedGroupNotActiveException(BasePermissionDeniedException):
    status_code = 462


class UserGPSNotWithinHotplaceException(BasePermissionDeniedException):
    status_code = 463


class UserGroupLeaderException(BasePermissionDeniedException):
    status_code = 464
