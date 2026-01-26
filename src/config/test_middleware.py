class RequestLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if '/api/users/login/' in request.path:
            with open('/tmp/middleware_debug.log', 'a') as f:
                f.write("="*80 + "\n")
                f.write(f"Middleware called for: {request.path}\n")
                f.write(f"Method: {request.method}\n")
                f.write(f"csrf_checks: {getattr(request, '_dont_enforce_csrf_checks', 'not set')}\n")
        
        response = self.get_response(request)
        
        if '/api/users/login/' in request.path:
            with open('/tmp/middleware_debug.log', 'a') as f:
                f.write(f"Response status: {response.status_code}\n")
                f.write("="*80 + "\n")
        
        return response
