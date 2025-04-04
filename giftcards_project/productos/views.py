from django.shortcuts import render, redirect, get_object_or_404
from .models import GiftCard, Compra, CodigoGiftCard, Price, Transaction  # Importa todos los modelos necesarios
from .forms import CompraGiftCardForm, CustomUserCreationForm # Importa los formularios
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import stripe
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.ipn.models import PayPalIPN
from .models import Pago, CarouselImage, MetodoPago, CodigoGiftCardHistorial, Tarjeta, JuegoRecarga
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.views import View
from django.utils import timezone
from django.utils.timezone import now
import json
from django.contrib.sites.shortcuts import get_current_site
from .whatsapp_api import enviar_mensaje_whatsapp  # Archivo donde está la función
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import CodigoEnviado  # Assuming models.py is in the same directory
from .serializers import CodigoGiftCardSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics
from decimal import Decimal
from django.db import transaction, IntegrityError
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Carrito, CodigoGiftCard
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib import messages 
from django.core.serializers.json import DjangoJSONEncoder
from .models import Compra, Price
import requests
from decimal import Decimal
from django.contrib.auth.views import redirect_to_login
from .forms import PagoPostVirtualForm, PagoMovilForm, PagoC2PForm
from .models import Carrito, Compra, Transaction
from .banco_api import * # Importar funciones de banco_api.py
from Crypto.Cipher import AES  # Importar clase AES
from .models import CredencialesBNC
from .forms import PagoC2PForm
import hashlib
import base64

from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
import json


def solicitar_recarga(request):
    if request.method == "POST":
        juego_id = request.POST.get("juego_id")
        monto = request.POST.get("monto")
        usuario_id = request.user.id
        numero_receptor = "584129368715"  # Reemplaza con tu número personal

        # Obtén el nombre del juego
        juego = JuegoRecarga.objects.get(id=juego_id)
        nombre_juego = juego.nombre

        try:
            juego_monto = json.loads(juego.monto)  # Esto convertirá el JSON a una lista
        except json.JSONDecodeError:
            juego_monto = []

            context = {
                'juego': juego,
                'juego_monto': juego_monto,  # Pasamos la lista de montos al contexto
            }

        # Enviar mensaje a WhatsApp
        response = enviar_mensaje_whatsapp(usuario_id, nombre_juego, monto, numero_receptor)

        if response.status_code == 200:
            return JsonResponse({"success": True, "message": "Solicitud enviada correctamente"})
        else:
            return JsonResponse({"success": False, "message": "Error al enviar solicitud"})

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            current_site = get_current_site(request)
            email_subject = 'Confirma tu cuenta'
            message = render_to_string('registration/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
            })

            send_mail(
                email_subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})





def giftcards(request):
    # tu lógica para mostrar las giftcards
    return render(request, 'productos/giftcards.html')


def giftcard_detail(request, id):
    giftcard = get_object_or_404(GiftCard, id=id)

    if request.user.is_authenticated:
        return render(request, 'productos/giftcard_detail.html', {'giftcard': giftcard})
    else:
        return redirect_to_login(request.path)  # Redirige al login con el parámetro next

'''
def home(request):
    giftcards = GiftCard.objects.all()
    carousel_images = CarouselImage.objects.all()
    return render(request, 'productos/home.html', {'giftcards': giftcards, 'carousel_images': carousel_images})
'''

def home(request):
    giftcards = GiftCard.objects.filter(id__in=[ 2, 7, 17, 28, 47, 67, 78]) #mostrando giftcard por su indice
    carousel_images = CarouselImage.objects.all()
    tipos_giftcards = GiftCard.objects.values_list('tipo', flat=True).distinct()

    return render(request, 'productos/home.html', {
        'giftcards': giftcards,
        'carousel_images': carousel_images,
        'tipos_giftcards': tipos_giftcards,
    })


def enviar_codigo(user, codigo):
    subject = 'Tu Gift Card Comprada'
    message = f'Hola {user.username}, has comprado una gift card con el código: {codigo}'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


# Vista para listar gift cards



def listar_giftcards(request):
    giftcards = GiftCard.objects.all()
    search_query = request.GET.get('q', '')
    if search_query:
        giftcards = giftcards.filter(name__icontains=search_query)

    if giftcards.exists():
        first_giftcard = giftcards.first()
        return redirect(f'/productos/{first_giftcard.tipo}/')  # Redirige a la lista correspondiente
    else:
        return redirect('/productos/home/')  # Redirige a una lista predeterminada si no hay giftcards

