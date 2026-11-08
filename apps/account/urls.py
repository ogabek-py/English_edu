from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    ProfileView, RegisterView, LogoutView, LoginView,
    login_page, register_page, forgot_password_page, reset_password_page,
    PasswordResetRequestView, PasswordResetConfirmView,
    TelegramWebhookView
)

urlpatterns = [
    path('login-page/', login_page, name='login_page'),
    path('register-page/', register_page, name='register_page'),
    path('forgot-password-page/', forgot_password_page, name='forgot_password_page'),
    path('reset-password-page/', reset_password_page, name='reset_password_page'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('login-api/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('telegram-webhook/', TelegramWebhookView.as_view(), name='telegram_webhook'),
]