import requests
import json
from .crypto_utils import ChiperCrypto

def enviar_peticion_api(url, client_guid, master_key, value, sw_test_operation=False):
    """Envía una petición a la API del banco."""

    crypto = ChiperCrypto(master_key)
    value_json = json.dumps(value)
    validation = crypto.HashGUID(value_json)
    value_encriptado = crypto.Encryptar(value_json)

    payload = {
        "ClientGUID": client_guid,
        "Reference": "",
        "Value": value_encriptado,
        "Validation": validation,
        "swTestOperation": sw_test_operation,
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Lanza una excepción para códigos de error HTTP
        respuesta_api = response.json()

        if respuesta_api["status"] == "OK":
            value_desencriptado = crypto.Desencryptar(respuesta_api["value"])
            respuesta_valor = json.loads(value_desencriptado)
            return respuesta_valor
        else:
            raise Exception(respuesta_api["message"])

    except requests.exceptions.RequestException as e:
        raise Exception(f"Error al conectar con la API: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"Error al decodificar la respuesta JSON: {e}")
    except Exception as e:
        raise Exception(f"Error en la API: {e}")
    

def procesar_pago_movil(request, form, monto):
    """Procesa el pago móvil."""

    client_guid = "TU_CLIENT_GUID"  # Reemplaza con tu ClientGUID
    master_key = "TU_MASTER_KEY"  # Reemplaza con tu Master Key
    url_api = "https://tu-api-banco.com/Api/MobPayment/SendP2P"  # Reemplaza con la URL de la API

    telefono = form.cleaned_data["telefono"]
    banco = form.cleaned_data["banco"]

    payload = {
        "Amount": str(monto),
        "BeneficiaryBankCode": banco,  # Ajusta según los códigos de banco del BNC
        "BeneficiaryCellPhone": telefono,
        "BeneficiaryEmail": request.user.email,  # Opcional
        "BeneficiaryID": request.user.username,  # Opcional
        "BeneficiaryName": request.user.first_name,  # Opcional
        "BranchID": "SUCURSAL",  # Opcional
        "ChildClientID": request.user.username,  # Opcional
        "Description": "Compra de giftcard",  # Opcional
        "OperationRef": "",  # Opcional
    }

    try:
        respuesta_api = enviar_peticion_api(url_api, client_guid, master_key, payload)
        return respuesta_api["Reference"], respuesta_api["AuthorizationCode"]
    except Exception as e:
        raise Exception(f"Error al procesar el pago móvil: {e}")


def procesar_pago_c2p(request, form, monto):
    """Procesa el pago C2P."""

    client_guid = "TU_CLIENT_GUID"  # Reemplaza con tu ClientGUID
    master_key = "TU_MASTER_KEY"  # Reemplaza con tu Master Key
    url_api = "https://tu-api-banco.com/Api/MobPayment/SendC2P"  # Reemplaza con la URL de la API

    telefono = form.cleaned_data["telefono"]
    banco = form.cleaned_data["banco"]
    terminal = form.cleaned_data["terminal"]
    token = form.cleaned_data["token"]

    payload = {
        "Amount": str(monto),
        "BranchID": "SUCURSAL",  # Opcional
        "ChildClientID": request.user.username,  # Opcional
        "DebtorBankCode": banco,  # Ajusta según los códigos de banco del BNC
        "DebtorCellPhone": telefono,
        "DebtorID": request.user.username,
        "Terminal": terminal,
        "Token": token,
    }

    try:
        respuesta_api = enviar_peticion_api(url_api, client_guid, master_key, payload)
        return respuesta_api["Reference"], respuesta_api["IdTransaction"]
    except Exception as e:
        raise Exception(f"Error al procesar el pago C2P: {e}")        