# Vista para comprar gift card
@login_required
def comprar_giftcard(request):
    if request.method == "POST":
        try:
            user = request.user  # Usuario autenticado
            data = json.loads(request.body)
            tarjeta_id = data.get("tarjeta_id")

            # Buscar la tarjeta
            tarjeta = get_object_or_404(Tarjeta, id=tarjeta_id)

            # Buscar un código disponible
            codigo_giftcard = CodigoGiftCard.objects.filter(
                tarjeta=tarjeta, disponible=True
            ).first()

            if not codigo_giftcard:
                return JsonResponse({"error": "No hay códigos disponibles para esta tarjeta"}, status=400)

            # Asignar el código al usuario y marcarlo como usado
            codigo_giftcard.usuario_asociado = user
            codigo_giftcard.disponible = False
            codigo_giftcard.fecha_uso = now()
            codigo_giftcard.save()

            # Enviar recibo electrónico
            send_mail(
                "Pago exitoso",
                f"Gracias por tu compra. Tu código de giftcard es: {codigo_giftcard.codigo}",
                "from@example.com",
                [user.email],
                fail_silently=False,
            )

            # Renderizar la página de confirmación con el código
            return render(
                request,
                "productos/confirmacion_compra.html",
                {"codigo": codigo_giftcard.codigo, "tarjeta": tarjeta},
            )

        except Exception as e:
            return JsonResponse({"error": f"Error interno: {str(e)}"}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)




def pago_exitoso(request):
    return render(request, 'productos/pago_exitoso.html')

def stripe_checkout(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Gift Card',
                },
                'unit_amount': 1000,  # Monto en centavos ($10.00)
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri('/pago_exitoso/'),
        cancel_url=request.build_absolute_uri('/'),
    )

    return redirect(session.url, code=303)

def pago_exitoso(request):
    return render(request, 'productos/pago_exitoso.html')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        # Manejar el pago exitoso
        print("Pago recibido.")

    return HttpResponse(status=200)



@csrf_exempt
def paypal_ipn(request):
    ipn = PayPalIPN()
    ipn.initialize(request)

    if ipn.is_valid() and ipn.payment_status == "Completed":
        pago = Pago.objects.create(
            usuario=request.user,
            monto=ipn.mc_gross,
            moneda=ipn.mc_currency,
            estado=ipn.payment_status,
            transaccion_id=ipn.txn_id,
        )
        
        # Enviar un correo al usuario con la información del pago
        send_mail(
            'Pago Recibido',
            f'Gracias por tu pago. Tu pago de {pago.monto} {pago.moneda} ha sido procesado correctamente. Transacción ID: {pago.transaccion_id}',
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False,
        )

        print(f"Pago registrado para: {ipn.txn_id}")
    else:
        print("Pago no completado o IPN no válido")

    return HttpResponse(status=200)

@login_required
def historial_pagos(request):
    # Filtramos los pagos solo para el usuario logueado
    pagos = Pago.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'productos/historial_pagos.html', {'pagos': pagos})



def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode('utf-8')
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, ):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('login')  # Redirige a la página de login
    else:
        return HttpResponse('El enlace de activación no es válido.', status=400)
    

def procesar_pago(request):
    if request.method == 'POST':
        giftcard_id = request.POST.get('giftcard_id')
        price_id = request.POST.get('price_id')

        # Guardar los IDs en la sesión
        request.session['giftcard_id'] = giftcard_id
        request.session['price_id'] = price_id

        return redirect(reverse('metodo_pago', args=['ficticio']))  # Redirigir directamente
    return render(request, 'productos/procesar_pago.html')  # Para el caso GET

        

def pagina_exito(request):
    return render(request, 'productos/exito.html')    



