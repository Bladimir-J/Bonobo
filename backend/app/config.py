from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_name: str
    database_username: str
    database_password: str

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    tmdb_token: str

    # Envio de emails (recuperar contraseña) con Brevo.
    # Tienen valor por defecto para que la app arranque aunque aun no esten
    # configuradas; sin BREVO_API_KEY simplemente no se envian correos.
    brevo_api_key: str = ""
    mail_from: str = "bonobo.app.oficial@gmail.com"
    mail_from_name: str = "Bonobo"
    # URL publica del frontend, para construir el enlace del correo
    frontend_url: str = "https://bonobo-ruby.vercel.app"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
