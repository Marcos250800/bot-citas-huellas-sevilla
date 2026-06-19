"""
Monitor de citas — Extranjería Sevilla (v3 — entra desde el portal padre)
Trámite: POLICÍA-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA) INICIAL, RENOVACIÓN, DUPLICADO Y LEY 14/2013
Oficina: Documentación de Extranjeros POLICIA, Plaza de España Torre Norte, s/n, Sevilla
Solicitante: CAROLINA LÓPEZ PUPO — NIE Z1195798X — Cuba

IMPORTANTE: Entrar SIEMPRE desde el portal padre (sede.administracionespublicas.gob.es),
no directamente a icp.administracionelectronica.gob.es (bloquea IPs de GitHub Actions).
"""

import asyncio
import os
import sys
import requests
from playwright.async_api import async_playwright

# --- CREDENCIALES ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN_HUELLAS")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID_HUELLAS")

# --- URLS ---
# Entramos por el portal padre (no por icp.* directamente)
URL_PORTAL = "https://sede.administracionespublicas.gob.es/pagina/index/directorio/icpplus/"

# --- DATOS DEL TRÁMITE ---
PROVINCIA = "Sevilla"
OFICINA_TEXTO = "Documentación de Extranjeros POLICIA"
TRAMITE_TEXTO = "POLICÍA-TOMA DE HUELLAS"

# --- DATOS DE CAROLINA ---
NIE = "Z1195798X"
NOMBRE = "CAROLINA LÓPEZ PUPO"
PAIS = "CUBA"

# --- FRASE QUE INDICA QUE NO HAY CITAS ---
SIN_CITAS_TEXTO = "no hay citas disponibles"


