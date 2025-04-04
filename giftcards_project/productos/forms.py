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

class PagoMovilForm(forms.Form):
    telefono = forms.CharField(max_length=11)
    banco = forms.CharField(max_length=50) # Puedes usar un ChoiceField para los bancos     



class PagoC2PForm(forms.Form):
    debtor_id = forms.CharField(label='Cédula', max_length=20)
    debtor_cellphone = forms.CharField(label='Teléfono', max_length=15)
    bank_code = forms.IntegerField(label='Banco')
    token = forms.CharField(label='Token', max_length=8)