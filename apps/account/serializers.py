from rest_framework import serializers
from .models import Account, PasswordResetCode, UserActivity, UserProgress, AuditLog

class UserProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = ['total_lessons_completed', 'total_words_learned', 'learning_streak']

class AccountSerializer(serializers.ModelSerializer):
    progress = UserProgressSerializer(read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'is_staff', 'is_approved', 'status', 'date_joined', 
            'last_login', 'last_activity', 'progress'
        ]

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['id', 'activity_type', 'description', 'timestamp']

class AuditLogSerializer(serializers.ModelSerializer):
    admin_username = serializers.ReadOnlyField(source='admin.username')
    target_username = serializers.ReadOnlyField(source='target_user.username')
    
    class Meta:
        model = AuditLog
        fields = ['id', 'action', 'admin_username', 'target_username', 'timestamp', 'details']

class DashboardStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    pending_approvals = serializers.IntegerField()
    approved_users = serializers.IntegerField()
    rejected_users = serializers.IntegerField()
    suspended_users = serializers.IntegerField()
    active_today = serializers.IntegerField()
    active_this_week = serializers.IntegerField()
    total_words_learned = serializers.IntegerField()
    total_lessons_completed = serializers.IntegerField()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Account
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True}
        }

    def create(self, validated_data):
        user = Account.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not Account.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ushbu email bilan foydalanuvchi topilmadi.")
        return value.lower()

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        try:
            user = Account.objects.get(email__iexact=data['email'])
            reset_code = PasswordResetCode.objects.filter(user=user, code=data['code'], is_used=False).last()
            
            if not reset_code:
                raise serializers.ValidationError({"code": "Kod noto'g'ri."})
            
            if not reset_code.is_valid():
                raise serializers.ValidationError({"code": "Kodning amal qilish muddati tugagan."})
            
            data['user'] = user
            data['reset_code_obj'] = reset_code
            return data
        except Account.DoesNotExist:
            raise serializers.ValidationError({"email": "Foydalanuvchi topilmadi."})