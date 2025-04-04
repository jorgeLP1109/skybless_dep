from django.contrib import admin
from django import forms
from django.urls import path
from django.http import HttpResponseRedirect
from django.shortcuts import render
import json
from .models import Usuario, GiftCard, Compra, Price, CarouselImage, CodigoGiftCard, CodigoGiftCardHistorial, JuegoRecarga, Tarjeta
from .models import CodigoEnviado
from .filters import CodigoEnviadoFilter
from django.urls import reverse
from .models import CredencialesBNC

admin.site.register(CredencialesBNC)



@admin.register(JuegoRecarga)
class JuegoRecargaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion')
    search_fields = ('nombre',)


@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at')
    ordering = ('-created_at',)


admin.site.register(Usuario)
admin.site.register(Compra)


# Admin para el modelo Price
@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('amount', 'habilitado')
    list_editable = ('habilitado',)


# Admin para el modelo GiftCard
@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = ("name", "get_monto", "estado")  
    list_filter = ('estado',)
    actions = ['marcar_como_vendida']
    filter_horizontal = ("prices",)

    def get_monto(self, obj):
        """Devuelve el primer precio de la lista de precios asociados."""
        return obj.prices.first().amount if obj.prices.exists() else "No disponible"
    get_monto.short_description = 'Monto'  

    @admin.action(description="Marcar como vendida")
    def marcar_como_vendida(self, request, queryset):
        queryset.update(estado='vendida')

        for giftcard in queryset:
            giftcard.imagen_vendida = f"giftcards/vendidas/{giftcard.id}_vendida.png"
            giftcard.save()




class CargarCodigosForm(forms.Form):
    archivo_json = forms.FileField()

@admin.register(CodigoGiftCard)
class CodigoGiftCardAdmin(admin.ModelAdmin):
    list_per_page = 1000
    list_display = ('codigo', 'tarjeta', 'disponible', 'usado', 'usuario_asociado', 'fecha_uso')
    list_filter = ('tarjeta', 'disponible', 'usado')
    search_fields = ('codigo', 'tarjeta__name', 'usuario_asociado__username')
    actions = ['marcar_como_usado']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(usado=False) # Only show unused codes

    @admin.action(description="Marcar como usado")
    def marcar_como_usado(self, request, queryset):
        for codigo_giftcard in queryset:
            if codigo_giftcard.disponible and not codigo_giftcard.usado:
                codigo_giftcard.usado = True
                codigo_giftcard.disponible = False
                codigo_giftcard.save()

                # Create a history record
                CodigoGiftCardHistorial.objects.create(
                    tarjeta=codigo_giftcard.tarjeta.name,
                    price=codigo_giftcard.prices.first().amount if codigo_giftcard.prices.exists() else 0, # get the price or 0
                    codigo=codigo_giftcard.codigo,
                    usuario_asociado=codigo_giftcard.usuario_asociado,
                    fecha_uso=codigo_giftcard.fecha_uso
                )

        self.message_user(request, "Códigos marcados como usados y historial creado.")

#cargar tarjetas anterior !!!!
#//////////////////////////////////////////////////////////////////
    '''def cargar_codigos(self, request):
        if request.method == "POST":
            form = CargarCodigosForm(request.POST, request.FILES)
            if form.is_valid():
                archivo = request.FILES["archivo_json"]
                datos = json.load(archivo)

                for item in datos:
                    nombre = item["nombre"]
                    montos = item["monto"]  # Assuming monto is a list of prices
                    codigo = item["codigo"]

                    tarjeta, created = Tarjeta.objects.get_or_create(name=nombre)

                    try:
                        codigo_giftcard = CodigoGiftCard.objects.get(codigo=codigo)
                        # Si el código existe, actualizarlo
                        codigo_giftcard.tarjeta = tarjeta
                        codigo_giftcard.disponible = True  # Asegurar que esté disponible
                        codigo_giftcard.usado = False  # Asegurar que no esté usado
                        codigo_giftcard.save()
                    except CodigoGiftCard.DoesNotExist:
                        # Si no existe, crearlo
                        codigo_giftcard = CodigoGiftCard.objects.create(tarjeta=tarjeta, codigo=codigo)

                    # Add the prices (assuming they exist as Price objects)
                    for monto in montos:
                        try:  # Handle potential Price.DoesNotExist error
                            price = Price.objects.get(amount=monto)  # Get the Price object
                            codigo_giftcard.prices.add(price)
                        except Price.DoesNotExist:
                            # Handle the case where the price doesn't exist
                            print(f"Price with amount {monto} not found.")

                self.message_user(request, "Códigos cargados exitosamente.")
                return HttpResponseRedirect("../")

        else:
            form = CargarCodigosForm()

        return render(request, "admin/cargar_codigos.html", {"form": form})
 '''   
    
#/////////////////////////////////////////////////////////////////    

def cargar_codigos(self, request):
    if request.method == "POST":
        form = CargarCodigosForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES["archivo_json"]
            datos = json.load(archivo)

            for item in datos:
                nombre = item["nombre"]
                montos = item["monto"]
                codigo = item["codigo"]

                try:
                    tarjeta = Tarjeta.objects.get(name=nombre)  # Obtener la tarjeta existente
                except Tarjeta.DoesNotExist:
                    self.message_user(request, f"La tarjeta '{nombre}' no existe. Códigos no cargados.", level="ERROR")
                    return HttpResponseRedirect("../")  # Redirigir con error

                try:
                    codigo_giftcard = CodigoGiftCard.objects.get(codigo=codigo)
                    codigo_giftcard.tarjeta = tarjeta
                    codigo_giftcard.disponible = True
                    codigo_giftcard.usado = False
                    codigo_giftcard.save()
                except CodigoGiftCard.DoesNotExist:
                    codigo_giftcard = CodigoGiftCard.objects.create(tarjeta=tarjeta, codigo=codigo)

                for monto in montos:
                    try:
                        price = Price.objects.get(amount=monto)
                        codigo_giftcard.prices.add(price)
                    except Price.DoesNotExist:
                        print(f"Price with amount {monto} not found.")

            self.message_user(request, "Códigos cargados exitosamente.")
            return HttpResponseRedirect("../")

    else:
        form = CargarCodigosForm()

    return render(request, "admin/cargar_codigos.html", {"form": form})



@admin.register(CodigoEnviado)
class CodigoEnviadoAdmin(admin.ModelAdmin):
    list_filter = ('fecha_envio', 'usuario', 'codigo')
    search_fields = ('codigo', 'usuario__username')
      # Si tienes un campo ManyToMany con productos
    # Usa Django Filters para filtros más avanzados
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return CodigoEnviadoFilter(request.GET, queryset=qs).qs
    
    def imprimir_reporte(self, request, queryset):
        # Guarda los filtros aplicados en la sesión
        request.session['reporte_codigos_ids'] = list(queryset.values_list('id', flat=True))
        return HttpResponseRedirect(reverse('imprimir_reporte'))  # Redirige a la vista

    imprimir_reporte.short_description = "Imprimir reporte seleccionado"  # Texto del botón
    imprimir_reporte.actions = ['imprimir_reporte']  # Registra la acción


    