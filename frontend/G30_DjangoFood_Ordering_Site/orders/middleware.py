from .api_services import APIService

class APISessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_service = APIService()

    def __call__(self, request):
        # Restore API session if it exists
        if 'api_session' in request.session:
            self.api_service.session.cookies.update(request.session['api_session'])
        
        response = self.get_response(request)
        
        # Update Django session with latest API session
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.session['api_session'] = self.api_service.session.cookies.get_dict()
        
        return response 