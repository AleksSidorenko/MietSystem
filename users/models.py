# ### `users/models.py`


from datetime import timedelta

from django.contrib.auth.models import (  # <--- Добавили импорт Group и Permission
    AbstractBaseUser,
    BaseUserManager,
    Group,
    Permission,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class VerificationToken(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["token"])]
        constraints = [
            models.UniqueConstraint(fields=["user", "token"], name="unique_user_token")
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)


class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("Email is required"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("role", "ADMIN")
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        # Суперпользователь должен быть автоматически добавлен в группы и иметь все пермиссии
        # (permissionsmixin позаботится об этом, если поля groups и user_permissions добавлены)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("TENANT", "Tenant"),
        ("LANDLORD", "Landlord"),
        ("ADMIN", "Admin"),
    )
    LANGUAGE_CHOICES = (
        ("en", "English"),
        ("de", "Deutsch"),
        ("ru", "Русский"),
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="TENANT")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="en")
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    history = HistoricalRecords()

    # --- ДОБАВЛЕННЫЕ ПОЛЯ ДЛЯ РАБОТЫ С PERMISSIONSMIXIN И ГРУППАМИ ---
    # groups = models.ManyToManyField(
    #     Group,
    #     verbose_name=_('groups'),
    #     blank=True,
    #     help_text=_(
    #         'The groups this user belongs to. A user will get all permissions '
    #         'granted to each of their groups.'
    #     ),
    #     related_name="custom_user_set", # Используй unique related_name
    #     related_query_name="custom_user",
    # )
    # user_permissions = models.ManyToManyField(
    #     Permission,
    #     verbose_name=_('user permissions'),
    #     blank=True,
    #     help_text=_('Specific permissions for this user.'),
    #     related_name="custom_user_set", # Используй unique related_name, тот же, что и выше, если хочешь
    #     related_query_name="custom_user",
    # )
    # ------------------------------------------------------------------

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "role"]

    class Meta:
        indexes = [
            models.Index(fields=["email"], name="user_email_idx"),
            models.Index(fields=["role"], name="user_role_idx"),
        ]
        # default_related_name = 'custom_user'
        verbose_name = _("User")
        verbose_name_plural = "Users (Пользователи)"  # Оставил твой verbose_name_plural

    def __str__(self):
        return self.email

    # --- ИСПРАВЛЕННЫЕ МЕТОДЫ РАЗРЕШЕНИЙ ---
    # УДАЛЯЕМ has_perm и has_module_perms, чтобы PermissionsMixin работал как надо.
    # PermissionsMixin предоставит правильную логику,
    # которая будет учитывать группы и user_permissions.
    # Если тебе нужна кастомная логика, используй ее только там, где это необходимо,
    # например, в методах ModelAdmin или в функциях-проверках.
    # Если ты хочешь, чтобы ADMIN роль всегда имела все права,
    # то лучше убедиться, что пользователи с ролью 'ADMIN' являются is_superuser.
    # Твой UserManager.create_superuser уже делает is_superuser=True для ADMIN.
    # Если ты хочешь, чтобы 'ADMIN' роль имела все права БЕЗ is_superuser,
    # то тебе придется реализовать это иначе, но это усложнит.
    # Пока оставим логику PermissionsMixin, она более стандартна.
    # Если тебе нужны эти методы, дай знать, мы их адаптируем.
    # For now, relying on PermissionsMixin for proper group/permission checks.
    # ----------------------------------------


#
# from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
# from django.db import models
# from simple_history.models import HistoricalRecords
# from django.utils import timezone
# from datetime import timedelta
# from django.utils.translation import gettext_lazy as _
#
# class VerificationToken(models.Model):
#     user = models.ForeignKey('User', on_delete=models.CASCADE)
#     token = models.CharField(max_length=64, unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     expires_at = models.DateTimeField()
#
#     class Meta:
#         indexes = [models.Index(fields=['token'])]
#         constraints = [
#             models.UniqueConstraint(fields=['user', 'token'], name='unique_user_token')
#         ]
#
#     def save(self, *args, **kwargs):
#         if not self.expires_at:
#             self.expires_at = timezone.now() + timedelta(hours=24)
#         super().save(*args, **kwargs)
#
# class UserManager(BaseUserManager):
#     def create_user(self, email, password, **extra_fields):
#         if not email:
#             raise ValueError(_('Email is required'))
#         email = self.normalize_email(email)
#         user = self.model(email=email, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
#
#     def create_superuser(self, email, password, **extra_fields):
#         extra_fields.setdefault('role', 'ADMIN')
#         extra_fields.setdefault('is_active', True)
#         extra_fields.setdefault('is_verified', True)
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         return self.create_user(email, password, **extra_fields)
#
# class User(AbstractBaseUser, PermissionsMixin):
#     ROLE_CHOICES = (
#         ('TENANT', 'Tenant'),
#         ('LANDLORD', 'Landlord'),
#         ('ADMIN', 'Admin'),
#     )
#     LANGUAGE_CHOICES = (
#         ('en', 'English'),
#         ('de', 'Deutsch'),
#         ('ru', 'Русский'),
#     )
#
#     email = models.EmailField(unique=True)
#     first_name = models.CharField(max_length=30)
#     last_name = models.CharField(max_length=30)
#     phone_number = models.CharField(max_length=15, blank=True)
#     role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='TENANT')
#     language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
#     is_active = models.BooleanField(default=True)
#     is_verified = models.BooleanField(default=False)
#     date_joined = models.DateTimeField(auto_now_add=True)
#     is_staff = models.BooleanField(default=False)
#     is_superuser = models.BooleanField(default=False)
#     history = HistoricalRecords()
#
#     objects = UserManager()
#
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['first_name', 'last_name', 'role']
#
#     class Meta:
#         indexes = [
#             models.Index(fields=['email'], name='user_email_idx'),
#             models.Index(fields=['role'], name='user_role_idx'),
#         ]
#         verbose_name = _('User')
#         # verbose_name_plural = _('Users')
#         verbose_name_plural = 'Users (Пользователи)'
#
#
#     def __str__(self):
#         return self.email
#
#     def has_perm(self, perm, obj=None):
#         return self.is_superuser or self.role == 'ADMIN'
#
#     def has_module_perms(self, app_label):
#         return self.is_superuser or self.role == 'ADMIN'