def verificar_pago(request, transaccion_id):
    # Lógica de verificación del pago
    pago_verificado = True  # Asume que `pago_verificado` es True si el pago es correcto
    if pago_verificado:
        # Buscar un código disponible para el tipo y monto específicos
        tipo = "Amazon"  # Ejemplo: tipo específico
        monto = 50.00    # Ejemplo: monto específico
        codigo = CodigoGiftCard.objects.filter(tipo=tipo, monto=monto, disponible=True).first()

        if codigo:
            # Asociar el código al usuario y marcarlo como usado
            codigo.disponible = False
            codigo.usuario_asociado = request.user
            codigo.fecha_uso = now()
            codigo.save()

            # Mostrar el código al usuario
            return render(request, 'codigo_asignado.html', {'codigo': codigo})
        else:
            return render(request, 'error.html', {'mensaje': 'No hay códigos disponibles para este tipo y monto.'})
        


@login_required
def user_dashboard(request):
    user = request.user

    # Obtener las últimas 10 compras del usuario ordenadas por fecha de compra descendente
    compras = Compra.objects.filter(usuario=user).order_by('-fecha_compra')[:10]

    # Preparar los datos para la plantilla
    historial = []  # Inicializar la lista historial
    for compra in compras:
        for giftcard in compra.giftcards.all():
            # Asumiendo que 'compra.codigos_giftcard' es una lista de códigos
            codigo = compra.codigos_giftcard[list(compra.giftcards.all()).index(giftcard)]

            # Obtener la Tarjeta correspondiente a la GiftCard
            try:
                tarjeta = giftcard.tarjeta  # Asumiendo que 'tarjeta' es el campo ForeignKey en GiftCard
                codigo_giftcard = CodigoGiftCard.objects.get(tarjeta=tarjeta, codigo=codigo)

                # Obtener el precio de la giftcard a través del modelo Price
                precio_giftcard = Price.objects.filter(codigos=codigo_giftcard, habilitado=True).first()
                if precio_giftcard:
                    precio = precio_giftcard.amount
                else:
                    precio = "No disponible"
            except (CodigoGiftCard.DoesNotExist, AttributeError):
                precio = "No disponible"

            historial.append({
                'tarjeta': giftcard.name,
                'price': precio,
                'codigo': codigo,
                'fecha_uso': compra.fecha_compra,
            })

    return render(request, 'user_dashboard.html', {'user': user, 'historial': historial})

def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('user_dashboard.html')
    else:
        form = CustomUserCreationForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})


def promociones(request):
    # tu lógica para mostrar las promociones
    return render(request, 'productos/promociones.html')



def lista_juegos(request):
    juegos = JuegoRecarga.objects.all()
    return render(request, 'recargas/lista_juegos.html', {'juegos': juegos})

def detalles_juego(request, juego_id):
    # Obtener el juego por su ID
    #juego = get_object_or_404(Juego, id=juego_id)
    juego = JuegoRecarga.objects.get(id=juego_id)

    if request.method == 'POST':
        # Obtener los datos del formulario
        monto = request.POST.get('monto')
        jugador_id = request.POST.get('jugador_id')
        
        if monto and jugador_id:
            usuario_id = request.user.id  # ID del usuario autenticado
            numero_receptor = "584129368715"  # Número fijo o dinámico, según lo implementes
            
            try:
                # Llamar a la función para enviar mensaje de WhatsApp
                response = enviar_mensaje_whatsapp(
                    usuario_id=usuario_id,
                    juego=juego.nombre,  # Pasar el nombre del juego
                    monto=monto,
                    jugador_id=jugador_id,
                    numero_receptor=numero_receptor
                )

                # Validar el código de respuesta de la API
                if response.status_code == 200:
                    return redirect('pago_exitoso')  # Redirige a una página de éxito
                else:
                    return HttpResponse(f"Error al enviar mensaje: {response.status_code} - {response.text}", status=500)
            except Exception as e:
                return HttpResponse(f"Error: {e}", status=500)
        else:
            return HttpResponse("Faltan datos obligatorios.", status=400)

    # Renderizar la plantilla para la página de recargas
    return render(request, 'recargas/detalles_juego.html', {'juego': juego})

def confirmar_compra(request, giftcard_id):
    giftcard = get_object_or_404(GiftCard, id=giftcard_id)

    # Verificar si hay códigos disponibles
    codigo_disponible = CodigoGiftCard.objects.filter(giftcard=giftcard, usado=False).first()

    if not codigo_disponible:
        return render(request, "productos/sin_codigos.html", {"giftcard": giftcard})

    # Marcar el código como usado
    codigo_disponible.usado = True
    codigo_disponible.save()

    return render(request, "productos/confirmacion_compra.html", {"giftcard": giftcard, "codigo": codigo_disponible.codigo})



