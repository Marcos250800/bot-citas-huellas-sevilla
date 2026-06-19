# Bot Citas Huellas Sevilla

Monitor automático de citas de extranjería en Sevilla.

- **Trámite:** POLICÍA-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA) INICIAL, RENOVACIÓN, DUPLICADO Y LEY 14/2013
- **Oficina:** Documentación de Extranjeros POLICIA, Plaza de España Torre Norte, s/n, Sevilla
- **Solicitante:** Carolina López Pupo — NIE Z1195798X — Cuba

Cuando detecta citas, avisa por **Telegram con captura de pantalla**.

## ⚡ Frecuencia

- **Cada 2 minutos** vía cron-job.org (gatillo externo)
- **Cada 5 minutos** vía GitHub Actions (respaldo por si falla cron-job.org)

## 🔐 Secrets necesarios en GitHub

| Nombre | Valor |
|---|---|
| `TELEGRAM_BOT_TOKEN_HUELLAS` | Token del bot de @BotFather |
| `TELEGRAM_CHAT_ID_HUELLAS` | `8755956593` |

## 🚀 Cómo arrancar

1. `Settings` → `Secrets and variables` → `Actions` → añadir los 2 secrets
2. Pestaña `Actions` → habilitar workflows
3. Lanzar `Run workflow` manualmente la primera vez para probar
4. Configurar cron-job.org con POST a:
   `https://api.github.com/repos/USUARIO/REPO/dispatches`
   con body `{"event_type":"check-citas-huellas"}`
