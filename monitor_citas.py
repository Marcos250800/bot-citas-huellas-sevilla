"""
Monitor de citas — Extranjería Sevilla (v9 — PRODUCCIÓN)
Trámite: POLICÍA-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA) INICIAL, RENOVACIÓN, DUPLICADO Y LEY 14/2013
Oficina: Documentación de Extranjeros POLICIA, Plaza de España Torre Norte, s/n, Sevilla
Solicitante: CAROLINA LÓPEZ PUPO — NIE Z1195798X — Cuba

REGLAS:
- SIEMPRE entrar por el portal padre (sede.administracionespublicas.gob.es)
- Telegram SOLO envía mensaje cuando HAY citas (silencio total en errores y sin citas)
- Headless: no se ve ventana (corre en segundo plano)
"""

import asyncio
import os
import sys
import requests
from playwright.async_api import async_playwright

# --- CREDENCIALES DE TELEGRAM ---
# En GitHub Actions vienen de secrets; en local están aquí abajo como fallback
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN_HUELLAS") or "8976054648:AAHMPBQvRrFi0F32eEnVEFqbaSgYgSFGGgA"
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID_HUELLAS") or "8755956593"

# --- URL DE ENTRADA: SIEMPRE EL PORTAL PADRE ---
URL_PORTAL_PADRE = "https://sede.administracionespublicas.gob.es/pagina/index/directorio/icpplus/"

# --- DATOS DEL TRÁMITE ---
PROVINCIA = "Sevilla"
OFICINA_TEXTO = "Documentación de Extranjeros POLICIA"
TRAMITE_TEXTO = "POLICÍA-TOMA DE HUELLAS"

# --- DATOS DE CAROLINA ---
NIE = "Z1195798X"
NOMBRE = "CAROLINA LÓPEZ PUPO"
PAIS = "CUBA"

SIN_CITAS_TEXTO = "no hay citas disponibles"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TIMEOUT_LARGO = 60000

# Si esta variable está, se intenta usar el Chrome real del sistema (modo local)
# En GitHub Actions no existe Chrome y usaremos el Chromium instalado por Playwright
USAR_CHROME_REAL = os.environ.get("GITHUB_ACTIONS") != "true"


def enviar_telegram(mensaje, screenshot_path=None):
    try:
        if screenshot_path and os.path.exists(screenshot_path):
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            with open(screenshot_path, "rb") as photo:
                files = {"photo": photo}
                data = {"chat_id": TELEGRAM_CHAT_ID, "caption": mensaje}
                r = requests.post(url, files=files, data=data, timeout=30)
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje}
            r = requests.post(url, data=data, timeout=30)

        if r.status_code == 200:
            print(f"✅ Telegram enviado")
        else:
            print(f"❌ Telegram error {r.status_code}")
    except Exception as e:
        print(f"❌ Excepción Telegram: {e}")


async def seleccionar_opcion(page, texto):
    return await page.evaluate(f"""
        () => {{
            const selects = document.querySelectorAll('select');
            for (const sel of selects) {{
                for (const opt of sel.options) {{
                    if (opt.text.includes("{texto}")) {{
                        sel.value = opt.value;
                        sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        sel.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        return opt.text;
                    }}
                }}
            }}
            return null;
        }}
    """)


