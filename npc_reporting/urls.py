from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# from rest_framework_simplejwt.views import TokenRefreshView  # Temporarily disabled
# from reports.auth_views import CustomTokenObtainPairView  # Temporarily disabled

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('reports.urls')),
    path('api-auth/', include('rest_framework.urls')),
    # JWT endpoints temporarily disabled due to pkg_resources issue
    # path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair_alt'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh_alt'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
