import hashlib
import logging
import typing

from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.crypto import constant_time_compare, get_random_string
from rest_framework_api_key.crypto import KeyGenerator


class Sha256ApiKeyHasher(BasePasswordHasher):
    algorithm = "sha256"

    def salt(self) -> str:
        return get_random_string(12)

    def encode(self, password: str, salt: str) -> str:
        hash_input = (salt + password).encode()
        hash_result = hashlib.sha256(hash_input).hexdigest()
        return f"{self.algorithm}${salt}${hash_result}"

    def verify(self, password: str, encoded: str) -> bool:
        _, salt, _ = encoded.split("$", 2)
        new_encoded = self.encode(password, salt)
        # Using constant_time_compare to prevent timing attacks
        return constant_time_compare(encoded, new_encoded)


class CustomAPIKeyGenerator(KeyGenerator):
    preferred_hasher = Sha256ApiKeyHasher()

    def __init__(self, prefix_length: int = 4, secret_key_length: int = 32):
        self.prefix_length = prefix_length
        self.secret_key_length = secret_key_length

    def get_prefix(self) -> str:
        random_part = get_random_string(self.prefix_length)
        return f"datbar_{random_part}"  # Cool prefix

    def get_secret_key(self) -> str:
        return get_random_string(self.secret_key_length)

    def hash(self, value: str) -> str:
        return self.preferred_hasher.encode(value, self.preferred_hasher.salt())

    def generate(self) -> typing.Tuple[str, str, str]:
        prefix = self.get_prefix()
        secret_key = self.get_secret_key()
        key = f"{prefix}.{secret_key}"
        hashed_key = self.hash(key)
        return key, prefix, hashed_key

    def verify(self, key: str, hashed_key: str) -> bool:
        if self.using_preferred_hasher(hashed_key):
            result = self.preferred_hasher.verify(key, hashed_key)
        else:
            logging.warning(
                "Received API key with unsupported hasher. Rejecting for security reasons.",
                extra={"hashed_key": hashed_key},
            )
            return False  # If the hasher is not preferred, we consider it invalid. You can implement fallback logic here if needed.

        return result

    def using_preferred_hasher(self, hashed_key: str) -> bool:
        return hashed_key.startswith(f"{self.preferred_hasher.algorithm}$")
