# Gameplays con J — Fábrica de videos

MVP para preparar videos narrados y publicarlos de forma controlada en **Gameplays con J**.

## Estado
- [x] OAuth de YouTube validado mediante GitHub Actions.
- [x] Workflow manual para generar un borrador MP4.
- [x] Narración en español mediante Edge TTS.
- [x] Tarjetas visuales por escena; admite imágenes propias.
- [x] Workflow de subida separado y manual.
- [ ] Investigación web automatizada y verificación de fuentes.
- [x] Plan editorial mixto: 40% misterios, 30% historias oscuras y 30% curiosidades.
- [ ] Generación automática de guiones originales de al menos 8 minutos.
- [ ] Integración de gameplay/capturas con derechos de uso.
- [ ] Prueba de subida privada y automatización posterior.

## Plan editorial
La mezcla de contenidos y las reglas de investigación están definidas en `config/editorial_plan.json`: videos de 8–12 minutos, voz masculina mexicana `es-MX-JorgeNeural`, separación entre hechos y teorías, fuentes verificables y revisión antes de publicar.

## Generar un borrador
1. Abre **Actions → Render video draft → Run workflow**.
2. Para el primer episodio real, cambia `episode_path` a `episodes/ep001_ff06b5.json`. Para la prueba técnica, usa `episodes/demo.json`.
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
- `episodes/demo.json`: episodio de demostración técnica.
- `episodes/ep001_ff06b5.json`: primer guion de 10 escenas sobre el misterio FF:06:B5 de Cyberpunk 2077.
- `scripts/youtube_upload.py`: sube un MP4 terminado.
- `.github/workflows/render-video.yml`: renderizado manual.
- `.github/workflows/publish.yml`: publicación manual.
