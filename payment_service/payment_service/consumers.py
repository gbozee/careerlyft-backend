import asyncio
import functools

import requests

from channels.db import database_sync_to_async
from django.conf.urls import url

from .async_utils import JsonConsumer


class LongPollConsumer(JsonConsumer):
    # @database_sync_to_async
    def get_user(self):
        return {}
        # return User.objects.first()

    async def get(self, body):
        response = {'hello': 'world'}
        await self.json(response)

    async def post(self, body):
        await self.json(body)



urlpatterns = [
    url(r"^longpoll/$", LongPollConsumer),
]
