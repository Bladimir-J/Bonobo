from sqlalchemy import Boolean, Column, Integer, String, Text, Date, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from ..database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)  # URL o foto subida (data URL)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    xp_total = Column(Integer, nullable=False, server_default=text("0"))
    nivel = Column(Integer, nullable=False, server_default=text("1"))

# Caché local de películas de TMDB. Solo guardamos lo esencial para relacionar
# acciones del usuario con una película concreta.
class Pelicula(Base):
    __tablename__ = "peliculas"

    id = Column(Integer, primary_key=True, nullable=False)
    tmdb_id = Column(Integer, nullable=False, unique=True)
    titulo = Column(String(255), nullable=True)
    poster_url = Column(String(500), nullable=True)
    anio_estreno = Column(Integer, nullable=True)


class Vista(Base):
    __tablename__ = "vistas"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False, index=True)
    puntuacion = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    pelicula = relationship("Pelicula")

    __table_args__ = (
        CheckConstraint("puntuacion >= 1 AND puntuacion <= 10", name="check_puntuacion"),
        UniqueConstraint("id_usuario", "id_pelicula", name="unique_usuario_pelicula_vista"),
    )


# Un usuario puede tener varias entradas para la misma película (visionados múltiples).
class EntradaDiario(Base):
    __tablename__ = "entradas_diario"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha_visionado = Column(Date, nullable=False)
    resena = Column(Text, nullable=True)
    puntuacion = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))


class MeGusta(Base):
    __tablename__ = "me_gusta"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (UniqueConstraint("id_usuario", "id_pelicula", name="unique_usuario_pelicula_mg"),)


class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (UniqueConstraint("id_usuario", "id_pelicula", name="unique_usuario_pelicula_wl"),)


# Máximo 4 películas favoritas por usuario, con orden 1-4 para el perfil.
class PeliculaFavorita(Base):
    __tablename__ = "peliculas_favoritas"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    orden = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    pelicula = relationship("Pelicula")

    __table_args__ = (
        CheckConstraint("orden >= 1 AND orden <= 4", name="check_orden"),
        UniqueConstraint("id_usuario", "id_pelicula", name="unique_usuario_pelicula_fav"),
        UniqueConstraint("id_usuario", "orden", name="unique_usuario_orden_fav"),
    )


class Seguidor(Base):
    __tablename__ = "seguidores"

    id = Column(Integer, primary_key=True, nullable=False)
    id_seguidor = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    id_seguido = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("id_seguidor", "id_seguido", name="unique_seguidor_seguido"),
        CheckConstraint("id_seguidor != id_seguido", name="check_no_autofollow"),
    )


class ComentarioResena(Base):
    __tablename__ = "comentarios_resena"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_entrada_diario = Column(Integer, ForeignKey("entradas_diario.id", ondelete="CASCADE"), nullable=False, index=True)
    texto = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    usuario = relationship("Usuario")


class LikeResena(Base):
    __tablename__ = "likes_resena"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_entrada_diario = Column(Integer, ForeignKey("entradas_diario.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("id_usuario", "id_entrada_diario", name="unique_usuario_entrada_like"),
    )


class Lista(Base):
    __tablename__ = "listas"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    es_publica = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))


class ListaPelicula(Base):
    __tablename__ = "listas_peliculas"

    id = Column(Integer, primary_key=True, nullable=False)
    id_lista = Column(Integer, ForeignKey("listas.id", ondelete="CASCADE"), nullable=False, index=True)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    pelicula = relationship("Pelicula")

    __table_args__ = (
        UniqueConstraint("id_lista", "id_pelicula", name="unique_lista_pelicula"),
    )


# catálogo de logros disponibles en el juego
class Logro(Base):
    __tablename__ = "logros"

    id = Column(Integer, primary_key=True, nullable=False)
    codigo = Column(String(50), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=False)
    xp = Column(Integer, nullable=False, server_default=text("0"))


# logros que ha desbloqueado cada usuario
class UsuarioLogro(Base):
    __tablename__ = "usuario_logros"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    id_logro = Column(Integer, ForeignKey("logros.id", ondelete="CASCADE"), nullable=False, index=True)
    xp_reclamado = Column(Boolean, nullable=False, server_default=text("false"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("id_usuario", "id_logro"),
    )

class ListaColaborador(Base):
    __tablename__ = "lista_colaboradores"

    id = Column(Integer, primary_key=True, nullable=False)
    id_lista = Column(Integer, ForeignKey("listas.id", ondelete="CASCADE"), nullable=False, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("id_lista", "id_usuario", name="unique_lista_colaborador"),
    )
