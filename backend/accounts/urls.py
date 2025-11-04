from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('auth/login/', views.login_view, name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/user/', views.user_profile_view, name='user'),
    path('auth/profile/', views.user_profile_view, name='profile'),
    path('auth/refresh/', views.refresh_token_view, name='refresh'),
    path('users/', views.users_list_view, name='users-list'),
]

