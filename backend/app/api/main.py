from fastapi import APIRouter

from app.api.routes import login, utils
from app.api.v1 import connection_lifetime

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(utils.router)
api_router.include_router(connection_lifetime.router)
