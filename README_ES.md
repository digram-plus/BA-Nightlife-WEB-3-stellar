# 🇦🇷 BA Nightlife Bot (Versión en Español)

BA Nightlife Bot es una solución integral para la agregación y automatización de anuncios de la vida nocturna de Buenos Aires. Combina scraping impulsado por IA, logística de contenido inteligente y tecnología Web3 para ofrecer una experiencia premium tanto para usuarios como para organizadores.

---

## 🚀 Características Principales

### 1. 🔍 Scraping Multi-canal (IA y OCR)

El bot recopila datos de todas las fuentes clave:

- **Instagram (Playwright + OCR)**: Supera las protecciones de Instagram, captura capturas de pantalla de alta resolución y utiliza EasyOCR para extraer fechas, nombres y artistas de los flyers.
- **Telegram Scraper**: Monitorea canales y grupos locales relevantes para capturar anuncios de la comunidad.
- **API de Agregadores**: Integración directa con plataformas como **Venti**, **Catpass** y **Passline** para obtener datos precisos y enlaces de compra.

### 2. 🧠 Publicación Inteligente en Telegram

Lógica refinada para mantener un canal profesional:

- **Orden Cronológico**: Los eventos se publican estrictamente según la fecha del evento, no por el momento del scraping.
- **Horizonte de 14 Días**: El bot solo publica anuncios para los próximos 14 días para evitar el spam y mantener la relevancia.
- **Tópicos Automáticos**: Los eventos se distribuyen por géneros (Techno, House, Jazz, Rock, etc.) dentro de un grupo de Telegram.
- **Alertas de Género**: Si el género no se detecta automáticamente, el bot alerta al administrador para una corrección manual.

### 3. 🌐 Dashboard Web3 y Billeteras

Interfaz moderna para el descubrimiento de eventos:

- **Dashboard en Next.js**: Calendario completo de eventos accesible vía Web App.
- **Openfort (Social Login)**: Inicio de sesión con un solo clic mediante Google, eliminando la necesidad de gestionar frases semilla.
- **Billeteras Embebidas**: Creación automática de billeteras inteligentes (Stellar/Celo) para check-ins y sistemas de lealtad.

### 4. 🤖 Automatización de Procesos

- **Sincronización con n8n**: Cada publicación exitosa en Telegram se sincroniza automáticamente con un webhook de n8n para integraciones externas (Google Calendar, logs).
- **Programador (Scheduler)**: Operación 100% autónoma las 24 horas, los 7 días de la semana.

---

## 🗺 Hoja de Ruta (Roadmap)

### 💎 Integración con Stellar

- **Fiat-to-Crypto On-ramp**: Recarga de billetera mediante tarjetas bancarias locales (Argentina, Colombia, México, etc.) utilizando herramientas de Stellar (SEP-24/SEP-6). Esto permitirá que usuarios sin experiencia previa en cripto compren entradas fácilmente.
- **Venta Directa de Entradas**: Permitir que artistas locales vendan entradas directamente en cripto (USDC/XLM) a través del bot, evitando altas comisiones.
- **Micro-donaciones**: Apoyo a artistas mediante "propinas" cripto integradas en el anuncio.
- **Proof of Presence (POW)**: Verificación on-chain de asistencia para recompensar a los miembros activos.

### 📍 Funciones Interactivas

- **Integración con Google Maps**: Vista de mapa en el bot/app para encontrar eventos por género y ubicación (distancia desde el usuario) para fechas específicas.

---

## 🛠 Stack Tecnológico

- **Backend**: Python (FastAPI / APScheduler / SQLAlchemy)
- **Scraping**: Playwright, BeautifulSoup, Cloudscraper
- **IA/OCR**: EasyOCR, Procesamiento de Lenguaje Natural para detección de géneros
- **Base de Datos**: PostgreSQL (Dockerizado)
- **Frontend**: Next.js, Tailwind CSS, Openfort SDK
- **Blockchain**: Stellar / Celo

---

## 📦 Instalación Rápida

1. **Clonar el repositorio**:

   ```bash
   git clone https://github.com/digram-plus/-BA-Nightlife-WEB-3-telegram.git
   ```

2. **Configurar el entorno**:
   Crea un archivo `.env` basado en `.env.example` con tus tokens de Telegram, claves de API y credenciales de base de datos.

3. **Ejecutar con Docker**:

   ```bash
   docker-compose up -d
   ```

4. **Instalar dependencias de Python**:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

5. **Iniciar el bot**:
   ```bash
   python3 main.py
   ```

---

¡Disfruta de la mejor vida nocturna de Buenos Aires con automatización y Web3! 🚀🤙