User = get_user_model()  # Obtén el modelo de usuario personalizado


@csrf_exempt
def subir_codigos(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            usuario_asociado = User.objects.get(username='admin')

            with transaction.atomic():
                for item in data:
                    nombre = item['nombre']
                    montos = item['monto']
                    codigo = item['codigo']

                    tarjeta, created = Tarjeta.objects.get_or_create(name=nombre)

                    try:
                        # Intenta convertir el código a mayúsculas para evitar duplicados por diferencia de mayúsculas
                        codigo = codigo.upper()

                        if not CodigoGiftCard.objects.filter(codigo=codigo).exists():
                            codigo_giftcard = CodigoGiftCard.objects.create(
                                tarjeta=tarjeta,
                                codigo=codigo,
                                usuario_asociado=usuario_asociado
                            )

                            if not isinstance(montos, list):
                                montos = [montos]

                            prices_ids = []
                            for monto in montos:
                                try:
                                    monto_decimal = Decimal(monto)
                                    price = Price.objects.get(amount=monto_decimal)
                                    prices_ids.append(price.id)
                                except Price.DoesNotExist:
                                    return HttpResponseBadRequest({'error': f'No se encontró el precio {monto}.'})
                                except (TypeError, ValueError):
                                    return HttpResponseBadRequest({'error': f'El monto {monto} no es un número válido.'})

                            codigo_giftcard.prices.set(prices_ids)
                        else:
                            print(f"Código duplicado omitido: {codigo}")

                    except IntegrityError:
                        return HttpResponseBadRequest({'error': f'Error al crear el código {codigo}. Es posible que ya exista.'})

            return JsonResponse({'message': 'Códigos cargados exitosamente'}, status=201)

        except json.JSONDecodeError:
            return HttpResponseBadRequest({'error': 'Formato JSON inválido.'})
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

def imprimir_reporte(request):
    # Obtén los objetos filtrados (puedes usar los mismos filtros del admin)
    codigos = CodigoEnviado.objects.all()  # O aplica filtros si es necesario
    return render(request, 'productos/reporte_impresion.html', {'codigos': codigos})



class CodigoGiftCardPagination(PageNumberPagination):
    page_size = 100  # Define la cantidad de elementos por página (ajusta este número según tus necesidades)

class CodigoGiftCardList(generics.ListAPIView):
    queryset = CodigoGiftCard.objects.all()
    serializer_class = CodigoGiftCardSerializer
    pagination_class = CodigoGiftCardPagination



@login_required
def agregar_al_carrito(request, giftcard_id):
    try:
        giftcard = GiftCard.objects.get(pk=giftcard_id)
        price_id = request.POST.get('price_id')
        precio = Price.objects.get(pk=price_id)

        try:
            carrito = request.user.carritos.get()
        except Carrito.DoesNotExist:
            carrito = Carrito.objects.create(usuario=request.user)

        # Seleccionar un código disponible que no esté ya en el carrito
        codigos_en_carrito = carrito.productos.values_list('codigo', flat=True)
        codigo_giftcard = CodigoGiftCard.objects.filter(
            tarjeta=giftcard.tarjeta,
            prices=precio,
            disponible=True
        ).exclude(codigo__in=codigos_en_carrito).first()

        if codigo_giftcard:
            carrito.productos.add(codigo_giftcard)
            messages.success(request, f"Se agregó {giftcard.name} (${precio.amount}) al carrito.")
            return redirect('mostrar_carrito')
        else:
            messages.error(request, "No hay más códigos disponibles para esta gift card y precio.")
            return redirect('mostrar_carrito')

    except GiftCard.DoesNotExist:
        messages.error(request, "La gift card no existe.")
        return redirect('mostrar_carrito')
    except Price.DoesNotExist:
        messages.error(request, "El precio no existe.")
        return redirect('mostrar_carrito')
    except Exception as e:
        print(f"An error occurred: {e}")
        messages.error(request, "Ocurrió un error. Por favor, inténtalo de nuevo más tarde.")
        return redirect('mostrar_carrito')
    
'''
@login_required
def mostrar_carrito(request):
    try:
        carrito = request.user.carritos.get()
        tasa_cambio = obtener_tasa_cambio()  # Obtener la tasa de cambio
        return render(request, 'productos/carrito.html', {'carrito': carrito, 'tasa_cambio': tasa_cambio})
    except Carrito.DoesNotExist:
        carrito = Carrito.objects.create(usuario=request.user)
        return render(request, 'productos/carrito.html', {'carrito': carrito})
'''

def mostrar_carrito(request):
    carrito = Carrito.objects.get(usuario=request.user)
    tasa_cambio = obtener_tasa_cambio()  # Asegúrate de tener la función obtener_tasa_cambio definida

    subtotal = Decimal('0.00')
    for producto in carrito.productos.all():
        precio = producto.prices.first()
        if precio:
            subtotal += precio.amount

    iva = subtotal * Decimal('0.16')
    total = subtotal + iva

    context = {
        'carrito': carrito,
        'tasa_cambio': tasa_cambio,
        'subtotal': subtotal,
        'iva': iva,
        'total': total,
    }
    return render(request, 'productos/carrito.html', context)


@login_required
def eliminar_del_carrito(request, codigo_giftcard_id):
    try:
        carrito = request.user.carritos.get()
        codigo_giftcard = CodigoGiftCard.objects.get(pk=codigo_giftcard_id)
        carrito.productos.remove(codigo_giftcard)
    except (Carrito.DoesNotExist, CodigoGiftCard.DoesNotExist):
        messages.error(request, "No se encontró el carrito o el código de gift card.") # Mensaje flash
        return redirect('mostrar_carrito') # Redirige de vuelta al carrito
    return redirect('mostrar_carrito')




def obtener_credenciales():
    """Obtiene las credenciales del modelo CredencialesBNC."""
    try:
        credenciales = CredencialesBNC.objects.first()
        return credenciales.client_guid, credenciales.master_key
    except CredencialesBNC.DoesNotExist:
        return None, None

def obtener_working_key():
    """Obtiene la WorkingKey de la API del BNC o de la caché."""
    # Aquí iría la lógica para obtener la WorkingKey de la caché o de la base de datos temporal
    # Por ahora, simularemos la obtención de la WorkingKey
    client_guid, master_key = obtener_credenciales()
    if client_guid and master_key:
        return obtener_working_key_ejemplo(client_guid, master_key)
    else:
        return None

def obtener_working_key_ejemplo(client_guid, master_key):
    """Simula la solicitud Logon y genera una WorkingKey de ejemplo."""
    # Simulación de la encriptación AES
    def encrypt_aes(data, key, iv):
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return base64.b64encode(cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))).decode('utf-8')

    # Simulación del hash SHA256
    def hash_sha256(data):
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    # Datos de ejemplo para la solicitud Logon
    logon_data = {"ClientGUID": client_guid}
    logon_data_json = json.dumps(logon_data)

    # Simulación de la encriptación y el hash
    iv = get_random_bytes(AES.block_size)
    encrypted_value = encrypt_aes(logon_data_json, master_key.encode('utf-8'), iv)
    validation_hash = hash_sha256(logon_data_json)

    # Simulación de la respuesta de la API
    response_data = {
        "status": "OK",
        "message": "000000Se ha iniciado sesión exitosamente.",
        "value": encrypted_value,
        "validation": validation_hash
    }
    #simulacion de la desencriptacion del value, para obtener la working key
    working_key = "clave_de_trabajo_de_ejemplo"

    return working_key

