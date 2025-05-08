from django.shortcuts import redirect

class BuyerSupplierLoginRequiredMiddleware:
    """
    Middleware to protect buyer and supplier pages.
    If user is not logged in, they will be redirected to login page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Paths that need protection
        protected_paths = [
            '/buyer/',         # All buyer pages
            '/supplier/',      # All supplier pages
        ]

        # Check if the request path starts with any protected path
        if any(request.path.startswith(path) for path in protected_paths):
            if not request.session.get('user_type'):
                # If user_type not found in session, redirect to login
                return redirect('login')  # URL name of your login page

        response = self.get_response(request)
        return response
