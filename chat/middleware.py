from urllib.parse import parse_qs

from django.contrib.auth import get_user_model
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Authenticates WebSocket connections using SimpleJWT.
    Expects token in query params:
    ws://domain/ws/chat/<room_id>/?token=ACCESS_TOKEN
    """

    async def __call__(self, scope, receive, send):
        query_string = scope["query_string"].decode()
        query_params = parse_qs(query_string)

        token = query_params.get("token")

        if token:
            token = token[0]
            jwt_auth = JWTAuthentication()

            try:
                validated_token = jwt_auth.get_validated_token(token)
                user = await self.get_user(validated_token["user_id"])
                scope["user"] = user
            except (InvalidToken, TokenError):
                scope["user"] = None
        else:
            scope["user"] = None

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
