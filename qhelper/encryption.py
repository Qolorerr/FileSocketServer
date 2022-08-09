from cryptography.fernet import Fernet


def init_encryption() -> None:
    global cipher
    cipher = Fernet(bytes(open("db/key.txt", 'r').read().encode("UTF-8")))


def encryption(text) -> str:
    return cipher.encrypt(bytes(text, encoding='utf-8')).decode('UTF-8')


def decryption(enc_text) -> str:
    return cipher.decrypt(bytes(enc_text, encoding='utf-8')).decode('UTF-8')
