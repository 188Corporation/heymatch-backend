from rest_framework.exceptions import APIException


class BasePermissionDeniedException(APIException):
    default_code = "error"

    def __init__(self, detail=None, status_code=None, extra_info=None):
        if detail:
            self.detail = detail
        if status_code:
            self.status_code = status_code
        if extra_info:
            self.detail = f"{self.detail} ({extra_info})"


class UserNotActiveException(BasePermissionDeniedException):
    status_code = 450
    detail = "비활성화 된 유저입니다 😰"


class UserAlreadyScheduledDeletionException(BasePermissionDeniedException):
    status_code = 451
    detail = "탈퇴가 진행중인 유저입니다 😰"


class UserDeletedException(BasePermissionDeniedException):
    status_code = 452
    detail = "회원 탈퇴한 유저입니다 😰"


class UserMainProfileImageNotFound(BasePermissionDeniedException):
    status_code = 453
    detail = "Should provide main profile image per user"


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


class UserPointBalanceNotEnoughException(BasePermissionDeniedException):
    status_code = 465
    detail = "젤리가 부족해요.. 충전해주세요! 🍬"


class JoinedGroupNotMineException(BasePermissionDeniedException):
    status_code = 466
    detail = "Not your joined group. Permission Denied."


class MatchRequestAlreadySubmittedException(BasePermissionDeniedException):
    status_code = 470
    detail = "이미 매칭요청을 보낸 그룹입니다!"


class MatchRequestNotFoundException(BasePermissionDeniedException):
    status_code = 471
    detail = "Requested MatchRequest not found."


class MatchRequestHandleFailedException(BasePermissionDeniedException):
    status_code = 472
    detail = "Cannot handle requested match request."


class MatchRequestGroupIsMineException(BasePermissionDeniedException):
    status_code = 473
    detail = "Cannot match with your own group."


class ReportMyGroupException(BasePermissionDeniedException):
    status_code = 474
    detail = "자기 자신을 신고할 수 없어요! 😵"


class ReceiptWrongEnvException(BasePermissionDeniedException):
    status_code = 480
    detail = (
        "Receipt received is for testing. " "Please send receipt to development server."
    )


class ReceiptNotPurchasedException(BasePermissionDeniedException):
    status_code = 481
    detail = "Receipt received is either PENDING or CANCELED. Please check or send a moment later"


class ReceiptItemNotFound(BasePermissionDeniedException):
    status_code = 484
    detail = "Product id in receipt not found in Item list."


class ReceiptProcessFailedException(BasePermissionDeniedException):
    status_code = 485
    detail = "Receipt validation failed."


class ReceiptInvalidPlatformRequestException(BasePermissionDeniedException):
    status_code = 486
    detail = "Payload `platform` is invalid. Please choose between ['ios', 'android']"


class ReceiptAlreadyProcessedException(BasePermissionDeniedException):
    status_code = 487
    detail = "Receipt is already processed."


class EmailVerificationCodeIncorrectException(BasePermissionDeniedException):
    status_code = 488
    detail = "Code is not correct or wrong email"


class EmailVerificationCodeExpiredException(BasePermissionDeniedException):
    status_code = 489
    detail = "Code is expired"


class EmailVerificationDomainNotFoundException(BasePermissionDeniedException):
    status_code = 490
    detail = "Could not find any school or company with your email. Please check."


class UserGroupLeaderException(BasePermissionDeniedException):
    status_code = 499
