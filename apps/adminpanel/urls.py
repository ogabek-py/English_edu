from django.urls import path
from .views import (
    admin_dashboard, admin_notifications, delete_user,
    toggle_notification_status, delete_notification
)

urlpatterns = [
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('notifications/', admin_notifications, name='admin_notifications'),
    path('user/delete/<int:user_id>/', delete_user, name='delete_user'),
    path('notification/toggle/<int:notification_id>/', toggle_notification_status, name='toggle_notification_status'),
    path('notification/delete/<int:notification_id>/', delete_notification, name='delete_notification'),
]
