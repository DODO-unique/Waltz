import hashlib

import bcrypt

from mvp_1.log.logger import get_logger

logger = get_logger("security.hashing")

logger.debug("security.hashing module loaded")


def hash_password(plain_text_password: str) -> bytes:
    logger.debug("hash_password called")
    # first we convert string to bytes
    password_bytes = plain_text_password.encode('utf-8')

    # generate salt
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    logger.debug("hash_password completed")
    return hashed_password

def compare_password(pt_pass: str, hpass: bytes) -> bool:
    logger.debug("compare_password called")
    password_bytes = pt_pass.encode('utf-8')
    res = bcrypt.checkpw(password_bytes, hpass)
    logger.debug("compare_password result=%s", res)
    return res

def sha_hash(code: str) -> str:
    logger.debug("sha_hash called")
    digest = hashlib.sha256(
        code.encode()
    ).hexdigest()
    logger.debug("sha_hash produced digest")
    return digest
