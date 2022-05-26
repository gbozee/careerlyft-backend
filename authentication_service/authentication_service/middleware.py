from django.utils.timezone import now


class SetLastVisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        # response = self.get_response(request)
        # if request.user.is_authenticated():
        #     # Update last visit time after request finished processing.
        #     UserProfile.objects.filter(
        #         user_id=request.user.pk).update(last_login=now())
        # Code to be executed for each request/response after
        # the view is called.

        return response