def procesar_pago_c2p(request, form, amount):
    """Simula el procesamiento de un pago C2P."""
    working_key = obtener_working_key()
    if working_key:
        id_transaction, reference = realizar_pago_c2p_ejemplo(
            working_key, form.cleaned_data['bank_code'],
            form.cleaned_data['debtor_cellphone'], form.cleaned_data['debtor_id'],
            amount, form.cleaned_data['token'], "15015840"
        )
        return reference, id_transaction
    else:
        raise Exception("Credenciales no configuradas.")

def realizar_pago_c2p_ejemplo(working_key, debtor_bank_code, debtor_cellphone, debtor_id, amount, token, terminal):
    """Simula la solicitud SendC2P y procesa el pago."""
    # Simulación de la encriptación AES
    def encrypt_aes(data, key, iv):
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return base64.b64encode(cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))).decode('utf-8')

    # Simulación del hash SHA256
    def hash_sha256(data):
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    # Datos de ejemplo para la solicitud SendC2P
    c2p_data = {
        "DebtorBankCode": debtor_bank_code,
        "DebtorCellPhone": debtor_cellphone,
        "DebtorID": debtor_id,
        "Amount": amount,
        "Token": token,
        "Terminal": terminal
    }
    c2p_data_json = json.dumps(c2p_data)

    # Simulación de la encriptación y el hash
    iv = get_random_bytes(AES.block_size)
    encrypted_value = encrypt_aes(c2p_data_json, working_key.encode('utf-8'), iv)
    validation_hash = hash_sha256(c2p_data_json)

    # Simulación de la respuesta de la API
    response_data = {
        "status": "OK",
        "message": "000000C2P procesado por un monto de 101.00, Nro de Referencia: 123456",
        "value": encrypted_value,
        "validation": validation_hash
    }
    #simulacion de la desencriptacion del value, para obtener el idtransaction y la referencia.
    id_transaction = "7891011"
    reference = "123456"

    return id_transaction, reference

class DecimalEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

@login_required
def procesar_compra(request):
    try:
        carrito = request.user.carritos.get()
        if not carrito.productos.exists():
            messages.error(request, "Tu carrito está vacío.")
            return redirect('mostrar_carrito')

        detalles_compra = []
        monto_total = 0
        codigos_utilizados = []
        giftcards_compradas = []

        with transaction.atomic():
            for codigo_giftcard in carrito.productos.all():
                giftcard = codigo_giftcard.tarjeta.giftcard
                price = codigo_giftcard.prices.first()
                monto = price.amount

                detalles_compra.append({
                    'nombre': giftcard.name,
                    'monto': str(monto),  # Convertir Decimal a str
                })
                codigos_utilizados.append(codigo_giftcard.codigo)
                giftcards_compradas.append(giftcard)
                monto_total += monto

                codigo_giftcard.disponible = False
                codigo_giftcard.usado = True
                codigo_giftcard.usuario_asociado = request.user
                codigo_giftcard.fecha_uso = timezone.now()
                codigo_giftcard.save()

            transaccion = Transaction.objects.create(
                metodo_pago='ficticio',  # Usamos 'ficticio' como marcador de posición
                monto=monto_total,
                usuario=request.user,
                codigo=codigos_utilizados[0]
            )

            compra = Compra.objects.create(
                usuario=request.user,
                transaction=transaccion,
                codigos_giftcard=codigos_utilizados,
                detalles_compra=json.dumps(detalles_compra, cls=DecimalEncoder),  # Serializar con DecimalEncoder
                monto_pagado=str(monto_total)  # Convertir Decimal a str
            )
            compra.giftcards.set(giftcards_compradas)

            carrito.productos.clear()

            messages.success(request, "¡Compra realizada con éxito!")
            return redirect(reverse('mostrar_recibo', args=[compra.id]))

    except Carrito.DoesNotExist:
        messages.error(request, "No tienes un carrito.")
        return redirect('mostrar_carrito')

    except Exception as e:
        print(f"Error en procesar_compra: {e}")
        messages.error(request, "Ocurrió un error durante la compra. Inténtalo de nuevo más tarde.")
        return render(request, 'productos/pago_fallido.html', {
            'error': 'Ocurrió un error durante la compra. Inténtalo de nuevo más tarde.'
        })


