from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
import requests
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Account, PasswordResetCode
from .serializers import (
    AccountSerializer, RegisterSerializer, 
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from .utils import send_telegram_notification, create_site_notification

def index_page(request):
    return render(request, 'index.html')

def login_page(request):
    return render(request, 'login.html')

def register_page(request):
    return render(request, 'register.html')

def forgot_password_page(request):
    return render(request, 'forgot_password.html')

def reset_password_page(request):
    return render(request, 'reset_password.html')

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class RegisterView(generics.CreateAPIView):
    queryset = Account.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        user.is_active = False # Tasdiqlanmaguncha login qila olmaydi
        user.save()

        # Telegram notification
        message = (
            f"🔔 <b>Yangi foydalanuvchi!</b>\n\n"
            f"👤 Ism: {user.first_name} {user.last_name}\n"
            f"📧 Email: {user.email}\n"
            f"🆔 Username: @{user.username}\n"
            f"📅 Vaqt: {user.date_joined.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        send_telegram_notification(message)
        
        # Site notification
        create_site_notification(
            title="Yangi foydalanuvchi ro'yxatdan o'tdi",
            message=f"{user.username} ({user.email}) tizimga qo'shildi. Tasdiqlash kutilmoqda."
        )

class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'is_staff': user.is_staff
            })
        return Response({'detail': 'Username yoki parol xato.'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = Account.objects.get(email__iexact=email)
        except Account.DoesNotExist:
            return Response({"email": "Ushbu email bilan foydalanuvchi topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        
        code = PasswordResetCode.generate_code()
        PasswordResetCode.objects.create(user=user, code=code)
        
        # Email yuborish
        send_mail(
            'Parolni tiklash kodi',
            f'Sizning parolni tiklash kodingiz: {code}. Kod 10 daqiqa davomida amal qiladi.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        return Response({"detail": "Parolni tiklash kodi emailingizga yuborildi."}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        reset_code = serializer.validated_data['reset_code_obj']
        new_password = serializer.validated_data['new_password']
        
        user.set_password(new_password)
        user.save()
        
        reset_code.is_used = True
        reset_code.save()
        
        return Response({"detail": "Parol muvaffaqiyatli o'zgartirildi."}, status=status.HTTP_200_OK)

class TelegramWebhookView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Tugmalar olib tashlangan, webhook hozircha faqat OK qaytaradi
        return Response({"status": "ok"})
