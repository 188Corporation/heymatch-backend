from rest_framework.exceptions import APIException


class BasePermissionDeniedException(APIException):
    default_code = "error"

    def __init__(self, detail=None, status_code=None):
        if detail:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code


class UserNotActiveException(BasePermissionDeniedException):
    status_code = 460
    detail = "비활성화 상태인 유저입니다 😰"


class UserNotJoinedGroupException(BasePermissionDeniedException):
    status_code = 461
    detail = "그룹을 먼저 생성하셔야 해요! 😎"


class UserJoinedGroupNotActiveException(BasePermissionDeniedException):
    status_code = 462
    detail = "조인한 그룹이 비활성화 상태에요.."


class UserGPSNotWithinHotplaceException(BasePermissionDeniedException):
    status_code = 463
    detail = "핫플 안에 있으셔야 해요! 😵"


class UserGroupLeaderException(BasePermissionDeniedException):
    status_code = 464