class MetodoPagoView(View):
    def get(self, request, metodo):
        try:
            carrito = request.user.carritos.get()
            if not carrito.productos.exists():
                messages.error(request, "Tu carrito está vacío.")
                return redirect('mostrar_carrito')

            items = [
                {
                    'giftcard': codigo_giftcard.tarjeta.giftcard,
                    'price': codigo_giftcard.prices.first()
                }
                for codigo_giftcard in carrito.productos.all()
            ]
            tasa_cambio = 1 # Simulación de la tasa de cambio

            post_virtual_form = PagoPostVirtualForm()
            pago_movil_form = PagoMovilForm()
            pago_c2p_form = PagoC2PForm()

            return render(request, 'productos/metodo_pago.html', {
                'items': items,
                'metodo': metodo,
                'tasa_cambio': tasa_cambio,
                'post_virtual_form': post_virtual_form,
                'pago_movil_form': pago_movil_form,
                'pago_c2p_form': pago_c2p_form,
            })
        except Carrito.DoesNotExist:
            messages.error(request, "No tienes un carrito.")
            return redirect('mostrar_carrito')

    def post(self, request, metodo):
        try:
            carrito = request.user.carritos.get()
            if not carrito.productos.exists():
                messages.error(request, "Tu carrito está vacío.")
                return redirect('mostrar_carrito')

            detalles_compra = []
            monto_total = 0
            codigos_utilizados = []
            giftcards_compradas = []

            with transaction.atomic():
                for codigo_giftcard in carrito.productos.all():
                    giftcard = codigo_giftcard.tarjeta.giftcard
                    price = codigo_giftcard.prices.first()

                    if metodo == 'pago_movil':
                        pago_movil_form = PagoMovilForm(request.POST)
                        if pago_movil_form.is_valid():
                            monto = price.amount
                            monto_total += monto
                            detalles_compra.append({
                                'nombre': giftcard.name,
                                'monto': monto,
                            })
                            codigos_utilizados.append(codigo_giftcard.codigo)
                            giftcards_compradas.append(giftcard)

                            codigo_giftcard.disponible = False
                            codigo_giftcard.usado = True
                            codigo_giftcard.usuario_asociado = request.user
                            codigo_giftcard.fecha_uso = timezone.now()
                            codigo_giftcard.save()

                    elif metodo == 'pago_c2p':
                        pago_c2p_form = PagoC2PForm(request.POST)
                        if pago_c2p_form.is_valid():
                            monto = price.amount
                            monto_total += monto
                            detalles_compra.append({
                                'nombre': giftcard.name,
                                'monto': monto,
                            })
                            codigos_utilizados.append(codigo_giftcard.codigo)
                            giftcards_compradas.append(giftcard)

                            codigo_giftcard.disponible = False
                            codigo_giftcard.usado = True
                            codigo_giftcard.usuario_asociado = request.user
                            codigo_giftcard.fecha_uso = timezone.now()
                            codigo_giftcard.save()

                    elif metodo == 'post_virtual':
                        post_virtual_form = PagoPostVirtualForm(request.POST)
                        if post_virtual_form.is_valid():
                            monto = price.amount
                            monto_total += monto
                            detalles_compra.append({
                                'nombre': giftcard.name,
                                'monto': monto,
                            })
                            codigos_utilizados.append(codigo_giftcard.codigo)
                            giftcards_compradas.append(giftcard)

                            codigo_giftcard.disponible = False
                            codigo_giftcard.usado = True
                            codigo_giftcard.usuario_asociado = request.user
                            codigo_giftcard.fecha_uso = timezone.now()
                            codigo_giftcard.save()

                transaccion = Transaction.objects.create(
                    metodo_pago=metodo,
                    monto=monto_total,
                    usuario=request.user,
                    codigo=codigos_utilizados[0]
                )

                compra = Compra.objects.create(
                    usuario=request.user,
                    transaction=transaccion,
                    codigos_giftcard=codigos_utilizados,
                    detalles_compra=detalles_compra,
                    monto_pagado=monto_total
                )
                compra.giftcards.set(giftcards_compradas)

                carrito.productos.clear()

                messages.success(request, "¡Compra realizada con éxito!")
                return redirect(reverse('mostrar_recibo', args=[compra.id]))

        except Carrito.DoesNotExist:
            messages.error(request, "No tienes un carrito.")
            return redirect('mostrar_carrito')

        except Exception as e:
            print(f"Error en MetodoPagoView: {e}")
            messages.error(request, "Ocurrió un error durante la compra. Inténtalo de nuevo más tarde.")
            return render(request, 'productos/pago_fallido.html', {
                'error': 'Ocurrió un error durante la compra. Inténtalo de nuevo más tarde.'
            })
        

'''def mostrar_recibo(request, compra_id):
    compra = Compra.objects.get(id=compra_id)
    # Usar detalles_compra directamente, ya que contiene nombre, código y monto
    detalles_con_codigos = compra.detalles_compra if compra.detalles_compra else []
    
    return render(request, 'productos/recibo.html', {
        'compra': compra,
        'detalles_con_codigos': detalles_con_codigos,
    })
'''
#temporal:

