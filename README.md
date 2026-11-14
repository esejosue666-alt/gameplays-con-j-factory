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
- [x] Selector automático de clips/imágenes locales aprobados según etiquetas de cada escena.
- [x] Buscador manual de candidatos de gameplay por escena (YouTube, sin descargar videos).\n- [ ] Verificación automatizada de permisos/licencias y adquisición segura del material.
- [ ] Prueba de subida privada y automatización posterior.

## Plan editorial
La mezcla de contenidos y las reglas de investigación están definidas en `config/editorial_plan.json`: videos de 8–12 minutos, voz masculina mexicana `es-MX-JorgeNeural`, separación entre hechos y teorías, fuentes verificables y revisión antes de publicar.

## Buscar gameplay de terceros\n1. Abre **Actions → Discover gameplay candidates → Run workflow**.\n2. Deja `episode_path` como `episodes/ep001_ff06b5.json` y `results_per_scene` como `4`.\n3. Ejecuta el workflow y descarga el artefacto `gameplay-candidates`.\n4. El JSON contiene candidatos agrupados por escena, canal, enlace original, duración y metadatos disponibles. Todos quedan `not_verified` y `approved_for_use: false`; debes obtener permiso o verificar una licencia compatible antes de incorporarlos.\n\nEl buscador usa yt-dlp solo para consultar resultados y metadatos públicos; no descarga archivos de video ni extrae audio. La disponibilidad de búsquedas puede variar por las restricciones de YouTube.\n\n## Generar un borrador
1. Abre **Actions → Render video draft → Run workflow**.
2. Para el primer episodio real, cambia `episode_path` a `episodes/ep001_ff06b5.json`. Para la prueba técnica, usa `episodes/demo.json`.
3. Descarga el artefacto **video-draft** al terminar.
4. Se genera un MP4 y un JSON de metadatos; no se publica nada.

Cada escena requiere `heading` y `narration`. Puede incluir `visual` para fijar un archivo o `visual_tags` para que el selector busque una coincidencia en `assets/gameplay/catalog.json`. Solo se utilizan archivos locales marcados `approved_for_use: true` y con base de derechos válida (`own_recording`, `written_permission` o `license`). Si no hay coincidencia aprobada, se genera una tarjeta de respaldo; nunca se elige gameplay aleatorio.

Consulta `assets/gameplay/README.md` para añadir material. Para Cyberpunk 2077, CD PROJEKT RED permite publicar gameplay relacionado con sus juegos y monetizarlo mediante programas de socios, pero recomienda activar “Desactivar música con derechos de autor”; la música puede tener derechos de terceros. La política no concede permiso para reutilizar grabaciones hechas por otros creadores. Consulta la [política oficial de vídeo](https://www.cdprojektred.com/es-mx/videopolicy) y las [directrices de contenido para fans](https://www.cdprojektred.com/es-mx/fan-content).

## Publicación
El workflow **Publish finished YouTube video** es manual y usa el secreto `YOUTUBE_TOKEN_B64` con el token OAuth codificado en Base64. La privacidad predeterminada es `private`. No ejecutes la publicación hasta revisar el MP4 y sus metadatos.

## Límites
- Edge TTS depende de un servicio en línea y no garantiza disponibilidad continua.
- El renderizador actual genera voz y tarjetas visuales; todavía no investiga ni redacta automáticamente el guion.
- GitHub Actions no es un servidor 24/7 y tiene cuotas.
- OAuth externo en estado **Testing** puede caducar refresh tokens a los 7 días para estos scopes.
- No se garantiza viralidad, monetización ni visitas.

## Archivos
- `scripts/render_video.py`: genera voz, subtítulos y monta escenas con selección de visuales aprobados y créditos automáticos.\n- `scripts/discover_gameplay.py`: busca candidatos de gameplay por escena sin descargarlos.\n- `.github/workflows/discover-gameplay.yml`: ejecuta la búsqueda y guarda el informe como artefacto.
- `episodes/demo.json`: episodio de demostración técnica.
- `episodes/ep001_ff06b5.json`: primer guion de 10 escenas sobre el misterio FF:06:B5 de Cyberpunk 2077.
- `scripts/youtube_upload.py`: sube un MP4 terminado.
- `.github/workflows/render-video.yml`: renderizado manual.
- `.github/workflows/publish.yml`: publicación manual.
