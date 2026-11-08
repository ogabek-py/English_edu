from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminDashboardViewSet, AdminUserViewSet, AdminAuditLogViewSet,
    admin_dashboard, admin_notifications, delete_user,
    toggle_notification_status, delete_notification
)

router = DefaultRouter()
router.register(r'dashboard-api', AdminDashboardViewSet, basename='admin-dashboard-api')
router.register(r'users-api', AdminUserViewSet, basename='admin-users-api')
router.register(r'audit-logs-api', AdminAuditLogViewSet, basename='admin-audit-logs-api')

urlpatterns = [
    path('api/', include(router.urls)),
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('notifications/', admin_notifications, name='admin_notifications'),
    path('user/delete/<int:user_id>/', delete_user, name='delete_user'),
    path('notification/toggle/<int:notification_id>/', toggle_notification_status, name='toggle_notification_status'),
    path('notification/delete/<int:notification_id>/', delete_notification, name='delete_notification'),
]
