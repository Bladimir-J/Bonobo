from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional
from .peliculas import PeliculaCache


class UserCreate(BaseModel):
    email: EmailStr
    # solo letras, numeros y _ (sin espacios, @, ni caracteres raros)
    # max 50 porque la columna VARCHAR de la BD es de ese tamaño
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(..., min_length=8, max_length=128)


# en la salida nunca metemos el password_hash, solo lo basico
class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class OlvidePassword(BaseModel):
    email: EmailStr


class RestablecerPassword(BaseModel):
    token: str = Field(..., min_length=10, max_length=2000)
    password_nueva: str = Field(..., min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None


class LogroOut(BaseModel):
    codigo: str
    nombre: str
    descripcion: str
    xp: int
    xp_reclamado: bool
    desbloqueado_el: datetime
    model_config = ConfigDict(from_attributes=True)


# datos minimos de un usuario, para listas (seguidores, buscador, ranking...)
class UsuarioResumen(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None
    xp_total: int = 0
    nivel: int = 1
    model_config = ConfigDict(from_attributes=True)


# perfil completo, lo usa la pagina de perfil
class UserProfile(BaseModel):
    id: int
    username: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    total_vistas: int
    seguidores: int = 0
    seguidos: int = 0
    yo_sigo: Optional[bool] = None
    xp_total: int = 0
    nivel: int = 1
    logros: list[LogroOut] = []
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    bio: Optional[str] = Field(None, max_length=250)
    avatar_url: Optional[str] = None

    @field_validator('avatar_url')
    @classmethod
    def validar_avatar_url(cls, v: Optional[str]) -> Optional[str]:
        # como minimo que sea http(s), no me vale "javascript:..." ni rutas raras
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('La URL del avatar debe empezar por http:// o https://')
        return v


class PasswordChange(BaseModel):
    password_actual: str
    password_nueva: str = Field(..., min_length=8, max_length=128)


class VistaConPelicula(BaseModel):
    id: int
    id_pelicula: int
    puntuacion: Optional[int] = None
    pelicula: PeliculaCache
    model_config = ConfigDict(from_attributes=True)


class FavoritaOut(BaseModel):
    orden: int
    pelicula: PeliculaCache
    model_config = ConfigDict(from_attributes=True)


class FeedItem(BaseModel):
    tipo: str
    usuario_id: int
    username: str
    avatar_url: Optional[str] = None
    pelicula_tmdb_id: int
    pelicula_titulo: str
    pelicula_poster: Optional[str] = None
    puntuacion: Optional[int] = None
    resena: Optional[str] = None
    entrada_id: Optional[int] = None
    created_at: str