def mostrar_recibo(request, compra_id):
    compra = get_object_or_404(Compra, pk=compra_id)
    detalles_con_codigos = json.loads(compra.detalles_compra) if compra.detalles_compra else []
    tasa_cambio = obtener_tasa_cambio()

    subtotal = Decimal('0.00')
    for detalle in detalles_con_codigos:
        subtotal += Decimal(detalle['monto'])

    iva = subtotal * Decimal('0.16')
    total = subtotal + iva

    context = {
        'compra': compra,
        'detalles_con_codigos': detalles_con_codigos,
        'tasa_cambio': tasa_cambio,
        'subtotal': subtotal,
        'iva': iva,
        'total': total,
    }
    return render(request, 'productos/recibo.html', context)

def imprimir_recibo(request, compra_id):
    compra = get_object_or_404(Compra, pk=compra_id)
    detalles_compra = compra.detalles_compra if compra.detalles_compra else []

    detalles_con_codigos = []
    subtotal = Decimal('0.00')

    for detalle in detalles_compra:
        detalle_con_codigo = {
            'nombre': detalle['nombre'],
            'codigo': compra.codigos_giftcard[detalles_compra.index(detalle)],
            'monto': Decimal(detalle['monto']),
        }
        detalles_con_codigos.append(detalle_con_codigo)
        subtotal += Decimal(detalle['monto'])

    iva = subtotal * Decimal('0.16')
    total = subtotal + iva

    tasa_cambio = obtener_tasa_cambio()

    context = {
        'compra': compra,
        'detalles_con_codigos': detalles_con_codigos,
        'tasa_cambio': tasa_cambio,
        'subtotal': subtotal,
        'iva': iva,
        'total': total,
    }
    return render(request, 'productos/recibo_impresion.html', context)


#tasa de cambio:

def obtener_tasa_cambio():
    """Obtiene la tasa de cambio de USD a VES desde ExchangeRate-API."""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        response.raise_for_status()
        data = response.json()
        tasa_cambio = Decimal(data['rates']['VES'])
        return tasa_cambio
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener la tasa de cambio: {e}")
        return Decimal(1) # Valor por defecto.
    except (KeyError, ValueError) as e:
        print(f"Error al procesar la respuesta de ExchangeRate-API: {e}")
        return Decimal(1) # Valor por defecto.
    

def playstation_giftcards(request):
    giftcards = GiftCard.objects.filter(tipo='playstation')
    tasa_cambio = obtener_tasa_cambio()
    return render(request, 'productos/playstation_giftcards.html', {'giftcards': giftcards, 'tasa_cambio': tasa_cambio})

def nintendo_giftcards(request):
    giftcards = GiftCard.objects.filter(tipo='nintendo')
    tasa_cambio = obtener_tasa_cambio()
    return render(request, 'productos/nintendo_giftcards.html', {'giftcards': giftcards, 'tasa_cambio': tasa_cambio})

def steam_giftcards(request):
    giftcards = GiftCard.objects.filter(tipo='steam')
    tasa_cambio = obtener_tasa_cambio()
    return render(request, 'productos/steam_giftcards.html', {'giftcards': giftcards, 'tasa_cambio': tasa_cambio})

def itunes_giftcards(request):
    giftcards = GiftCard.objects.filter(tipo='itunes')
    tasa_cambio = obtener_tasa_cambio()
    return render(request, 'productos/itunes_giftcards.html', {'giftcards': giftcards, 'tasa_cambio': tasa_cambio})

def xbox_giftcards(request):
    giftcards = GiftCard.objects.filter(tipo='xbox')
    tasa_cambio = obtener_tasa_cambio()
    return render(request, 'productos/xbox_giftcards.html', {'giftcards': giftcards, 'tasa_cambio': tasa_cambio})

def roblox_giftcards(request):
    giftcards = GiftCard.objects.filter(tipo='roblox')
    tasa_cambio = obtener_tasa_cambio()
    return render(request, 'productos/roblox_giftcards.html', {'giftcards': giftcards, 'tasa_cambio': tasa_cambio})

def google_play_giftcards(request):
    giftcards = GiftCard.objects.filter(tipo='google_play')
    tasa_cambio = obtener_tasa_cambio()
    return render(request, 'productos/google_play_giftcards.html', {'giftcards': giftcards, 'tasa_cambio': tasa_cambio}) 


