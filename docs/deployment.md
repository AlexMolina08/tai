# Despliegue y sincronización

## GitHub Pages

La web se publica mediante `.github/workflows/deploy-pages.yml` en cada envío a `main`. El trabajo instala las dependencias, compila la aplicación y entrega `dist/` a GitHub Pages.

El flujo necesita esta variable y este secreto en el repositorio:

- Variable `VITE_SUPABASE_URL`: URL pública del proyecto Supabase.
- Secreto `VITE_SUPABASE_PUBLISHABLE_KEY`: clave publicable del proyecto.

No se incluye la contraseña de PostgreSQL en la compilación, en GitHub ni en el navegador.

## Supabase

La migración `supabase/migrations/20260802165000_create_tai_progress_sync.sql` crea:

- `tai_progress_snapshots`, sin acceso directo para usuarios anónimos.
- La función `tai_sync_progress`, único punto público de lectura y escritura.

La función convierte el código de sincronización en SHA-256 y utiliza ese hash como identificador. El código original no se almacena. Un código largo y aleatorio permite compartir la misma copia entre dispositivos sin crear una cuenta.

La aplicación conserva IndexedDB como fuente local y funciona sin conexión. Cuando hay código configurado:

- sincroniza al abrir la aplicación;
- sincroniza al cerrar un test o cambiar una favorita;
- permite una actualización manual desde Progreso.

En caso de dos cambios sin conexión, prevalece la copia con la fecha de modificación más reciente. La exportación JSON continúa disponible como copia de seguridad manual.

## Aplicar la migración de nuevo

Con el proyecto enlazado al CLI:

```bash
supabase link --project-ref TU_REFERENCIA
supabase db push
```

También puede aplicarse por una conexión PostgreSQL con SSL. La contraseña debe introducirse de forma interactiva o mediante un gestor de secretos; nunca debe guardarse en el repositorio.
