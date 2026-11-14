# Biblioteca de gameplay

Coloca aquí clips o capturas que tengas derecho a utilizar. El renderizador busca coincidencias entre las etiquetas de cada escena y las etiquetas de cada archivo del catálogo.

## Reglas de autorización
- `own_recording`: grabación propia del juego (por ejemplo, captura de tu PS5).
- `written_permission`: permiso expreso y conservable del titular.
- `license`: licencia que permite el uso previsto; conserva la prueba/licencia.
- No marques un archivo como aprobado solo porque esté publicado en YouTube.
- No incluyas música de radio protegida. En Cyberpunk 2077 activa “Desactivar música con derechos de autor” antes de grabar.

## Añadir un clip
1. Copia el MP4/MOV/MKV/WEBM o imagen JPG/PNG/WEBP a esta carpeta o una subcarpeta.
2. Añade un objeto a `catalog.json`:
   - `path`: ruta relativa desde la raíz del repositorio.
   - `tags`: etiquetas temáticas, por ejemplo `["corpo_plaza","statue","ff06b5"]`.
   - `approved_for_use`: `true` solo después de confirmar derechos.
   - `rights_basis`: `own_recording`, `written_permission` o `license`.
   - `source_note`: nota breve que identifique el origen o la licencia.
3. El sistema asignará el clip a escenas con etiquetas coincidentes y evitará repetirlo en el mismo vídeo.

Si no existe una coincidencia aprobada, se conserva la tarjeta de respaldo; nunca se rellena con gameplay aleatorio.
