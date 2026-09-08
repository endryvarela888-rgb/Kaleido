from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import api_views

app_name = 'users_api'

urlpatterns = [
    path('signup/', api_views.SignupView.as_view(), name='signup'),
    path('me/', api_views.MeView.as_view(), name='me'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('creators/<int:pk>/', api_views.CreatorProfileView.as_view(), name='creator_profile'),
    path('me/become-creator/', api_views.BecomeCreatorView.as_view(), name='become_creator'),
    path('me/change-password/', api_views.ChangePasswordView.as_view(), name='change_password'),
    path('resend-activation/', api_views.ResendActivationView.as_view(), name='resend_activation'),
    path('activate/', api_views.ActivateAccountView.as_view(), name='activate'),
    path('password-reset/', api_views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/confirm/', api_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
