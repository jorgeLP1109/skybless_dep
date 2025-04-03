from django import forms
from .models import GiftCard
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Usuario



class CompraGiftCardForm(forms.Form):
    giftcard = forms.ModelChoiceField(queryset=GiftCard.objects.filter(estado='disponible'), label="Selecciona una Gift Card")

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Usuario  # Usamos el modelo personalizado
        fields = ['username', 'email', 'first_name', 'last_name','avatar']


class PagoPostVirtualForm(forms.Form):
    numero_tarjeta = forms.CharField(max_length=16)
    fecha_vencimiento = forms.CharField(max_length=4)
    cvv = forms.CharField(max_length=3)

BANCOS = (
    ('BNC', 'Banco Nacional de Crédito'),
    ('Mercantil', 'Banco Mercantil'),
    ('Venezuela', 'Banco de Venezuela'),
    # Agrega otros bancos según sea necesario
)

class PagoMovilForm(forms.Form):
    banco = forms.ChoiceField(choices=BANCOS)
    telefono = forms.CharField(max_length=20)
    referencia = forms.CharField(max_length=50)  

class PagoC2PForm(forms.Form):
    telefono = forms.CharField(max_length=11)
    banco = forms.CharField(max_length=50)
    terminal = forms.CharField(max_length=8)
    token = forms.CharField(max_length=8)       