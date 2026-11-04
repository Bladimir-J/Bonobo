from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from .. import database, schemas, models, utils, oauth2
from ..config import settings
from ..services import email_service

router = APIRouter(
    prefix="/api/auth",
    tags=['Autenticación']
)


@router.post('/registro', status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def crear_usuario(usuario: schemas.UserCreate, db: Session = Depends(database.get_db)):

    # comprobamos que el email no este pillado
    usuario_existente = db.execute(
        select(models.Usuario).where(models.Usuario.email == usuario.email)
    ).scalar_one_or_none()
    if usuario_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Ese email ya está registrado")

    hashed_password = utils.hash_password(usuario.password)

    nuevo_usuario = models.Usuario(
        email=usuario.email,
        username=usuario.username,
        password_hash=hashed_password
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario


@router.post('/login', response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):

    # OAuth2PasswordRequestForm pide un campo "username" pero nosotros
    # metemos ahi el email. Es como funciona el form de FastAPI por defecto.
    user = db.execute(
        select(models.Usuario).where(models.Usuario.email == user_credentials.username)
    ).scalar_one_or_none()

    # devolvemos el mismo error en los dos casos para no chivar si
    # el email existe o no (cuestion de seguridad basica)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Credenciales inválidas")

    if not utils.verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Credenciales inválidas")

    access_token = oauth2.create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}


#  RECUPERAR CONTRASEÑA
# Paso 1: el usuario escribe su email y le mandamos un enlace.
# Respondemos SIEMPRE lo mismo, exista o no el email, para no chivar que
# cuentas hay registradas. El correo se envia en segundo plano (despues de
# responder) para que el tiempo de respuesta tampoco lo delate.
MENSAJE_OLVIDE = ("Si ese email está registrado, te hemos enviado un enlace "
                  "para cambiar la contraseña. Revisa también la carpeta de spam.")


@router.post('/olvide-password', status_code=status.HTTP_202_ACCEPTED)
def olvide_password(datos: schemas.OlvidePassword,
                    background_tasks: BackgroundTasks,
                    db: Session = Depends(database.get_db)):

    user = db.execute(
        select(models.Usuario).where(func.lower(models.Usuario.email) == datos.email.lower())
    ).scalars().first()

    if user:
        token = oauth2.create_reset_token(user)
        enlace = f"{settings.frontend_url.rstrip('/')}/pages/restablecer-password.html?token={token}"
        background_tasks.add_task(
            email_service.enviar_email_recuperacion,
            user.email, user.username, enlace, oauth2.RESET_TOKEN_EXPIRE_MINUTES
        )

    return {"message": MENSAJE_OLVIDE}


# Paso 2: el usuario abre el enlace del correo y elige la contraseña nueva.
@router.post('/restablecer-password')
def restablecer_password(datos: schemas.RestablecerPassword, db: Session = Depends(database.get_db)):

    user = oauth2.verify_reset_token(datos.token, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="El enlace no es válido o ha caducado. Pide uno nuevo.")

    user.password_hash = utils.hash_password(datos.password_nueva)
    db.commit()

    return {"message": "Contraseña cambiada. Ya puedes iniciar sesión."}
