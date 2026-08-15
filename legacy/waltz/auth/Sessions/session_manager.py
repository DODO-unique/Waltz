'''
docstring for session manager

manage sessions. Tasks seperated into functions
'''
from auth.Sessions.session_manager_2 import is_session_running
from validators.master_validator import UserName
from logger import loggy
from uuid import uuid4
from datetime import datetime, timedelta

def log(msg: str) -> None:
    loggy("Sessions/session_manager", msg)

async def create_session(uname: UserName):
    '''
    create session. 
    session has:
    1. id
    2. user_id
    3. token
    4. created_at
    5. expires_at
    # we have to decide the above here and send to ORM, there add an entry.
    out of those 5, some are created automatically. like id, created at, expires_at
    we need to set token.
    We also need to fetch user id which will refer to the user table.
    information relevant to this would be used relationally.
    '''
    # this returns a ScalarResult object. We can pass it as model
    select_object = await fetch_line(uname= uname)

    token = uuid4()

    # create a new session!
    result = await new_session(session_token=token, user = select_object) 
    if result:
        log("created new session; returning token to Verification")
        return { "token" : token , "expires_at" : datetime.now() + timedelta(hours=1)}
    initiate_error_handler(message="could not create session", errCode=ErrorCodes.CANNOT_CREATE_SESSION.value, error=ValueError("could not create session"))

async def fetch_session(uname: UserName):
    '''
    get session for a user.
    '''
    running_status = await is_session_running(uname=uname, return_user_row=True)
    if running_status['is_running']:
        user_row = running_status['user_row']
        session = await get_session(user_row=user_row)
        if session:
            log("Wrapped session object")
            return { "token" : session.token, "expires_at" : session.expires_at}

    initiate_error_handler(message="could not get session", errCode=ErrorCodes.CANNOT_GET_SESSION.value, error=ValueError("could not get session"))

async def delete_session(uname: UserName):
    '''
    delete session for a user.
    '''
    running_status = await is_session_running(uname=uname, return_user_row=True)
    if running_status['is_running']:
        user_row = running_status['user_row']
        result = await remove_session(user_row=user_row)
        if result:
            log("deleted session")
            return True
    initiate_error_handler(message="could not delete session", errCode=ErrorCodes.CANNOT_DELETE_SESSION.value, error=ValueError("could not delete session"))
