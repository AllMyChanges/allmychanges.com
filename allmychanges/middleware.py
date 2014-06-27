class TurnOffCSRFProtectionIfOAuthenticated(object):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if request.user.is_authenticated() \
           and request.META.get('HTTP_AUTHORIZATION', '').startswith('Bearer'):
            setattr(request, 'csrf_processing_done', True)
