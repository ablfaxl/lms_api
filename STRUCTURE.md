# 🐍 راهنمای ساختار پروژه و کد تمیز — Django REST Framework (Backend)

> اصول: **SOLID · KISS · DRY · Clean Code · Best Practices**

---

## 📁 ساختار پوشه‌بندی پروژه

```
backend/
├── config/                      # تنظیمات اصلی پروژه
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              # تنظیمات مشترک
│   │   ├── development.py       # تنظیمات محیط توسعه
│   │   └── production.py        # تنظیمات محیط عملیاتی
│   ├── urls.py                  # URL اصلی
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                        # اپلیکیشن‌های Django
│   ├── users/                   # Feature: مدیریت کاربران
│   │   ├── migrations/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── managers.py          # Custom Model Managers
│   │   ├── models.py
│   │   ├── services.py          # Business Logic
│   │   ├── selectors.py         # Query Layer (Pattern: Django Styleguide)
│   │   ├── permissions.py       # Custom Permissions
│   │   ├── signals.py
│   │   ├── tasks.py             # Celery Tasks
│   │   ├── tests/
│   │   │   ├── test_models.py
│   │   │   ├── test_services.py
│   │   │   └── test_api.py
│   │   ├── admin.py
│   │   └── apps.py
│   │
│   ├── products/
│   │   └── ...                  # همان ساختار
│   │
│   └── orders/
│       └── ...
│
├── common/                      # کد مشترک بین اپ‌ها
│   ├── __init__.py
│   ├── models.py                # Base Model (TimeStampedModel)
│   ├── serializers.py           # Base Serializers
│   ├── permissions.py           # Permissions مشترک
│   ├── exceptions.py            # Custom Exceptions
│   ├── pagination.py            # Custom Pagination
│   ├── utils/
│   │   ├── email.py
│   │   └── validators.py
│   └── middleware/
│       └── request_logger.py
│
├── tests/                       # تست‌های Integration و E2E
│   ├── conftest.py
│   └── factories/               # Factory Boy Factories
│       ├── user_factory.py
│       └── product_factory.py
│
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── .env.example
├── .env
├── Makefile
├── manage.py
└── pyproject.toml               # ruff, black, mypy config
```

---

## 🧱 SOLID در Django REST Framework

### S — Single Responsibility (مسئولیت واحد)

View فقط HTTP مدیریت می‌کند، Business Logic در Service است.

```python
# ❌ بد — View پر از لاجیک است
class UserRegisterView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email exists'}, status=400)
        user = User.objects.create_user(
            email=email,
            password=request.data['password']
        )
        # ارسال ایمیل
        send_mail('Welcome', 'Hello!', 'no-reply@app.com', [email])
        token = Token.objects.create(user=user)
        return Response({'token': token.key})


# ✅ خوب — جداسازی لایه‌ها

# apps/users/services.py
class UserService:
    @staticmethod
    def register(email: str, password: str) -> User:
        """ثبت‌نام کاربر جدید"""
        if UserSelector.email_exists(email):
            raise ValidationError({'email': 'این ایمیل قبلاً ثبت شده است.'})
        
        user = User.objects.create_user(email=email, password=password)
        EmailService.send_welcome_email(user)
        return user


# apps/users/selectors.py
class UserSelector:
    @staticmethod
    def email_exists(email: str) -> bool:
        return User.objects.filter(email=email).exists()
    
    @staticmethod
    def get_active_users() -> QuerySet:
        return User.objects.filter(is_active=True).select_related('profile')


# apps/users/api/views.py
class UserRegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = UserService.register(**serializer.validated_data)
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({'token': token.key}, status=status.HTTP_201_CREATED)
```

---

### O — Open/Closed (باز برای توسعه، بسته برای تغییر)

```python
# ✅ Base Serializer قابل توسعه
# common/serializers.py
class TimestampedModelSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    updated_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')


# apps/products/api/serializers.py
class ProductSerializer(TimestampedModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'created_at', 'updated_at']


# ✅ Base ViewSet قابل توسعه بدون تغییر
# common/views.py
class BaseModelViewSet(ModelViewSet):
    def get_serializer_class(self):
        action_serializers = getattr(self, 'action_serializers', {})
        return action_serializers.get(self.action, self.serializer_class)


# apps/products/api/views.py
class ProductViewSet(BaseModelViewSet):
    serializer_class = ProductSerializer
    action_serializers = {
        'create': ProductCreateSerializer,
        'list': ProductListSerializer,
    }
```

---

### L — Liskov Substitution (جایگزینی لیسکوف)

```python
# ✅ Base Model مشترک برای همه مدل‌ها
# common/models.py
import uuid
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])


# همه مدل‌ها از BaseModel ارث می‌برند و رفتار یکسان دارند
class User(BaseModel):
    email = models.EmailField(unique=True)

class Product(BaseModel):
    name = models.CharField(max_length=255)

class Order(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
```

---

### I — Interface Segregation (جداسازی اینترفیس)

