import hashlib

import bcrypt


def hash_password(plain_text_password: str) -> bytes:
    # first we convert string to bytes
    password_bytes = plain_text_password.encode('utf-8')

    # generate salt
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password

def compare_password(pt_pass: str, hpass: bytes) -> bool:
    password_bytes = pt_pass.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hpass)

def sha_hash(code: str) -> str:
    digest = hashlib.sha256(
        code.encode()
    ).hexdigest()
    return digest