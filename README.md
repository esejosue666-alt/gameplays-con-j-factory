# Gameplays con J — Fábrica de videos

MVP para preparar videos narrados y publicarlos de forma controlada en **Gameplays con J**.

## Estado
- [x] OAuth de YouTube validado mediante GitHub Actions.
- [x] Workflow manual para generar un borrador MP4.
- [x] Narración en español mediante Edge TTS.
- [x] Tarjetas visuales por escena; admite imágenes propias.
- [x] Workflow de subida separado y manual.
- [ ] Investigación web automatizada y verificación de fuentes.
- [ ] Generación automática de guiones originales de al menos 8 minutos.
- [ ] Integración de gameplay/capturas con derechos de uso.
- [ ] Prueba de subida privada y automatización posterior.

## Generar un borrador
1. Abre **Actions → Render video draft → Run workflow**.
2. Deja `episodes/demo.json` para la primera prueba.
3. Descarga el artefacto **video-draft** al terminar.
4. Se genera un MP4 y un JSON de metadatos; no se publica nada.

Cada escena requiere `heading` y `narration`. Puede incluir `image` con una ruta a una imagen del repositorio. Si no hay imagen, se genera una tarjeta gráfica. Para episodios reales, usa gameplay/capturas propios o material con licencia compatible.

## Publicación
El workflow **Publish finished YouTube video** es manual y usa el secreto `YOUTUBE_TOKEN_B64` con el token OAuth codificado en Base64. La privacidad predeterminada es `private`. No ejecutes la publicación hasta revisar el MP4 y sus metadatos.

## Límites
- Edge TTS depende de un servicio en línea y no garantiza disponibilidad continua.
- El renderizador actual genera voz y tarjetas visuales; todavía no investiga ni redacta automáticamente el guion.
- GitHub Actions no es un servidor 24/7 y tiene cuotas.
- OAuth externo en estado **Testing** puede caducar refresh tokens a los 7 días para estos scopes.
- No se garantiza viralidad, monetización ni visitas.

## Archivos
- `scripts/render_video.py`: genera voz y monta escenas.
- `episodes/demo.json`: episodio de demostración.
- `scripts/youtube_upload.py`: sube un MP4 terminado.
- `.github/workflows/render-video.yml`: renderizado manual.
- `.github/workflows/publish.yml`: publicación manual.
