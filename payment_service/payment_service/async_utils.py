import json
import urllib.parse

from django.template import loader
import channels.layers
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.http import AsyncHttpConsumer

channel_layer = channels.layers.get_channel_layer()


def process_thumbnails():
    async_to_sync(channel_layer.send)('thumbnails-generate', {
        'type': 'sync_call',
    })


def test_async_call():
    async_to_sync(channel_layer.send)('api-calls', {'type': 'make_call'})


def transform_headers(headers):
    return [(x.encode('utf-8'), y.encode('utf-8')) for x, y in headers.items()]


class BaseConsumer(AsyncHttpConsumer):
    def get_query_params(self):
        return dict(
            urllib.parse.parse_qsl(self.scope['query_string'].decode()))

    async def get(self, *args, **kwargs):
        pass


class JsonConsumer(AsyncHttpConsumer):
    # @dec_check
    async def handle(self, body):
        if self.scope['method'] == 'GET':
            await self.json_get(body)
        else:
            await self.json_post(body)

    async def json_get(self, body):
        query_string = self.scope.get('query_string') or b''
        params = dict(
            urllib.parse.parse_qsl(query_string.decode()))
        await self.get(params)

    async def json_post(self, body):
        data = json.loads(body.decode())
        await self.post(data)

    async def json(self, data, status=200, **kwargs):
        response_headers = {'Content-Type': 'application/json'}
        headers = kwargs.get('headers')
        if headers:
            response_headers.update(headers)
        result = json.dumps(data).encode('utf-8')
        await self.send_response(
            status, result, headers=transform_headers(response_headers))


class TemplateConsumer(AsyncHttpConsumer):
    async def handle(self, body):
        params = params = dict(
            urllib.parse.parse_qsl(self.scope['query_string'].decode()))
        context = self.get_context_data(query_params=params)
        await self.render_to_response(context)

    @sync_to_async
    def return_content(self, context):
        return loader.render_to_string(
            self.template_name, context, None, using=None)

    def get_context_data(self, **kwargs):
        context = kwargs
        return context

    async def render_to_response(self, context):
        response_headers = {'Content-Type': 'text/html'}
        data = await self.return_content(context)
        await self.send_response(
            200,
            data.encode('utf-8'),
            headers=transform_headers(response_headers))
