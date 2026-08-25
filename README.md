# Waltz

> **Pre-release notice:** Waltz is an in-progress project. Unit tests are still outstanding and the code is **not ready for use**. The APIs and integrations described here may change.

Waltz is a storage-agnostic, stateful authentication framework for FastAPI. It aims to provide federated authentication without coupling an application to a particular database, email provider, or OAuth/OIDC identity provider.

Its core separates authentication orchestration from integrations. Your application supplies listeners for persistence and delivery; Waltz emits typed operations for local accounts, sessions, one-time passwords, email delivery, and registered identity-provider credentials.

## Philosophy

<!-- LOGO: Add the Waltz logo here. -->

<!-- ![Waltz logo](path-or-url-to-logo) -->

- **Transparency:** integrations are explicit. Your application owns storage, sessions, OTP persistence, and email delivery.
- **Concrete user APIs:** typed payloads and operation contracts make the data crossing the framework boundary visible.
- **Documentation:** fuller integration guidance is planned and will be added soon.

## What it is intended to handle

- Local registration and password authentication.
- OAuth 2.0 authorization-code flows and OIDC ID-token flows.
- OAuth provider configuration through registered credentials.
- UUID session creation, lookup, validation, and destruction through storage callbacks.
- Email verification using expiring, hashed one-time passwords and an application-provided delivery callback.

## How integrations work

Waltz's internal `TicketBus` is the boundary between its core and your application. Register a `Listeners` instance, decorate asynchronous handlers for the operations your storage supports, then subscribe it to the shared bus.

```python
from mvp_1.core.enums import Session, User
from mvp_1.core.general import bus
from mvp_1.sdk.listeners import Listeners

listeners = Listeners(base_uri="https://api.example.com")

@listeners.decorator(User.GetID)
async def get_user_id(identity):
    # Query your database by identity.email or identity.uname.
    return None

@listeners.decorator(Session.Create)
async def create_session(request):
    # Persist the session and return its UUID token.
    ...

@listeners.cadence_decorator
def send_verification_email(message):
    # message.email and message.code are provided by Waltz.
    ...

bus.subscribe(listeners)

The operation contracts currently cover:

| Category | Operations |
| --- | --- |
| Users | Resolve an ID, fetch local/OAuth user data, retrieve email, and register local or OAuth users |
| Sessions | Create, check, delete, delete all, and retrieve a token |
| One-time passwords | Store, retrieve, and delete verification codes |
| Email cadence | Deliver an email and plaintext verification code through one registered callback |
| OAuth/OIDC | Register provider credentials and use them to initiate authorization and exchange codes |

### FastAPI routes

Create the router with `routes(prefix)` from `mvp_1.api.endpoints` and include it in your FastAPI app.

| Route | Purpose |
| --- | --- |
| `POST /local/register` | Register a local account |
| `POST /local/authenticate` | Authenticate a local account and return a session token |
| `GET /oauth/init` | Create a provider authorization URL |
| `GET /oauth/authResponse` | Process an OAuth/OIDC authorization response |
| `POST /verify/email/sent` | Issue and dispatch an email-verification OTP |
| `POST /verify/email/validate` | Validate a submitted OTP |

OAuth provider credentials are registered with:

```python
listeners.serenity(provider, OAuthCredentials(...))
```

The configured base URI is used to derive the callback path `/auth/oauth/authResponse`; ensure it matches the callback URL registered with the provider.

## File structure

```text
Waltz/
├── README.md
├── mvp_1/
│   ├── api/
│   │   └── endpoints.py          # FastAPI router and authentication endpoints
│   ├── constants/
│   │   └── providers.py          # Provider metadata and claim schemas
│   ├── core/
│   │   ├── orchestration.py      # Main authentication workflow
│   │   ├── idenity_service.py    # Identity registration and authentication
│   │   ├── session_manager.py    # Session lifecycle operations
│   │   ├── cadence.py            # OTP issuance and validation
│   │   ├── serenity.py           # OAuth/OIDC authorization and token exchange
│   │   ├── general.py            # Shared TicketBus helpers
│   │   ├── enums.py              # User, session, and OTP operation contracts
│   │   └── enums_bridge.py       # Generic operation-intention type
│   ├── sdk/
│   │   ├── listeners.py          # Application integration registration API
│   │   └── ticket_handler.py     # TicketBus implementation
│   ├── security/
│   │   ├── hashing.py            # Password and OTP hashing helpers
│   │   └── jwt_handler.py        # OIDC/JWK token verification
│   ├── validators/               # Pydantic payload and endpoint schemas
│   ├── exceptions/               # Waltz-specific exceptions
│   └── log/                      # Logging configuration
├── legacy/                       # Earlier experimental code
└── test.py                       # Scratch/example code; not a test suite
```

> `idenity_service.py` is the current filename spelling in the repository.

## Current status and limitations

This project is a foundation under active development, not a production package.

- Unit tests have not yet been written or run.
- The `update_user` path is not implemented.
- Session, callback, provider, and async-delivery behavior still require review and hardening.
- Packaging, installation instructions, a reference storage adapter, and a complete integration guide have not yet been added.

Do not use Waltz to protect real user accounts or production data until these gaps are resolved and the framework has been thoroughly tested and audited.