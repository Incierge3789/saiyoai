class CleanHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.META.get('HTTP_HOST', '')
        if ',' in host:
            request.META['HTTP_HOST'] = host.split(',')[0].strip()
        response = self.get_response(request)
        return response
