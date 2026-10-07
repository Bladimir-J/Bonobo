from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
