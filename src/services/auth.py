import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.config.settings import settings



class AuthProvider:
    def __init__(self, domain: str, audience: str, algorithms: list[str]):
        self.issuer = f"https://{domain}/"
        self.audience = audience
        self.algorithms = algorithms
        self.jwks_url = f"{self.issuer}.well-known/jwks.json"
        self.jwk_client = PyJWKClient(self.jwks_url)
        self.bearer = HTTPBearer()

    def verify_jwt(self, token: str) -> dict:
        try:
            signing_key = self.jwk_client.get_signing_key_from_jwt(token).key
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer,
            )
            return payload  # dict with sub, scope/permissions etc
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
    def require_permissions(self, *required: str):
        def dep(payload=Depends(self.verify_jwt)):
            perms = set(payload.get("permissions", []))
            if not perms and (scope := payload.get("scope")):
                perms = set(scope.split())
            if not set(required).issubset(perms):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions"
                )
            return payload
        return dep
    