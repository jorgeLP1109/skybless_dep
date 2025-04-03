import django_filters
from .models import CodigoEnviado


class CodigoEnviadoFilter(django_filters.FilterSet):
    fecha_envio_min = django_filters.DateTimeFilter(field_name='fecha_envio', lookup_expr='gte')
    fecha_envio_max = django_filters.DateTimeFilter(field_name='fecha_envio', lookup_expr='lte')
    
    
    # Agrega filtros para otros campos (producto, monto, etc.)
    # Ejemplo para un campo 'monto' en tu modelo:
    # monto = django_filters.NumberFilter(field_name='monto')

    class Meta:
        model = CodigoEnviado
        fields = ['codigo', 'usuario', 'fecha_envio']  # Campos para filtrar