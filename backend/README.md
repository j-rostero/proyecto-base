# Backend Django REST Framework

## Instalación

1. Crear un entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Copiar el archivo de variables de entorno:
```bash
cp .env.example .env
```

4. Ejecutar migraciones:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Crear un superusuario:
```bash
python manage.py createsuperuser
```

6. Ejecutar el servidor:
```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

## Endpoints

- `POST /api/auth/login/` - Iniciar sesión
- `POST /api/auth/logout/` - Cerrar sesión
- `GET /api/auth/profile/` - Obtener perfil del usuario
- `POST /api/auth/refresh/` - Refrescar token de acceso

