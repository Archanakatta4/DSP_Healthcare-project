from cryptography.fernet import Fernet

# Encryption key (must be stored securely)
key = Fernet.generate_key()
cipher = Fernet(key)

def encrypt_data(data):
    return cipher.encrypt(data.encode()).decode()
def decrypt_data(encrypted_data):
    return cipher.decrypt(encrypted_data.encode()).decode()
