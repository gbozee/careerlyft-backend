from channels.routing import ProtocolTypeRouter, ChannelNameRouter, URLRouter
from channels.http import AsgiHandler
from django.conf.urls import url
from . import consumers
application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    # "channel":
    # ChannelNameRouter({
    #     y.NAME: y
    #     for y in [
    #         consumers.GenerateConsumer, consumers.DeleteConsumer,
    #         consumers.RequestConsumer
    #     ]
    # }),
    "http":
    URLRouter(consumers.urlpatterns + [
        # url(r"^longpoll/$", consumers.LongPollConsumer),
        # url(r"^notifications/(?P<stream>\w+)/$", LongPollConsumer),
        url(r"", AsgiHandler),
    ])
})
