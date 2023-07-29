from typing import List

import requests


class OneSignalClient:
    """
    Refer:
     - API: https://documentation.onesignal.com/reference/create-notification
     - Push Notification message: https://documentation.onesignal.com/reference/push-channel-properties
    """

    endpoint = "https://onesignal.com/api/v1/notifications"

    def __init__(self, app_id: str, rest_api_key: str, is_local: bool = False):
        self.app_id = app_id
        self.rest_api_key = rest_api_key
        self.is_local = is_local

    def send_notification_to_specific_users(
        self,
        title: str,
        content: str,
        user_ids: List[str],
        custom_data: dict or None = None,
    ) -> dict:
        if self.is_local:
            return self.local_response()

        headers = {
            "accept": "application/json",
            "Authorization": f"Basic {self.rest_api_key}",
            "content-type": "application/json",
        }
        payload = {
            "title": {"en": title, "ko": title},
            "contents": {"en": content, "ko": content},  # en: is required
            "include_external_user_ids": user_ids,
            "channel_for_external_user_ids": "push",
            "app_id": self.app_id,
            "custom_data": custom_data,
        }
        res = requests.post(self.endpoint, json=payload, headers=headers)
        return res.json()

    @staticmethod
    def local_response():
        return {
            "id": "local-onesignal-notification-id",
            "recipients": 1,
            "external_id": None,
        }
