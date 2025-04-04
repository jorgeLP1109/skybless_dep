from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.models import User






class UsuarioManager(BaseUserManager):  # Custom Manager
    def create_user(self, username, password=None, **extra_fields):
        # Ensure username is lowercase
        username = self.normalize_email(username)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        username = self.normalize_email(username)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        user = self.create_user(username, password, **extra_fields)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, username):
        return self.get(username__iexact=username) # Case-insensitive lookup

class Usuario(AbstractUser):
    es_administrador = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    objects = UsuarioManager()  # Use the custom manager
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None

    def __str__(self):
        return self.username


class Price(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    habilitado = models.BooleanField(default=True)  # Nuevo campo para habilitar/deshabilitar precios

    def __str__(self):
        return f"${self.amount} ({'Habilitado' if self.habilitado else 'Deshabilitado'})"

class Tarjeta(models.Model):
    name = models.CharField(max_length=100)
    # Otros campos si es necesario

    def __str__(self):
        return self.name    



class GiftCard(models.Model):
    name = models.CharField(max_length=100)
    estado = models.CharField(
        max_length=20,
        choices=[('disponible', 'Disponible'), ('vendida', 'Vendida')],
        default='disponible',
    )
    description = models.TextField()
    image = models.ImageField(upload_to='giftcards/')
    tarjeta = models.OneToOneField(Tarjeta, on_delete=models.CASCADE, related_name='giftcard')
    imagen_vendida = models.ImageField(upload_to='giftcards/vendidas/', null=True, blank=True)
    prices = models.ManyToManyField(Price, related_name='giftcards')
    tipo = models.CharField(
        max_length=50,
        choices=[
            ('playstation', 'PlayStation Gift Card USA'),
            ('nintendo', 'Nintendo Gift Card USA'),
            ('steam', 'STEAM USA'),
            ('itunes', 'ITUNES USA'),
            ('xbox', 'XBOX USA'),
            ('roblox', 'ROBLOX'),
            ('google_play', 'GOOGLE PLAY'),
        ],
        default='playstation',  # Puedes establecer un valor predeterminado
    )

    def obtener_imagen(self):
        """Devuelve la imagen según el estado."""
        return self.imagen_vendida if self.estado == 'vendida' else self.image

    def __str__(self):
        return self.name


class Compra(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    giftcards = models.ManyToManyField(GiftCard)  # ManyToMany relationship
    fecha_compra = models.DateTimeField(auto_now_add=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    transaction = models.OneToOneField('Transaction', on_delete=models.CASCADE, null=True, blank=True)
    codigos_giftcard = models.JSONField(null=True, blank=True)
    detalles_compra = models.JSONField(null=True, blank=True)

    def __str__(self):
        giftcard_names = ", ".join([giftcard.name for giftcard in self.giftcards.all()])
        return f"{self.usuario.username} - {giftcard_names}"

class Pago(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=[
        ('paypal', 'PayPal'),
        ('tarjeta', 'Tarjeta de Crédito'),
        ('transferencia', 'Transferencia Bancaria')
    ])
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido')
    ], default='pendiente')
    transaccion_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.metodo} - {self.estado} - {self.usuario.username}"
    
class MetodoPago(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    logo = models.ImageField(upload_to='metodos_pago/', null=True, blank=True)

    def __str__(self):
        return self.nombre
    
class Transaction(models.Model):
    metodo_pago = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=100, blank=True, null=True)  # Código de la giftcard o token
    fecha_transaccion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} - {self.metodo_pago} - {self.codigo}"    
    
class CarouselImage(models.Model):
    title = models.CharField(max_length=100, blank=True, null=True, verbose_name="Título")
    image = models.ImageField(upload_to='carousel_images/', verbose_name="Imagen del carrusel")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title if self.title else f"Imagen {self.id}"    
    



class CodigoEnviado(models.Model):
    codigo = models.CharField(max_length=255)  # Removed unique=True
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Changed to ForeignKey
    fecha_envio = models.DateTimeField(auto_now_add=True)
    
    

    def __str__(self):
        return self.codigo



class CodigoGiftCard(models.Model):
    tarjeta = models.ForeignKey(Tarjeta, on_delete=models.CASCADE, related_name='codigos')
    codigo = models.CharField(max_length=255, unique=True)
    disponible = models.BooleanField(default=True)
    usado = models.BooleanField(default=False)
    usuario_asociado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_uso = models.DateTimeField(null=True, blank=True)
    prices = models.ManyToManyField('Price', related_name='codigos') # Relación con Price

    def __str__(self):
        return self.codigo




class CodigoGiftCardHistorial(models.Model):
    tarjeta = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    codigo = models.CharField(max_length=100)
    usuario_asociado = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    fecha_uso = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tarjeta} - {self.price} - {self.codigo}"    
    
class JuegoRecarga(models.Model):
    nombre = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='juegos/')
    monto = models.JSONField(help_text="Lista de montos disponibles en formato JSON (e.g., [5, 10, 20])")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre  

    
class Carrito(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carritos')
    productos = models.ManyToManyField('CodigoGiftCard', related_name='carritos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

    def total(self):
        total = 0
        for producto in self.productos.all():
            precio = producto.prices.first()  # Asumiendo un precio por producto
            if precio:
                total += precio.amount
        return total
    
class CredencialesBNC(models.Model):
    client_guid = models.CharField(max_length=36)
    master_key = models.CharField(max_length=255)

    def __str__(self):
        return "Credenciales BNC"

    
    