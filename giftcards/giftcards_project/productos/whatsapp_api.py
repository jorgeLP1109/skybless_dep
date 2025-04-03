import requests
import json
from datetime import datetime

# Token de acceso y URL de la API
WHATSAPP_API_URL = "https://graph.facebook.com/v21.0/527935020403320/messages"
ACCESS_TOKEN = "EAASeIk75X0sBO4YZBsGipZCsUjFXcDzcSiWV0Il0ZBZAG5cfVLzp33UD1Vbifc7VbD315dQEkqEKtH0pXQzijNeGyRJX8y6NB5gQXzG82haKRA04ZCHYeodXVBOi3f1Svz1aRY268BZCPOKR5C7hEWSzIxoXyKJB0e0GL6uuYhYTxoP30V58KLXz921qavH6WFgWbPO9zyy4IDvh9qCn08ZCuTw"
NUMERO_RECEPTOR_FIJO = "584129368715"  # Número receptor fijo (en formato internacional, sin el '+' inicial)

def enviar_mensaje_whatsapp(usuario_id, juego, monto, jugador_id, numero_receptor):
    # Datos a enviar
    mensaje = (
        f"Recarga solicitada:\n"
        f"- Usuario ID: {usuario_id}\n"
        f"- Juego: {juego}\n"
        f"- Monto: ${monto}\n"
        f"- ID del Jugador: {jugador_id}\n"
        f"- Fecha y Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero_receptor,  # Usar el número receptor fijo aquí
        "type": "text",
        "text": {"body": mensaje},
    }

    # Enviar solicitud POST a la API
    response = requests.post(WHATSAPP_API_URL, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        print("Mensaje enviado correctamente")
    else:
        print(f"Error al enviar mensaje: {response.status_code} - {response.text}")

    return response
