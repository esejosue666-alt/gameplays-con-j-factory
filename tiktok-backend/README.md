# TikTok backend — Gameplays con J

Esta integración vive en un **Cloudflare Worker**, separado de GitHub Pages y de los workflows de YouTube. El secreto de TikTok nunca debe estar en HTML, JavaScript público ni GitHub.

## Qué hace
- Login Kit web OAuth v2 con parámetro `state` anti-CSRF.
- Intercambia el código por tokens desde el servidor.
- Guarda access/refresh tokens en Cloudflare KV y renueva el access token.
- Acepta un video MP4/MOV/WebM de hasta 50 MB, lo envía con `video.upload` y devuelve el `publish_id`.
- El usuario termina la publicación desde la notificación de TikTok. No publica directamente.

## Desplegar (una sola vez)
1. Crea una cuenta gratuita en Cloudflare y abre **Workers & Pages → Create → Worker**.
2. Crea un namespace KV llamado `GAMEPLAYS_TIKTOK`.
3. Crea un Worker llamado `gameplays-con-j-tiktok` y pega el contenido de `worker.js`.
4. En Settings → Variables and Secrets configura:
   - Secret `TIKTOK_CLIENT_KEY`: Client Key de TikTok.
   - Secret `TIKTOK_CLIENT_SECRET`: Client Secret de TikTok.
   - Variable `TIKTOK_REDIRECT_URI`: URL exacta del Worker terminada en `/oauth/callback`.
   - Variable `APP_URL`: `https://esejosue666-alt.github.io/gameplays-con-j-factory/`
   - Binding KV: variable `TIKTOK_KV` enlazada al namespace `GAMEPLAYS_TIKTOK`.
5. En TikTok Developers → Login Kit → Web registra como Redirect URI exactamente el valor de `TIKTOK_REDIRECT_URI`.
6. Prueba `https://TU-WORKER.workers.dev/health`; debe devolver `{"ok":true,...}`.

## Rutas
- `GET /oauth/start`: inicia el consentimiento TikTok.
- `GET /oauth/callback`: valida state y guarda tokens.
- `GET /api/status`: comprueba conexión.
- `POST /api/upload`: multipart/form-data con campo `video`.
- `POST /api/disconnect`: revoca/desconecta la sesión.

## Importante antes de producción
- El Worker es un backend mínimo para una sola cuenta propietaria y una demo controlada. Antes de ofrecerlo a terceros, añadir autenticación propia, límites de uso, registro de auditoría y política de retención.
- La API de TikTok debe aprobar la app y el scope `video.upload`; añadir el producto no equivale a aprobación.
- No uses el endpoint de carga hasta que TikTok apruebe el scope y el usuario haya consentido.
- El límite de 50 MB aquí es deliberado para la primera versión y la demo de revisión; TikTok admite archivos más grandes.
- GitHub Pages no ejecuta OAuth server-side; por eso el callback está en el Worker.
- No subas Client Secret ni tokens a este repositorio.

## Referencias oficiales
- Login Kit Web: https://developers.tiktok.com/docs/en/login-kit-web
- OAuth token: https://developers.tiktok.com/docs/en/oauth-get-a-user-access-token
- Content Posting API upload: https://developers.tiktok.com/docs/en/content-posting-api-reference-upload-video
- Media transfer: https://developers.tiktok.com/docs/en/content-posting-api-media-transfer-guide
