from master_validator import loginCredentials, TicketType, Payload
from ticket_enum import TicketEnum
import bcrypt
from uuid import uuid4
from ticket_handler import TicketBus
# from demo_parent_ticket_resolver import 


class Ticket:
    def __init__(self, content: TicketType):
        self.id = content.id
        self.type = content.type
        self.payload = content.payload

def hash_password(plain_text_password: str) -> bytes:
    # first we convert string to bytes
    password_bytes = plain_text_password.encode('utf-8')

    # generate salt
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password


class verify_credentials:
    def __init__(self, creds: loginCredentials): 
        self.identity = creds.identity
        self.pwd =creds.pwd
        self.uname = creds.uname
        self.payload = {
                    'identity': self.identity 
                }
        self.bus = TicketBus()
    
    async def authenticate(self) -> dict[str, str]:
        '''
        Expected:
        {password : "hash"}: dict[str, str]
        The hash should be in strings and not bytes. We will handle it's encoding.
        '''

        password_body = await self.bus.raise_ticket(
                TicketType(
                    id=uuid4(),
                    type= TicketEnum.FETCH_USER_CREDS_UNAME if self.uname else TicketEnum.FETCH_USER_CREDS_EMAIL,
                    payload=Payload(
                        value=self.payload
                    )
                )
            )
        
        stored_pass = password_body['password'].encode('utf-8')

        is_authenticate = self._compare_pass(stored_pass)

        return {
                "response" : "200/OK",
                "is_authenticate" : "true" if is_authenticate else "false"
            }
    
    def _compare_pass(self, hpass: bytes) -> bool:
        password_bytes = self.pwd.encode('utf-8')

        return bcrypt.checkpw(password_bytes, hpass)
