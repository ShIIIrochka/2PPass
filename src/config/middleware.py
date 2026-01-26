import logging
from django.middleware.csrf import CsrfViewMiddleware

logger = logging.getLogger(__name__)


class DisableCSRFForAPI(CsrfViewMiddleware):
    def _reject(self, request, reason):
        if request.path.startswith('/api/users/login/'):
            logger.info(f"CSRF rejection prevented for path: {request.path}, reason: {reason}")
            return None
        return super()._reject(request, reason)
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if request.path.startswith('/api/users/login/'):
            logger.info(f"Disabling CSRF in process_view for path: {request.path}")
            setattr(request, '_dont_enforce_csrf_checks', True)
        return super().process_view(request, callback, callback_args, callback_kwargs)
