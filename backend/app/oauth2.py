import hashlib
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from . import schemas, database, models
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='api/auth/login')

# auto_error=False -> si no hay token devolvemos None en lugar de tirar 401.
# Lo usamos en endpoints que son publicos pero que pueden enriquecer la
# respuesta si hay sesion (por ejemplo el detalle de pelicula).
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl='api/auth/login', auto_error=False)

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


#  RECUPERAR CONTRASEÑA
# El token del enlace del correo es un JWT aparte del de sesion:
#  - usa la clave "reset_user_id" (no "user_id"), asi no sirve para iniciar sesion
#  - lleva purpose="reset", asi un token de sesion no sirve para cambiar la contraseña
#  - lleva una huella del hash actual de la contraseña: en cuanto se cambia la
#    contraseña la huella deja de coincidir y el enlace ya no vale (un solo uso)
RESET_TOKEN_EXPIRE_MINUTES = 30


def _huella_password(password_hash: str) -> str:
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()[:16]


def create_reset_token(user: models.Usuario) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "reset_user_id": user.id,
        "purpose": "reset",
        "pwd": _huella_password(user.password_hash),
        "exp": expire,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_reset_token(token: str, db: Session):
    """Devuelve el usuario del token, o None si el enlace no es valido."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

    if payload.get("purpose") != "reset":
        return None

    user_id = payload.get("reset_user_id")
    if user_id is None:
        return None

    user = db.execute(
        select(models.Usuario).where(models.Usuario.id == user_id)
    ).scalar_one_or_none()
    if user is None:
        return None

    # si la contraseña ya cambio desde que se envio el correo, el enlace caduca
    if payload.get("pwd") != _huella_password(user.password_hash):
        return None

    return user


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        if id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=id)
    except JWTError:
        raise credentials_exception
    return token_data


# sin token -> None (visitante). Token presente pero invalido o caducado -> 401.
def get_optional_user(token: str = Depends(oauth2_scheme_optional), db: Session = Depends(database.get_db)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"}
            )
        user = db.execute(
            select(models.Usuario).where(models.Usuario.id == user_id)
        ).scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token caducado o inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se han podido validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"}
    )

    token_data = verify_access_token(token, credentials_exception)

    user = db.execute(
        select(models.Usuario).where(models.Usuario.id == token_data.id)
    ).scalar_one_or_none()

    return user
