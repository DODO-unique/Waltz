from secrets import randbelow

from version_0_1.log.logger import get_logger

logger = get_logger("core.cadence")

logger.debug("core.cadence module loaded")
import time
from uuid import uuid4

from version_0_1.core.enums import OneTimePassword
from version_0_1.core.general import dispatch_ticket, get_id, publish_ticket
from version_0_1.exceptions.waltz_exceptions import (
    OTPExpiredException,
    UserNotFoundException,
)
from version_0_1.security.hashing import sha_hash
from version_0_1.validators.core_validator import (
    CadencePayload,
    CadenceTicket,
    FetchOTP,
    IdentityPayload,
    Mail,
    StoreOTP,
    TicketType,
    Uid,
)


class Cadence:
    '''
    Verifier said it needed a name 
    Cadence: A OTP service

    Anyway, so what does a Verifier need:

    1. Get a email
    2. Generate the OTP.
    3. Hash it
    4. Store the OTP in persistence
    5. Send OTP to the given mail/phone-number/etc
    6. wait for user-entered OTP
    7. Compare hashes.
    '''

    def __init__(self, email: Mail):
        self.email = email


    async def issue(self, uid: Uid):
        '''
        Provider is the service provider

        1. Receive email.
        2. Generate OTP.
        3. Hash OTP.
        4. Store hash + expiry + metadata.
        5. Send plaintext OTP to the email.
        6. Return "OTP issued."

        Just like tokens, otp also has an expiry and if now is greater than expiry you kill the token.
        THis is a persistence decision.
        ''' 
        logger.debug("Cadence.issue called for email=%s", self.email)
        code = randbelow(900_000) + 100_000
        digest = sha_hash(str(code))

        # pass the digest to be stored in the DB
        await publish_ticket(
            TicketType(id=uuid4(),
            type=OneTimePassword.Store,
            payload= StoreOTP(
                digest=digest,
                uid=uid
            )
            )
        )

        await dispatch_ticket(
            CadenceTicket(
                payload=CadencePayload(
                    email=self.email,
                    code=str(code)
                )
                )
            ) 
        logger.info("Cadence.issue dispatched OTP to email=%s", self.email)


    async def validate(self, code: str) -> bool:
        '''
        1. Fetch stored OTP record.
        2. Check expiry.
        3. Hash submitted OTP.
        4. Compare hashes.
        5. If valid:
            - mark OTP as used
            - continue workflow
        6. Return success/failure.
        '''

        logger.debug("Cadence.validate called email=%s", self.email)
        uid = await get_id(IdentityPayload(email=self.email))
        if uid is None:
            logger.error("Cadence.validate: No user found for email=%s", self.email)
            raise UserNotFoundException("No user found")
        result: FetchOTP = await publish_ticket(
            TicketType(
                type=OneTimePassword.Get,
                payload=uid
            )
        )

        if result.expiry < time.time():
            raise OTPExpiredException(f"OTP expired for {(result.expiry + time.time()) / 60} mins")

        given_otp_digest = sha_hash(code)

        if given_otp_digest == result.digest:
            # it is correct, send a correct flag back and delete the otp
            await publish_ticket(
                TicketType(
                    type=OneTimePassword.DeleteOTP,
                    payload=uid
                )
            )

            logger.info("Cadence.validate succeeded for email=%s uid=%s", self.email, uid)
            return True

        else:
            logger.info("Cadence.validate failed for email=%s uid=%s", self.email, uid)
            return False            
