from django.urls import path
from . import views
urlpatterns = [
    path('', views.profile_display, name='profile_display'),
    path('update/', views.profile_update, name='profile_update'),
]