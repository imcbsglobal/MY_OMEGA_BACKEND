from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth / User
    path('api/', include('login.urls')),
    path('api/', include('User.urls')),
    path('api/user-controll/', include('user_controll.urls')),

    # HR
    path('api/hr/', include('HR.urls')),

    # Recruitment
    path('api/cv-management/', include('cv_management.urls')),
    path('api/interview-management/', include('interview_management.urls')),
    path('api/offer-letter/', include('offer_letter.urls')),

    # Employee
    path('api/employee-management/', include('employee_management.urls')),

    # Payroll
    path('api/payroll/', include('payroll.urls')),

    # Others
    path('api/whatsapp/', include('whatsapp_service.urls')),
    path('api/certificate/', include('certificate_hub.urls')),
    path('api/master/', include('master.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
