from fastapi import FastAPI, APIRouter
from core import verify_credentials
from master_validator import loginCredentials


def install(app: FastAPI, path: str ='/auth'):

    auth = APIRouter(prefix=path)

    @auth.get('/health')
    def health(): #type: ignore
        return (
            {'Success': '200/OK'}
        )
    
    @auth.post('/credentials')
    def creds(creds: loginCredentials):
       verify_credentials(creds).authenticate()
    
    app.include_router(auth)