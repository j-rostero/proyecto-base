# Creación de Archivo .gitignore a Nivel Raíz

Se ha creado un archivo `.gitignore` en la raíz del proyecto para gestionar los archivos y directorios que no deben ser rastreados por Git. Este archivo complementa el `.gitignore` existente en el directorio `backend/` y proporciona una cobertura completa para todo el proyecto Django + Next.js.

## Estructura del .gitignore

El archivo `.gitignore` creado incluye exclusiones para varios tipos de archivos y directorios organizados por categorías:

### Python / Django

Incluye todas las exclusiones estándar para proyectos Python, cubriendo archivos compilados, entornos virtuales, y artefactos de construcción. Se excluyen directorios como `__pycache__/`, `venv/`, `env/`, y archivos como `*.pyc`, `*.pyo`, y archivos de distribución como `*.egg-info/`.

Para Django específicamente, se excluyen archivos de base de datos de desarrollo (`db.sqlite3`), archivos de log (`*.log`), y directorios comunes como `/media`, `/staticfiles`, y `/static` que contienen archivos generados.

### Node.js / Next.js

Se excluyen los directorios y archivos comunes de proyectos Node.js, incluyendo `node_modules/` que contiene todas las dependencias del proyecto, y varios tipos de archivos de log de diferentes gestores de paquetes (npm, yarn, pnpm).

Para Next.js específicamente, se excluyen directorios de construcción como `.next/`, `out/`, y `build/`, así como archivos de configuración de despliegue como `.vercel`. También se excluyen archivos TypeScript de construcción (`*.tsbuildinfo`) y el archivo de definiciones de tipos generado (`next-env.d.ts`).

### Variables de Entorno

Se excluyen todos los archivos de variables de entorno, incluyendo `.env`, `.env.local`, y variantes específicas para diferentes entornos (desarrollo, testing, producción). Esto es importante para evitar que información sensible como claves secretas, tokens de API, y configuraciones específicas del entorno se suban al repositorio.

### Sistema Operativo

Se incluyen exclusiones para archivos específicos de diferentes sistemas operativos. Para macOS se excluyen `.DS_Store` y otros archivos de metadatos del sistema. Para Windows se excluyen `Thumbs.db`, `Desktop.ini`, y el directorio `$RECYCLE.BIN/`.

### IDEs y Editores

Se excluyen directorios y archivos de configuración de diferentes entornos de desarrollo integrados, incluyendo `.vscode/` para Visual Studio Code, `.idea/` para IntelliJ IDEA, y archivos temporales de editores como Vim (`*.swp`, `*.swo`).

### Archivos Temporales y Logs

Se excluyen archivos temporales con extensiones comunes como `.tmp`, `.temp`, `.bak`, y `.backup`, así como directorios de logs y archivos de log individuales.

## Ubicación del Archivo

El archivo `.gitignore` se encuentra en la raíz del proyecto:

```
memos/
├── .gitignore          # Archivo creado
├── backend/
│   └── .gitignore      # Archivo existente (complementario)
├── frontend/
└── documentation/
```

## Relación con el .gitignore del Backend

El `.gitignore` en el directorio `backend/` sigue siendo válido y complementa el archivo raíz. El archivo raíz proporciona una cobertura más amplia para todo el proyecto, mientras que el archivo del backend puede contener exclusiones específicas de Django si es necesario.

## Beneficios

La creación de este archivo `.gitignore` a nivel raíz proporciona una capa de protección adicional para evitar que archivos sensibles, dependencias, y artefactos de construcción se suban accidentalmente al repositorio. Esto es especialmente importante para:

- Archivos de configuración con información sensible (`.env`, `.env.local`)
- Dependencias del proyecto que deben ser instaladas localmente (`node_modules/`, `venv/`)
- Archivos de base de datos de desarrollo (`db.sqlite3`)
- Archivos generados automáticamente (`.next/`, `__pycache__/`)
- Configuraciones específicas del IDE del desarrollador

## Verificación

Para verificar que el `.gitignore` está funcionando correctamente, puedes usar:

```bash
git status
```

Este comando mostrará los archivos que Git está rastreando. Los archivos y directorios especificados en `.gitignore` no deberían aparecer en la lista de archivos no rastreados, a menos que hayan sido previamente añadidos al repositorio antes de crear el `.gitignore`.

Si algunos archivos ya estaban siendo rastreados antes de agregarlos al `.gitignore`, necesitarás eliminarlos del índice de Git (pero no del sistema de archivos) usando:

```bash
git rm --cached <archivo>
```

## Notas Adicionales

El archivo incluye una sección comentada para excluir documentación generada si fuera necesario. Esta línea está comentada por defecto, ya que la documentación del proyecto se mantiene en el repositorio.

El `.gitignore` está diseñado para ser compatible con el desarrollo en diferentes sistemas operativos (Linux, macOS, Windows) y diferentes entornos de desarrollo, asegurando que el repositorio permanezca limpio independientemente del entorno de trabajo del desarrollador.

