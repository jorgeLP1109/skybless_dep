import base64
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad #Import unpad too.
import hashlib

class ChiperCrypto:
    def __init__(self, master_key):
        self.master_key = master_key
        self.salt = b'salt'  # Puedes usar un salt más seguro y almacenarlo de forma segura
        self.key = PBKDF2(self.master_key, self.salt, dkLen=32)
        self.iv = PBKDF2(self.master_key, self.salt, dkLen=16)[:16]

    def Encryptar(self, texto):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        texto_bytes = pad(texto.encode('utf-8'), AES.block_size)
        texto_encriptado = cipher.encrypt(texto_bytes)
        return base64.b64encode(texto_encriptado).decode('utf-8')

    def Desencryptar(self, texto_encriptado_base64):
        texto_encriptado = base64.b64decode(texto_encriptado_base64)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        texto_bytes = cipher.decrypt(texto_encriptado)
        texto_desencriptado = pad.unpad(texto_bytes, AES.block_size).decode('utf-8')
        return texto_desencriptado

    def HashGUID(self, guid):
        return hashlib.sha256(guid.encode('utf-8')).hexdigest()