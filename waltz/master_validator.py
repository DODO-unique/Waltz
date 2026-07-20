from pydantic import BaseModel
from uuid import UUID
from ticket_enum import TicketEnum


class loginCredentials(BaseModel):
    identity: str
    pwd: str
    uname: bool



class Payload(BaseModel):
    value: dict[str, str]

class TicketType(BaseModel):
    id: UUID
    type: TicketEnum
    payload: Payload

