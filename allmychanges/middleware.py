import uuid

class TurnOffCSRFProtectionIfOAuthenticated(object):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if request.user.is_authenticated() \
           and request.META.get('HTTP_AUTHORIZATION', '').startswith('Bearer'):
            setattr(request, 'csrf_processing_done', True)


class LightUserMiddleware(object):
    """This view creates a request.light_user attribute on a request
    where light user is an uuid like 038dc495-7d9b-43e5-afa7-e3a0895cad55.
    This uuid value is stored in the cookie and could be used to stitch
    together actions user've done on landing page before he signed in.
    """
    def process_request(self, request):
        request.light_user = request.COOKIES.get('light_user_id')
        if request.light_user is None:
            request.light_user = uuid.uuid4()
            request.light_user_created = True

    def process_response(self, request, response):
        if getattr(request, 'light_user_created', False):
            light_user_id = getattr(request, 'light_user', None)
            if light_user_id:
                response.set_cookie('light_user_id', light_user_id)

        return response
