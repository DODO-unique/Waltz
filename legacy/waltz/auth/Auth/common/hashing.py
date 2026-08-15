import bcrypt
from validators.master_validator import Password, UserName
from logger import loggy

def log(msg: str) -> None:
    loggy("Auth/common/hashing.py", msg)

def hash_password(pt_password: Password) -> bytes:
    log(f"pt_password: {pt_password}")
    log(f"pt_password: {pt_password.value}")
    password = pt_password.value.get_secret_value().encode('utf-8')
    salt = bcrypt.gensalt()
    digest = bcrypt.hashpw(password, salt)
    return digest

async def verify_password(pt_password: Password, uname: UserName):
    '''
    This will take plain text password, pass it to hasher, hash the plaintext password, then send it to ORM to check, and then return the response.
    '''
    # we fetch the hash for verification from ORM
    log("fetching hash for verification")
    result = await fetch_password(uname)

    if result is None:
        log("User not found.")
        return False
    
    password_bytes = pt_password.value.get_secret_value().encode('utf-8')
    if bcrypt.checkpw(password_bytes, result):
        log("Password verified.")
        return True
    else:
        log("Password not verified.")
        return False
    

    