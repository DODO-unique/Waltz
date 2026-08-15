from logger import loggy
from validators.master_validator import Mail, UserName

def log(msg: str) -> None:
    loggy("Auth/common/username_check.py", msg)

# check user, create a response Dict and send it back.
async def check_user(username: UserName, email: Mail) -> dict[str, bool]:
    response: dict[str, bool] = {}

    log(f"Received request to check user: {username} and {email}")
    log("checking email availability")
    # try email
    is_email_taken = await check_user_exists(Users.email, email)
    log(f"Is email taken?: {is_email_taken}")
    response['email_available'] = not is_email_taken # if email is taken, it's not available
    log(f"email_availability: {not is_email_taken}")
    
    log("checking username availability")
    # try username
    is_username_taken = await check_user_exists(Users.uname, username)
    log(f"Is username taken?: {is_username_taken}")
    response['username_available'] = not is_username_taken # if username is taken, it's not available
    log("Received a response, returning to registration module")
    return response


# for quick username check for better UX
async def check_username(username: UserName):
    is_taken = await check_user_exists(Users.uname, username)
    log(f"Is username taken?: {is_taken}")
    return {'username_available' : not is_taken}