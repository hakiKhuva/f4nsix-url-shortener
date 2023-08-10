import hashlib


def generate_secure_string(api_key_or_string):
    """
    generate and return the secure string of api key or any other string
    """
    return hashlib.sha512(api_key_or_string.encode()).hexdigest()