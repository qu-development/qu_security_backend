"""
URL configuration for qu_security project.

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

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Swagger/OpenAPI schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="QU Security API",
        default_version="v1",
        description="API documentation for QU Security Backend",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@qusecurity.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


def redirect_to_swagger(request):
    """Redirect root URL to Swagger documentation"""
    return redirect("schema-swagger-ui")


urlpatterns = [
    # Language selection - outside i18n_patterns to work for all languages
    path("i18n/", include("django.conf.urls.i18n")),
    # Root URL redirects to Swagger
    path("", redirect_to_swagger, name="root-redirect"),
]

# Internationalized URL patterns
urlpatterns += i18n_patterns(
    # Admin panel
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/", include("core.urls")),
    # Mobile API endpoints
    path("api/mobile/", include("mobile.urls")),
    # Common endpoints
    path("api/common/", include("common.urls")),
    # Permission-secured endpoints
    path("", include("permissions.urls")),
    # Swagger/OpenAPI documentation
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
)

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