def enviar_telegram(mensaje, screenshot_path=None):
    """Envía mensaje a Telegram, con captura si se proporciona."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Faltan credenciales de Telegram")
        return

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
            print(f"✅ Telegram enviado: {mensaje[:60]}")
        else:
            print(f"❌ Telegram error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"❌ Excepción Telegram: {e}")


async def revisar_citas():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 900},
            locale="es-ES",
            extra_http_headers={
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        context.set_default_timeout(45000)
        context.set_default_navigation_timeout(90000)

        page = await context.new_page()

        try:
            # ========================================
            # PASO 0: Entrar por el PORTAL PADRE
            # ========================================
            print(f"➡️  Entrando en portal padre: {URL_PORTAL}")
            await page.goto(URL_PORTAL, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)

            # Aceptar cookies si aparece
            try:
                acepto = page.locator("text=Acepto").first
                if await acepto.is_visible(timeout=3000):
                    await acepto.click()
                    print("🍪 Cookies aceptadas")
                    await page.wait_for_timeout(800)
            except Exception:
                pass

            # ========================================
            # PASO 1: Clic en "Acceder al Procedimiento"
            #   → esto navega a icp.* de forma natural
            # ========================================
            print("➡️  Clic en 'Acceder al Procedimiento'")
            await page.click("text=Acceder al Procedimiento")

            # Espera al select de provincia (señal de que llegamos al icpplus)
            await page.wait_for_selector("select#form", timeout=90000, state="visible")
            await page.wait_for_timeout(1500)
            print(f"   ✓ Llegamos a: {page.url}")

            # ========================================
            # PASO 2: Seleccionar provincia Sevilla
            # ========================================
            print(f"➡️  Seleccionando provincia: {PROVINCIA}")
            await page.select_option("select#form", label=PROVINCIA)
            await page.wait_for_timeout(800)

            await page.click("input[value='Aceptar'], button:has-text('Aceptar')")
            await page.wait_for_selector("select", timeout=60000, state="visible")
            await page.wait_for_timeout(1500)

            # ========================================
            # PASO 3: Seleccionar oficina
            # ========================================
            print(f"➡️  Seleccionando oficina: {OFICINA_TEXTO}")
            oficina_seleccionada = await page.evaluate(f"""
                () => {{
                    const selects = document.querySelectorAll('select');
                    for (const sel of selects) {{
                        for (const opt of sel.options) {{
                            if (opt.text.includes("{OFICINA_TEXTO}")) {{
                                sel.value = opt.value;
                                sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return opt.text;
                            }}
                        }}
                    }}
                    return null;
                }}
            """)
            if not oficina_seleccionada:
                raise Exception(f"No se encontró oficina '{OFICINA_TEXTO}'")
            print(f"   ✓ {oficina_seleccionada}")
            await page.wait_for_timeout(1500)

            # ========================================
            # PASO 4: Seleccionar trámite
            # ========================================
            print(f"➡️  Seleccionando trámite: {TRAMITE_TEXTO}")
            tramite_seleccionado = await page.evaluate(f"""
                () => {{
                    const selects = document.querySelectorAll('select');
                    for (const sel of selects) {{
                        for (const opt of sel.options) {{
                            if (opt.text.includes("{TRAMITE_TEXTO}")) {{
                                sel.value = opt.value;
                                sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return opt.text;
                            }}
                        }}
                    }}
                    return null;
                }}
            """)
            if not tramite_seleccionado:
                raise Exception(f"No se encontró trámite '{TRAMITE_TEXTO}'")
            print(f"   ✓ {tramite_seleccionado}")
            await page.wait_for_timeout(1000)

            await page.click("input[value='Aceptar'], button:has-text('Aceptar')")
            await page.wait_for_load_state("domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)

            # ========================================
            # PASO 5: Clic en "Presentación sin Cl@ve"
            # ========================================
            print("➡️  Clic en 'Presentación sin Cl@ve'")
            await page.click("text=Presentación sin Cl@ve")
            await page.wait_for_load_state("domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)

            # ========================================
            # PASO 6: Rellenar formulario
            # ========================================
            print(f"➡️  Rellenando formulario")
            await page.fill("input[name='txtIdCitado'], input#txtIdCitado", NIE)
            await page.fill("input[name='txtDesCitado'], input#txtDesCitado", NOMBRE)
            await page.select_option("select[name='txtPaisNac'], select#txtPaisNac", label=PAIS)
            await page.wait_for_timeout(800)

            await page.click("input[value='Aceptar'], button:has-text('Aceptar')")
            await page.wait_for_load_state("domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)

            # ========================================
            # PASO 7: Clic en "Solicitar Cita"
            # ========================================
            print("➡️  Clic en 'Solicitar Cita'")
            await page.click("text=Solicitar Cita")
            await page.wait_for_load_state("domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2500)

            # ========================================
            # PASO 8: Comprobar resultado
            # ========================================
            contenido = (await page.content()).lower()
            screenshot_final = "/tmp/cita_final.png"
            await page.screenshot(path=screenshot_final, full_page=True)

            if SIN_CITAS_TEXTO in contenido:
                print("😴 No hay citas disponibles")
                return False
            else:
                print("🎉 ¡PARECE QUE HAY CITAS!")
                mensaje = (
                    "🚨 ¡POSIBLES CITAS DISPONIBLES! 🚨\n\n"
                    "📍 Sevilla — Toma de Huellas\n"
                    "👤 Carolina López Pupo\n\n"
                    f"Entra YA a:\n{URL_PORTAL}\n\n"
                    "(Revisa la captura para confirmar)"
                )
                enviar_telegram(mensaje, screenshot_final)
                return True

        except Exception as e:
            print(f"❌ ERROR: {e}")
            screenshot_error = "/tmp/cita_error.png"
            try:
                await page.screenshot(path=screenshot_error, full_page=True)
                enviar_telegram(
                    f"⚠️ Bot Huellas Sevilla — error:\n{str(e)[:300]}",
                    screenshot_error,
                )
            except Exception:
                enviar_telegram(f"⚠️ Bot Huellas Sevilla — error sin captura:\n{str(e)[:300]}")
            return False

        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    resultado = asyncio.run(revisar_citas())
    sys.exit(0 if resultado is not None else 1)