async def revisar_citas():
    async with async_playwright() as p:
        # Configuración de navegador: en local usa Chrome real, en GitHub usa Chromium
        launch_args = {
            "headless": True,  # producción: sin ventana
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        }
        if USAR_CHROME_REAL:
            launch_args["channel"] = "chrome"

        try:
            browser = await p.chromium.launch(**launch_args)
            print(f"✅ Navegador lanzado (channel={launch_args.get('channel', 'chromium-default')})")
        except Exception as e:
            print(f"⚠️  Falló con Chrome real ({e}), usando Chromium por defecto")
            browser = await p.chromium.launch(headless=True, args=launch_args["args"])

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 900},
            locale="es-ES",
            extra_http_headers={
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            },
        )
        context.set_default_timeout(TIMEOUT_LARGO)
        context.set_default_navigation_timeout(TIMEOUT_LARGO)

        page = await context.new_page()

        try:
            # PASO 0: Portal padre
            print(f"➡️  Portal padre: {URL_PORTAL_PADRE}")
            await page.goto(URL_PORTAL_PADRE, wait_until="domcontentloaded", timeout=TIMEOUT_LARGO)
            await page.wait_for_timeout(2000)

            # Cookies
            try:
                acepto = page.locator("text=Acepto").first
                if await acepto.is_visible(timeout=3000):
                    await acepto.click()
                    await page.wait_for_timeout(800)
            except Exception:
                pass

            # PASO 1: Acceder al Procedimiento
            print("➡️  Acceder al Procedimiento")
            await page.click("text=Acceder al Procedimiento")
            await page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_LARGO)
            await page.wait_for_timeout(2000)

            # PASO 2: Provincia
            print(f"➡️  Provincia: {PROVINCIA}")
            await page.wait_for_selector("select", timeout=TIMEOUT_LARGO, state="visible")
            if not await seleccionar_opcion(page, PROVINCIA):
                raise Exception(f"No se encontró provincia '{PROVINCIA}'")
            await page.wait_for_timeout(1000)
            await page.click("input[value='Aceptar'], button:has-text('Aceptar')")
            await page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_LARGO)
            await page.wait_for_selector("select", timeout=TIMEOUT_LARGO, state="visible")
            await page.wait_for_timeout(1500)

            # PASO 3: Oficina
            print(f"➡️  Oficina: {OFICINA_TEXTO}")
            if not await seleccionar_opcion(page, OFICINA_TEXTO):
                raise Exception(f"No se encontró oficina '{OFICINA_TEXTO}'")
            await page.wait_for_timeout(2000)

            # PASO 4: Trámite
            print(f"➡️  Trámite: {TRAMITE_TEXTO}")
            if not await seleccionar_opcion(page, TRAMITE_TEXTO):
                raise Exception(f"No se encontró trámite '{TRAMITE_TEXTO}'")
            await page.wait_for_timeout(1000)
            await page.click("input[value='Aceptar'], button:has-text('Aceptar')")
            await page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_LARGO)
            await page.wait_for_timeout(2000)

            # PASO 5: Presentación sin Cl@ve
            print("➡️  Presentación sin Cl@ve")
            await page.click("text=Presentación sin Cl@ve")
            await page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_LARGO)
            await page.wait_for_timeout(2000)

            # PASO 6: Formulario
            print("➡️  Rellenando formulario")
            await page.fill("input[name='txtIdCitado'], input#txtIdCitado", NIE)
            await page.fill("input[name='txtDesCitado'], input#txtDesCitado", NOMBRE)
            if not await seleccionar_opcion(page, PAIS):
                raise Exception(f"No se encontró país '{PAIS}'")
            await page.wait_for_timeout(800)
            await page.click("input[value='Aceptar'], button:has-text('Aceptar')")
            await page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_LARGO)
            await page.wait_for_timeout(2000)

            # PASO 7: Solicitar Cita
            print("➡️  Solicitar Cita")
            await page.click("text=Solicitar Cita")
            await page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_LARGO)
            await page.wait_for_timeout(2500)

            # PASO 8: Comprobar resultado
            contenido = (await page.content()).lower()
            screenshot_final = os.path.join(SCRIPT_DIR, "ultima_captura.png")
            await page.screenshot(path=screenshot_final, full_page=True)

            if SIN_CITAS_TEXTO in contenido:
                print("😴 No hay citas disponibles (silencio)")
                return False
            else:
                print("🎉 ¡HAY CITAS! Enviando aviso a Telegram...")
                mensaje = (
                    "🚨 ¡POSIBLES CITAS DISPONIBLES! 🚨\n\n"
                    "📍 Sevilla — Toma de Huellas\n"
                    "👤 Carolina López Pupo\n\n"
                    f"Entra YA a:\n{URL_PORTAL_PADRE}\n\n"
                    "(Revisa la captura para confirmar)"
                )
                enviar_telegram(mensaje, screenshot_final)
                return True

        except Exception as e:
            # Solo log local — NO se notifica a Telegram en errores
            print(f"❌ ERROR (silenciado, no se notifica): {str(e)[:300]}")
            return False

        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    print("=" * 50)
    print("🔍 Monitor Citas — Huellas Sevilla (v9 producción)")
    print("=" * 50)
    resultado = asyncio.run(revisar_citas())
    print("=" * 50)
    if resultado:
        print("✅ FIN — Citas detectadas y notificadas")
    else:
        print("⏳ FIN — Sin citas o error (silencio)")
    print("=" * 50)
