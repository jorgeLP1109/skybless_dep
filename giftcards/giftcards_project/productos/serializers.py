# serializers.py
from rest_framework import serializers
from .models import Carrito, CodigoGiftCard

class CodigoGiftCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodigoGiftCard
        fields = '__all__'

class CarritoSerializer(serializers.ModelSerializer):
    productos = CodigoGiftCardSerializer(many=True, read_only=True)

    class Meta:
        model = Carrito
        fields = ['id', 'usuario', 'productos', 'fecha_creacion', 'total']
        read_only_fields = ['usuario', 'fecha_creacion', 'total']