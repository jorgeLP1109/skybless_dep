from django.contrib import admin
from django.urls import path, include
from productos import views
from django.conf.urls.static import static
from django.conf import settings
from productos.views import subir_codigos

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('productos/', include('productos.urls')),
    path('productos/giftcards/', views.giftcards, name='giftcards'),
    path('accounts/', include('django.contrib.auth.urls')),  # Para manejar el login
    path('api/subir_codigos/', subir_codigos, name='subir_codigos'),
    
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
