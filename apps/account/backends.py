from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import Account

class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(Account.USERNAME_FIELD)
        
        try:
            # Username yoki Email orqali foydalanuvchini topish
            user = Account.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except Account.DoesNotExist:
            return None
        except Account.MultipleObjectsReturned:
            # Agar bir xil email bilan bir nechta foydalanuvchi bo'lsa (teoretik jihatdan unique=True bo'lishi kerak)
            user = Account.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
