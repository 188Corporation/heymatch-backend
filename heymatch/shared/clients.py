from typing import List

import requests


class OneSignalClient:
    endpoint = "https://onesignal.com/api/v1/notifications"

    def __init__(self, app_id: str, rest_api_key: str):
        self.app_id = app_id
        self.rest_api_key = rest_api_key

    def send_notification(self, message: str, user_ids: List[str]) -> dict:
        headers = {
            "accept": "application/json",
            "Authorization": f"Basic {self.rest_api_key}",
            "content-type": "application/json",
        }
        payload = {
            "contents": {"en": "Welcome to HeyMatch!", "ko": message},
            "include_external_user_ids": user_ids,
            "channel_for_external_user_ids": "push",
            "app_id": self.app_id,
        }
        res = requests.post(self.endpoint, json=payload, headers=headers)
        return res.json()
