'''
This creates sessions as well. So we have to create a relevant session verification function in ORM.

To verify we simply have to check if the credentials are avaialble. Usually only uname and passwords
'''

from validators.master_validator import UserName, Password
from auth.Auth.common.hashing import verify_password
from auth.Auth.common.username_check import check_username
from auth.Sessions.session_manager import create_session, fetch_session
from auth.Sessions.session_manager_2 import is_session_running
from logger import loggy

def log(msg: str):
    loggy("auth/Auth/auth_moderator/verification.py", msg)

# take uname and password

async def verification(uname: UserName, password: Password):
    # check credentials

    # first uname
    uname_result = await check_username(uname)
    if uname_result['username_available']:
        log("Username not found during verification.")
        initiate_error_handler(message="Username not found", errCode=ErrorCodes.USER_NOT_FOUND.value, error=ValueError("Username not found"))
    
    log(f"Username {uname.value} verified successfully.")
    # if username is available, check password
    result = await verify_password(pt_password=password, uname=uname)
    if not result:
        log("Password verification failed.")
        initiate_error_handler(message="Incorrect password", errCode=ErrorCodes.INCORRECT_PASSWORD.value, error=ValueError("Incorrect password"))

    log(f"Password verified for user {uname.value}.")
    
    # check if user already has a session under their name
    session_check = await is_session_running(uname)
    if session_check['is_running']:
        log("User already has a running session. Returning existing session.")
        return await fetch_session(uname)
    
    log("Creating a new session for user.")
    return await create_session(uname=uname)



