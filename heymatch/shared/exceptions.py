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
    detail = "비활성화 된 유저입니다 😰"


class UserNotJoinedGroupException(BasePermissionDeniedException):
    status_code = 461
    detail = "그룹을 먼저 만들어 주세요! 😎"


class UserJoinedGroupNotActiveException(BasePermissionDeniedException):
    status_code = 462
    detail = "비활성화 된 그룹이에요 😰"


class UserGPSNotWithinHotplaceException(BasePermissionDeniedException):
    status_code = 463
    detail = "핫플 안에 들어와 주세요! 😵"


class GroupNotWithinSameHotplaceException(BasePermissionDeniedException):
    status_code = 464
    detail = "상대 그룹과 같은 핫플에 있어야 해요! 😥"


class UserPointBalanceNotEnough(BasePermissionDeniedException):
    status_code = 465
    detail = "젤리가 부족해요.. 충전해주세요! 🍬"


class UserGroupLeaderException(BasePermissionDeniedException):
    status_code = 499
