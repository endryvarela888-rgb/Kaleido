from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def creator_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not request.user.is_creator:
            messages.info(request, 'Become a creator to access this page.')
            return redirect('users:settings')
        return view_func(request, *args, **kwargs)
    return wrapper