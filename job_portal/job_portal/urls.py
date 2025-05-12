"""
URL configuration for job_portal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from jobs import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('profile/', include('Profile.urls')),
    path('rojgarhub/', views.rojgarhub, name='rojgarhub'),
    path('about/', views.about, name='about'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('post_job/', views.post_job, name='post_job'),
    path('apply_job/<int:job_id>/', views.apply_job, name='apply_job'),
    path('logout/', views.logout_view, name='logout'),
    path('feedback/', views.feedback, name='feedback'),
    path('uploads/<str:filename>/', views.uploads, name='uploads'),
    path('delete_job/<int:job_id>/', views.delete_job, name='delete_job'),
    path('application_details/<int:application_id>/', views.application_details, name='application_details'),
    path('job_details/<int:job_id>/', views.job_details, name='job_details'),
    path('delete_application/<int:application_id>/', views.delete_application, name='delete_application'),
    path('employer_application_details/<int:application_id>/', views.employer_application_details, name='employer_application_details'),
    path('dashboard_home/', views.dashboard_home, name='dashboard_home'),
    path('employer_dashboard/', views.employer_dashboard, name='employer_dashboard'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

