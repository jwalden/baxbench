from django.urls import path
from .views import InviteUserView, CreateUserView

urlpatterns = [
    path('invite_user', InviteUserView.as_view(), name='invite_user'),
    path('create_user', CreateUserView.as_view(), name='create_user'),
]