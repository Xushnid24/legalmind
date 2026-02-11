from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # все наши view доступны по /, /analyze_case/ и т.д.
]