```python
# ✅ Permission های کوچک و متمرکز به جای یک Permission بزرگ
# apps/users/permissions.py
class IsOwner(BasePermission):
    """فقط صاحب آبجکت دسترسی دارد"""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsAdminOrReadOnly(BasePermission):
    """ادمین همه چیز، بقیه فقط خواندن"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff


class IsEmailVerified(BasePermission):
    """فقط کاربران تأییدشده"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.email_verified


# ترکیب Permission ها در View
class ProductViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsOwner]
```

---

### D — Dependency Inversion (وارونگی وابستگی)

```python
# ✅ EmailService به provider وابسته نیست
# common/utils/email.py
from abc import ABC, abstractmethod
from django.conf import settings


class EmailBackend(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> None:
        pass


class DjangoEmailBackend(EmailBackend):
    def send(self, to: str, subject: str, body: str) -> None:
        from django.core.mail import send_mail
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to])


class SendGridEmailBackend(EmailBackend):
    def send(self, to: str, subject: str, body: str) -> None:
        # SendGrid implementation
        pass


class EmailService:
    def __init__(self, backend: EmailBackend = None):
        self.backend = backend or DjangoEmailBackend()
    
    def send_welcome_email(self, user: 'User') -> None:
        self.backend.send(
            to=user.email,
            subject='خوش آمدید!',
            body=f'سلام {user.get_full_name()}'
        )
```

---

## 💧 DRY — Don't Repeat Yourself

```python
# ✅ Generic Mixin برای عملیات تکراری
# common/views.py
class SoftDeleteMixin:
    """به جای حذف واقعی، غیرفعال می‌کند"""
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuditLogMixin:
    """تغییرات را لاگ می‌کند"""
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


# استفاده در ViewSet
class ProductViewSet(SoftDeleteMixin, AuditLogMixin, ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
```

```python
# ✅ Custom Manager برای query های تکراری
# apps/products/managers.py
class ProductManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)
    
    def in_stock(self):
        return self.active().filter(stock__gt=0)
    
    def by_category(self, category_id: int):
        return self.active().filter(category_id=category_id).select_related('category')


class Product(BaseModel):
    objects = ProductManager()
    
# استفاده
Product.objects.in_stock()
Product.objects.by_category(category_id=5)
```

---

## 🤏 KISS — Keep It Simple, Stupid

```python
# ❌ بد — پیچیده‌تر از نیاز
class UserSerializer(serializers.ModelSerializer):
    def validate(self, data):
        errors = {}
        if 'password' in data:
            if len(data['password']) < 8:
                errors['password'] = ['رمز عبور باید حداقل ۸ کاراکتر باشد.']
            if not any(c.isupper() for c in data['password']):
                errors['password'] = errors.get('password', []) + ['باید حروف بزرگ داشته باشد.']
        if errors:
            raise serializers.ValidationError(errors)
        return data

# ✅ خوب — استفاده از validators ساده و خوانا
from django.core.validators import MinLengthValidator

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[MinLengthValidator(8)],
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name']
```

---

## ✅ Best Practices

### تنظیمات محیطی

```python
# config/settings/base.py
from pathlib import Path
import environ

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# خواندن .env به صورت اتوماتیک
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

DATABASES = {
    'default': env.db('DATABASE_URL')  # postgres://user:pass@host/db
}
```

### Custom Exception Handler

```python
# common/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        response.data = {
            'success': False,
            'errors': response.data,
            'status_code': response.status_code,
        }
    return response


# config/settings/base.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'common.exceptions.custom_exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
```

### Custom Pagination

```python
# common/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'total_pages': self.page.paginator.num_pages,
            'results': data,
        })
```

### URL نامگذاری استاندارد

```python
# apps/products/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('products', views.ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
    path('products/<uuid:pk>/publish/', views.ProductPublishView.as_view(), name='product-publish'),
]

# config/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include([
        path('', include('apps.users.api.urls')),
        path('', include('apps.products.api.urls')),
        path('', include('apps.orders.api.urls')),
    ])),
]
```

### Model استاندارد

```python
# apps/products/models.py
from django.db import models
from common.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Product(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name='products'
    )

    objects = ProductManager()

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['price']),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0
```

---

## 📋 چک‌لیست کد تمیز

| قانون | توضیح |
|-------|--------|
| ✅ Fat Model, Thin View | لاجیک در Model/Service، نه View |
| ✅ Service Layer | Business Logic جدا از View |
| ✅ Selector Layer | Query های پیچیده در selectors.py |
| ✅ select_related / prefetch | جلوگیری از N+1 query |
| ✅ تنظیمات چندمحیطی | base / dev / prod جدا باشند |
| ✅ Custom Exception | پاسخ خطا یکنواخت باشد |
| ✅ UUID به جای Integer ID | امنیت بیشتر در API |
| ✅ Soft Delete | حذف واقعی نداریم |
| ✅ Type Hints | همه توابع type hint دارند |
| ✅ Docstring فارسی | توضیح برای توابع مهم |
| ✅ تست نوشته شده | حداقل ۸۰٪ پوشش تست |
| ✅ `.env.example` در گیت | هرگز `.env` را کامیت نکن |
