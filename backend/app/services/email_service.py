"""Envio de emails transaccionales con la API de Brevo.

Usamos la API HTTP (no SMTP) porque es mas sencilla y funciona en cualquier
hosting, incluido el plan gratis de Render.
Docs: https://developers.brevo.com/reference/sendtransacemail
"""
import logging
import time
from html import escape

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_STATS_URL = "https://api.brevo.com/v3/smtp/statistics/aggregatedReport"
BREVO_TIMEOUT = 10.0


def _headers() -> dict:
    return {
        "api-key": settings.brevo_api_key,
        "accept": "application/json",
        "content-type": "application/json",
    }


def email_configurado() -> bool:
    return bool(settings.brevo_api_key)


def enviar_email(destinatario: str, asunto: str, html: str, texto: str) -> bool:
    """Envia un email. Devuelve True si Brevo lo acepto.

    Nunca lanza excepciones: si falla lo dejamos en el log y seguimos, para
    que un problema con el correo no tumbe la peticion del usuario.
    """
    if not email_configurado():
        logger.warning("BREVO_API_KEY no configurada: no se envia el email a %s", destinatario)
        return False

    payload = {
        "sender": {"name": settings.mail_from_name, "email": settings.mail_from},
        "to": [{"email": destinatario}],
        "subject": asunto,
        "htmlContent": html,
        "textContent": texto,
    }

    try:
        with httpx.Client(timeout=BREVO_TIMEOUT) as client:
            res = client.post(BREVO_SEND_URL, headers=_headers(), json=payload)
        if res.status_code >= 400:
            logger.error("Brevo rechazo el email (%s): %s", res.status_code, res.text)
            return False
        return True
    except httpx.HTTPError as e:
        logger.error("Error de red enviando email con Brevo: %s", e)
        return False


def enviar_email_recuperacion(destinatario: str, username: str, enlace: str, minutos: int) -> bool:
    nombre = escape(username)
    enlace_html = escape(enlace, quote=True)

    asunto = "Recupera tu contraseña de Bonobo"

    html = f"""\
<!DOCTYPE html>
<html lang="es">
<body style="margin:0;padding:0;background:#0e0e12;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0e0e12;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#16161e;border:1px solid #2a2a3c;border-radius:12px;">
        <tr><td style="padding:32px;">
          <p style="margin:0 0 24px;font-size:24px;font-weight:bold;letter-spacing:2px;color:#e8a020;">BONOBO</p>
          <p style="margin:0 0 16px;font-size:16px;color:#e8e8f2;">Hola, {nombre}:</p>
          <p style="margin:0 0 24px;font-size:14px;line-height:1.6;color:#b8b8d0;">
            Hemos recibido una solicitud para cambiar la contraseña de tu cuenta.
            Pulsa el botón para elegir una nueva:
          </p>
          <p style="margin:0 0 24px;">
            <a href="{enlace_html}" style="display:inline-block;background:#e8a020;color:#0e0e12;text-decoration:none;font-weight:bold;font-size:15px;padding:12px 24px;border-radius:8px;">
              Cambiar contraseña
            </a>
          </p>
          <p style="margin:0 0 8px;font-size:12px;line-height:1.6;color:#7878a0;">
            El enlace caduca en {minutos} minutos y solo sirve una vez.
          </p>
          <p style="margin:0 0 8px;font-size:12px;line-height:1.6;color:#7878a0;">
            Si el botón no funciona, copia esta dirección en tu navegador:<br>
            <span style="color:#b8b8d0;word-break:break-all;">{enlace_html}</span>
          </p>
          <p style="margin:24px 0 0;font-size:12px;line-height:1.6;color:#7878a0;">
            Si no has pedido este cambio, ignora este correo: tu contraseña seguirá siendo la misma.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    texto = (
        f"Hola, {username}:\n\n"
        "Hemos recibido una solicitud para cambiar la contraseña de tu cuenta de Bonobo.\n"
        f"Abre este enlace para elegir una nueva (caduca en {minutos} minutos):\n\n"
        f"{enlace}\n\n"
        "Si no has pedido este cambio, ignora este correo."
    )

    return enviar_email(destinatario, asunto, html, texto)


# Brevo desactiva una clave API si pasa 90 dias sin usarse. Como solo se usa
# cuando alguien pide recuperar la contraseña, el endpoint /api/salud (que
# visita GitHub Actions cada 3 dias) hace una consulta ligera para mantenerla
# viva. Como mucho una vez al dia, para no gastar llamadas.
_ultimo_ping_brevo = 0.0
PING_BREVO_CADA = 24 * 60 * 60


def mantener_clave_activa() -> str:
    global _ultimo_ping_brevo

    if not email_configurado():
        return "sin configurar"
    if time.time() - _ultimo_ping_brevo < PING_BREVO_CADA:
        return "ok"

    try:
        with httpx.Client(timeout=BREVO_TIMEOUT) as client:
            res = client.get(BREVO_STATS_URL, headers=_headers(), params={"days": 1})
        if res.status_code >= 400:
            logger.error("Ping a Brevo fallido (%s): %s", res.status_code, res.text)
            return "error"
        _ultimo_ping_brevo = time.time()
        return "ok"
    except httpx.HTTPError as e:
        logger.error("Error de red en ping a Brevo: %s", e)
        return "error"
