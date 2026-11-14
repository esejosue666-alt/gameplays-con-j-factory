# Gameplays con J — Fábrica de videos

Proyecto inicial para preparar y publicar videos terminados en el canal **Gameplays con J**.

## Estado actual

- [x] Repositorio conectado.
- [x] Script inicial para subir un MP4 a YouTube Data API.
- [x] Workflow manual de GitHub Actions.
- [ ] Generación automática de investigación, guion, voz, imágenes y edición.
- [ ] Autorización OAuth de YouTube y prueba privada de subida.
- [ ] Publicación automática al finalizar una producción.

**Importante:** este repositorio todavía no genera videos completos. El workflow actual solo sube un MP4 ya terminado y se inicia manualmente; no publica nada automáticamente al hacer push.

## Preparar un video

1. Coloca un MP4 terminado en `output/final.mp4`.
2. Copia `output/metadata.example.json` a `output/metadata.json` y edita título, descripción y etiquetas.
3. Configura el secreto `YOUTUBE_TOKEN_JSON` en GitHub: Settings → Secrets and variables → Actions → New repository secret.
4. En Actions, ejecuta **Publish finished YouTube video** manualmente.
5. El workflow usa `privacyStatus: private` por defecto. Mantén la primera prueba como privada.

El secreto debe contener el JSON de credenciales de usuario OAuth autorizado para el scope `https://www.googleapis.com/auth/youtube.upload`, con `client_id`, `client_secret` y `refresh_token`. No pegues credenciales, tokens ni el archivo OAuth en issues, commits o chats. No uses una API key: no permite subir videos.

## OAuth: advertencia sobre Testing

Si la pantalla de consentimiento OAuth de Google está en **Testing** y la aplicación es externa, los refresh tokens para estos scopes pueden caducar a los 7 días. Por tanto, no es adecuado para una automatización semanal permanente. Para uso continuo habrá que configurar correctamente el estado de publicación y completar cualquier verificación que Google exija. No cambies a producción ni publiques públicamente sin revisar los requisitos de Google.

## Límites

GitHub Actions ejecuta trabajos en máquinas temporales; no es un servidor 24/7. Los límites gratuitos dependen del tipo de repositorio y de las cuotas vigentes de GitHub. La publicación también está sujeta a las cuotas y políticas de YouTube Data API.

## Estructura

- `scripts/youtube_upload.py`: carga un MP4 terminado.
- `output/metadata.example.json`: plantilla de metadatos.
- `.github/workflows/publish.yml`: workflow manual de publicación.
