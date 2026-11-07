from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from apps.account.models import Account, Notification

@user_passes_test(lambda u: u.is_staff, login_url='/api/login-page/')
def admin_dashboard(request):
    users = Account.objects.all().order_by('-date_joined')
    return render(request, 'admin_dashboard.html', {'users': users})

@user_passes_test(lambda u: u.is_staff, login_url='/api/login-page/')
def admin_notifications(request):
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'admin_notifications.html', {'notifications': notifications})

@user_passes_test(lambda u: u.is_staff, login_url='/api/login-page/')
def delete_user(request, user_id):
    user = get_object_or_404(Account, id=user_id)
    if not user.is_staff: # Adminlarni o'chirib bo'lmasligi kerak
        user.delete()
    return redirect('admin_dashboard')

@user_passes_test(lambda u: u.is_staff, login_url='/api/login-page/')
def toggle_notification_status(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = not notification.is_read
    notification.save()
    return redirect('admin_notifications')

@user_passes_test(lambda u: u.is_staff, login_url='/api/login-page/')
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.delete()
    return redirect('admin_notifications')
