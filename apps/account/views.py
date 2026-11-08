from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
import requests
from rest_framework import generics, status, permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Account, PasswordResetCode, UserActivity, UserProgress, AuditLog
from .serializers import (
    AccountSerializer, RegisterSerializer, 
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    DashboardStatsSerializer, UserActivitySerializer, AuditLogSerializer
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

class AdminDashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        stats = {
            'total_users': Account.objects.count(),
            'pending_approvals': Account.objects.filter(status='pending').count(),
            'approved_users': Account.objects.filter(status='approved').count(),
            'rejected_users': Account.objects.filter(status='rejected').count(),
            'suspended_users': Account.objects.filter(status='suspended').count(),
            'active_today': Account.objects.filter(last_activity__gte=today_start).count(),
            'active_this_week': Account.objects.filter(last_activity__gte=week_start).count(),
            'total_words_learned': UserProgress.objects.aggregate(Sum('total_words_learned'))['total_words_learned__sum'] or 0,
            'total_lessons_completed': UserProgress.objects.aggregate(Sum('total_lessons_completed'))['total_lessons_completed__sum'] or 0,
        }
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def charts(self, request):
        # O'tgan 7 kundagi registratsiyalar trendi
        now = timezone.now()
        days = []
        registrations = []
        activity = []
        
        for i in range(6, -1, -1):
            date = (now - timedelta(days=i)).date()
            days.append(date.strftime('%Y-%m-%d'))
            registrations.append(Account.objects.filter(date_joined__date=date).count())
            activity.append(UserActivity.objects.filter(timestamp__date=date).count())

        return Response({
            'labels': days,
            'registration_data': registrations,
            'activity_data': activity
        })

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all().order_by('-date_joined')
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        user = self.get_object()
        user.status = 'approved'
        user.is_approved = True
        user.is_active = True
        user.save()
        
        AuditLog.objects.create(
            action='user_approved',
            admin=request.user,
            target_user=user,
            details=f"User {user.username} approved."
        )
        
        # Email notification
        try:
            send_mail(
                'English Edu - Hisobingiz faollashtirildi',
                f'Assalomu alaykum, {user.first_name or user.username}!\n\nSizning hisobingiz admin tomonidan tasdiqlandi. Endi tizimga kirishingiz mumkin.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except:
            pass
            
        return Response({'status': 'user approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        user = self.get_object()
        user.status = 'rejected'
        user.is_active = False
        user.save()
        
        AuditLog.objects.create(
            action='user_rejected',
            admin=request.user,
            target_user=user,
            details=f"User {user.username} rejected."
        )
        return Response({'status': 'user rejected'})

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        user = self.get_object()
        user.status = 'suspended'
        user.is_active = False
        user.save()
        
        AuditLog.objects.create(
            action='user_suspended',
            admin=request.user,
            target_user=user,
            details=f"User {user.username} suspended."
        )
        return Response({'status': 'user suspended'})

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        user = self.get_object()
        activities = user.activities.all().order_by('-timestamp')[:50]
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)

class AdminAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

class TelegramWebhookView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Tugmalar olib tashlangan, webhook hozircha faqat OK qaytaradi
        return Response({"status": "ok"})
