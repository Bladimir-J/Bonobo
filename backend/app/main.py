from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from . import database
from .services import email_service
from .routers import auth, peliculas, acciones, usuarios, social, diario, listas, logros

app = FastAPI(title="Bonobo API")

# orígenes permitidos: prod (vercel) + dev local en distintos puertos
# OJO: si se añade un dominio nuevo hay que meterlo aquí, sino el navegador
# tira error de CORS. Antes esto era ["*"] pero con allow_credentials=True
# los navegadores rechazan esa combinacion.
origins = [
    "https://bonobo-ten.vercel.app",
    "https://bonobo-ruby.vercel.app",
   "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(peliculas.router)
app.include_router(acciones.router)
app.include_router(usuarios.router)
app.include_router(social.router)
app.include_router(diario.router_diario)
app.include_router(diario.router_comentarios)
app.include_router(listas.router)
app.include_router(logros.router)


@app.get("/")
def root():
    # endpoint tonto para comprobar que la api responde
    return {"message": "Bonobo API funcionando"}


# Lo visita GitHub Actions cada 3 dias (.github/workflows/mantener-despierto.yml)
# para que Render se despierte, Supabase no se pause por inactividad y la
# clave de Brevo no caduque por no usarse.
@app.get("/api/salud")
def salud(db: Session = Depends(database.get_db)):
    db.execute(text("SELECT 1"))
    return {"api": "ok", "base_de_datos": "ok", "email": email_service.mantener_clave_activa()}
