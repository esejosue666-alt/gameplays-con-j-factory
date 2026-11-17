# Biblioteca de gameplay de terceros

La fábrica puede usar grabaciones de otros jugadores cuando exista una base documentada que permita reutilizarlas. La atribución automática se añade a la descripción del video final.

## Importante: crédito no es permiso
Poner el nombre del canal o enlazar el video original es una buena práctica, pero no concede por sí solo derechos para descargar, recortar, editar, sincronizar o monetizar la grabación. No se debe marcar un clip como autorizado únicamente porque sea público en YouTube.

## Bases admitidas por el renderizador
- `written_permission`: permiso expreso del titular, conservado como evidencia. Se exige `permission_evidence`, `creator_name` y `source_url`.
- `license`: licencia verificable que permite el uso previsto, incluida edición y uso comercial cuando el canal vaya a monetizar. Se exige `license_url`, `creator_name` y `source_url`.
- `own_recording`: grabación propia, con `source_note`.

No se aceptan licencias que prohíban obras derivadas o uso comercial si el plan incluye editar o monetizar el video. Si las condiciones no están claras, no se aprueba el clip.

## Añadir un clip
1. Guarda el archivo autorizado en esta carpeta o una subcarpeta.
2. Añade un objeto en `catalog.json` con los campos del ejemplo.
3. Usa etiquetas que describan exactamente el contenido visual.
4. Comprueba que la evidencia cubre el archivo y el uso previsto.

Ejemplo de clip con permiso:
```json
{
  "path": "assets/gameplay/cyberpunk/iglesia.mp4",
  "tags": ["church", "biotechnica", "servers"],
  "approved_for_use": true,
  "rights_basis": "written_permission",
  "creator_name": "Nombre del creador",
  "creator_channel_url": "https://www.youtube.com/@canal",
  "source_url": "https://www.youtube.com/watch?v=VIDEO",
  "permission_evidence": "Registro privado del permiso recibido; no publicar datos privados",
  "attribution_text": "Gameplay de Nombre del creador"
}
```

Para licencia, sustituye `permission_evidence` por `license_url` y registra las condiciones en `source_note` o en un archivo de documentación.

## Selección y créditos
- El renderizador selecciona clips por coincidencia de etiquetas y evita repetirlos dentro del mismo episodio.
- Solo usa archivos locales con aprobación y datos de derechos suficientes.
- Añade automáticamente nombre, canal, video fuente y licencia (si aplica) a `output/metadata.json`.
- Si no hay un clip válido, utiliza la tarjeta de respaldo; nunca gameplay aleatorio.
- No descargues videos de YouTube ni elimines marcas de agua o atribuciones sin autorización.
- La música y los efectos de sonido tienen derechos separados: verifica su licencia por separado. En Cyberpunk 2077, activa la opción de desactivar música con derechos de autor al grabar.

La búsqueda de fuentes no equivale a autorización: cada clip debe pasar revisión antes de incorporarse al catálogo.


## Fondo de combate como respaldo para una escena sin toma exacta

En las escenas que incluyan `fallback_background_tags`, el renderizador intenta primero encontrar un video exacto de la escena. Si no existe, busca un video aprobado cuyos tags incluyan **todos** los tags configurados. En el episodio FF:06:B5, el respaldo requiere `cyberpunk_2077` y `combat`; así no se usa combate de otro juego por accidente. Las escenas 4 y 7 pueden reutilizar ese mismo fondo si solo hay una grabación aprobada.

Ejemplo de fondo de combate grabado por ti:

```json
{
  "path": "assets/gameplay/cyberpunk/combat-own-recording.mp4",
  "tags": ["cyberpunk_2077", "combat", "firefight"],
  "approved_for_use": true,
  "rights_basis": "own_recording",
  "source_note": "Grabación propia de Cyberpunk 2077; sin música con derechos de autor"
}
```

También se pueden añadir capturas autorizadas con tags como `church`, `biotechnica`, `servers`, `terminal` o `laptop`. La fábrica las muestra en paneles por turnos sobre el gameplay en movimiento. Cuando no hay capturas aprobadas, genera paneles ilustrativos con el rótulo **RECREACIÓN VISUAL · NO ES CAPTURA DEL JUEGO**. Esos paneles no se presentan como imágenes reales del juego.

**Importante:** el código no descarga ni reutiliza automáticamente los candidatos públicos de YouTube. El fondo de combate debe estar guardado localmente y marcado como grabación propia, permiso escrito o licencia compatible en `catalog.json`.
