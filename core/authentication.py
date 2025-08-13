# core/authentication.py
from drf_spectacular.authentication import OpenApiAuthenticationExtension
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import UntypedToken
from django.contrib.auth import get_user_model
from django.conf import settings


class CookieJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'core.authentication.CookieJWTAuthentication'  # полное имя класса
    name = 'cookieJWT'  # название схемы в Swagger

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'cookie',
            'name': 'access_token',  # имя куки, если ты так назвал
        }

User = get_user_model()

class CookieJWTAuthentication(BaseAuthentication):
    """
    Кастомный класс аутентификации для извлечения JWT-токена из куки 'access_token'.
    Используется для аутентификации через DRF с токеном, выданным CustomTokenObtainPairView.
    """
    def authenticate(self, request):
        # Извлекаем токен из куки
        token = request.COOKIES.get('access_token')
        if not token:
            return None  # Возвращаем None для анонимного доступа, если токен отсутствует

        try:
            # Валидация токена
            validated_token = UntypedToken(token)
            # Предполагаем, что токен содержит 'user_id' (или другой идентификатор)
            user_id = validated_token.get('user_id')
            if not user_id:
                raise KeyError('No user_id in token payload')
            user = User.objects.get(id=user_id)
            if not user.is_active:
                raise AuthenticationFailed('User is inactive or deleted')
            return (user, validated_token)
        except (KeyError, User.DoesNotExist, ValueError, Exception) as e:
            raise AuthenticationFailed('Invalid token or user') from e


