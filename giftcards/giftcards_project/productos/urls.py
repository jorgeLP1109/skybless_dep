from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import MetodoPagoView
from .views import user_dashboard
from .views import edit_profile
from .views import subir_codigos
from .views import comprar_giftcard


urlpatterns = [
    path('', views.home, name='home'),
    path('giftcards/', views.listar_giftcards, name='listar_giftcards'),
    #path('giftcards/', views.giftcards, name='giftcards'),
    path('comprar/', views.comprar_giftcard, name='comprar_giftcard'),
    path("comprar/", comprar_giftcard, name="comprar_giftcard"),
    path('paypal/', include('paypal.standard.ipn.urls')),
    path('ipn/', views.paypal_ipn, name='paypal_ipn'),
    path('procesar_pago/', views.procesar_pago, name='procesar_pago'),
    path('pago_exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path('stripe/', views.stripe_checkout, name='stripe_checkout'),
    path('pago_exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path('historial-pagos/', views.historial_pagos, name='historial_pagos'),
    path('productos/giftcards/<int:id>/', views.giftcard_detail, name='giftcard_detail'),
    path('signup/', views.signup, name='signup'),
    path('accounts/activate/<uidb64>/<token>/', views.activate, name='activate'),
    #path('metodo_pago/<str:metodo>/', views.metodo_pago, name='metodo_pago'),
    path('procesar/', views.procesar_compra, name='procesar_compra'),  # Para seleccionar giftcard y precio
    path('metodo_pago/<str:metodo>/', views.MetodoPagoView.as_view(), name='metodo_pago'),  # Para el pago
    # ...
    #path('metodo_pago/<str:metodo>/', MetodoPagoView.as_view(), name='metodo_pago'),
    path('exito/', views.pagina_exito, name='pagina_exito'),
    path('listar/', views.listar_giftcards, name='listar_giftcards'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('promociones/', views.promociones, name='promociones'),
    #path('recarga/', views.recarga_directa, name='recarga_directa'),
    path('recargas/', views.lista_juegos, name='lista_juegos'),
    path('recargas/<int:juego_id>/', views.detalles_juego, name='detalles_juego'),
    path('api/subir_codigos/', subir_codigos, name='subir_codigos'),
    path('procesar_pago/', views.procesar_pago, name='procesar_pago'),
    path('recibo/<int:compra_id>/', views.mostrar_recibo, name='mostrar_recibo'), # Nueva URL para mostrar el recibo
    path('imprimir/', views.imprimir_reporte, name='imprimir_reporte'), 
    path('api/codigos/', views.CodigoGiftCardList.as_view(), name='lista_codigos'),  # Nueva URL para la API
    path('carrito/agregar/<int:giftcard_id>/', views.agregar_al_carrito, name='agregar_al_carrito'), # Cambiado a giftcard_id
    path('carrito/', views.mostrar_carrito, name='mostrar_carrito'),
    path('carrito/eliminar/<int:codigo_giftcard_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/procesar/', views.procesar_compra, name='procesar_compra'),
    path('recibo/<int:compra_id>/imprimir/', views.imprimir_recibo, name='imprimir_recibo'),path('playstation/', views.playstation_giftcards, name='playstation_giftcards'),
    path('nintendo/', views.nintendo_giftcards, name='nintendo_giftcards'),
    path('steam/', views.steam_giftcards, name='steam_giftcards'),
    path('itunes/', views.itunes_giftcards, name='itunes_giftcards'),
    path('xbox/', views.xbox_giftcards, name='xbox_giftcards'),
    path('roblox/', views.roblox_giftcards, name='roblox_giftcards'),
    path('google-play/', views.google_play_giftcards, name='google_play_giftcards'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
