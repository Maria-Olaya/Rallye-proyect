
from django.urls import path
from users.views import LoginView, LogoutView, UserProfileView

urlpatterns = [
    path("login/", LoginView.as_view(), name="api_login"),
    path("logout/", LogoutView.as_view(), name="api_logout"),
    path("profile/", UserProfileView.as_view(), name="api_profile"),
]
