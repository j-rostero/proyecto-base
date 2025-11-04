# Proyecto de Autenticación con Django REST Framework y Next.js

## Resumen

Este proyecto implementa un sistema completo de autenticación con usuario y contraseña, compuesto por dos aplicaciones principales: un backend desarrollado con Django REST Framework que proporciona una API REST para la autenticación mediante tokens JWT, y un frontend construido con Next.js y TypeScript que consume esta API y gestiona la sesión del usuario en el navegador.

## Estructura del Proyecto

El proyecto está organizado en dos directorios principales:

```
memos/
├── backend/          # Aplicación Django REST Framework
│   ├── accounts/     # App de autenticación
│   ├── config/       # Configuración de Django
│   └── manage.py
└── frontend/         # Aplicación Next.js con TypeScript
    ├── app/          # Páginas y rutas
    └── lib/          # Utilidades y servicios
```

## Backend: Django REST Framework

### Configuración Inicial

El backend utiliza Django 5.0.6 y Django REST Framework 3.14.0 para construir una API REST. La autenticación se implementa mediante JSON Web Tokens (JWT) usando la librería `djangorestframework-simplejwt`.

### Modelo de Usuario

Se creó un modelo personalizado de usuario que extiende `AbstractUser` de Django, permitiendo agregar campos adicionales como `email` único y timestamps de creación y actualización:

```12:23:backend/accounts/models.py
class User(AbstractUser):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.username
```

Este modelo se configura como el modelo de usuario por defecto en `settings.py` mediante `AUTH_USER_MODEL = 'accounts.User'`.

### Serializadores

Los serializadores gestionan la validación y transformación de datos. El `LoginSerializer` valida las credenciales del usuario y autentica utilizando el sistema de autenticación de Django:

```11:27:backend/accounts/serializers.py
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(request=self.context.get('request'),
                              username=username, password=password)
            if not user:
                raise serializers.ValidationError('Credenciales inválidas.')
            if not user.is_active:
                raise serializers.ValidationError('Usuario inactivo.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Debe ingresar usuario y contraseña.')
        return attrs
```

El método `validate` utiliza `authenticate` de Django para verificar las credenciales. Si las credenciales son válidas y el usuario está activo, almacena el objeto usuario en los atributos validados para su uso posterior en la vista.

### Endpoints de Autenticación

La aplicación expone cuatro endpoints principales para la gestión de autenticación:

**Login (`POST /api/auth/login/`)**: Recibe un objeto JSON con `username` y `password`, autentica al usuario y retorna un objeto con los datos del usuario y los tokens JWT (access y refresh):

```12:31:backend/accounts/views.py
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Endpoint para autenticación de usuarios.
    Recibe username y password, retorna tokens JWT.
    """
    serializer = LoginSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Login exitoso',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Error en la autenticación',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)
```

El endpoint utiliza `RefreshToken.for_user()` para generar los tokens JWT. El token de acceso tiene una duración de una hora, mientras que el token de refresh tiene una duración de siete días.

**Logout (`POST /api/auth/logout/`)**: Permite cerrar sesión. En la implementación actual, simplemente retorna una respuesta exitosa, ya que la invalidación del token se maneja en el cliente al eliminar los tokens del almacenamiento local.

**Perfil de Usuario (`GET /api/auth/profile/`)**: Retorna la información del usuario autenticado. Requiere autenticación mediante el token JWT en el header `Authorization: Bearer <token>`.

**Refresh Token (`POST /api/auth/refresh/`)**: Permite generar un nuevo token de acceso utilizando el token de refresh cuando el token de acceso ha expirado.

### Configuración de JWT

La configuración de JWT se define en `settings.py`:

```107:117:backend/config/settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}
```

`ROTATE_REFRESH_TOKENS` está configurado en `True`, lo que significa que cada vez que se refresca el token de acceso, se genera un nuevo token de refresh, mejorando la seguridad del sistema.

### Configuración de CORS

Para permitir que el frontend de Next.js se comunique con el backend, se configuró `django-cors-headers`:

```119:125:backend/config/settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True
```

Esto permite que las peticiones desde `localhost:3000` (donde corre Next.js por defecto) puedan acceder a la API.

## Frontend: Next.js con TypeScript

### Configuración del Cliente API

El frontend utiliza Axios para realizar las peticiones HTTP. Se creó una clase `ApiClient` que encapsula la configuración de Axios y maneja la autenticación mediante interceptores:

```12:38:frontend/lib/api.ts
  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use(
      (config) => {
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem('access_token');
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }
```

El interceptor de peticiones añade automáticamente el token de acceso al header `Authorization` si existe en `localStorage`. El interceptor de respuestas detecta errores 401 (no autorizado) y redirige al usuario a la página de login, limpiando los datos de sesión almacenados.

### Servicio de Autenticación

El servicio `authService` proporciona métodos de alto nivel para interactuar con la autenticación:

```9:40:frontend/lib/auth.ts
  async login(username: string, password: string): Promise<{ user: User; tokens: AuthTokens }> {
    const response = await apiClient.login(username, password);
    
    if (response.success && response.data) {
      const { user, tokens } = response.data;
      
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
        localStorage.setItem('user', JSON.stringify(user));
      }
      
      return { user, tokens };
    }
    
    throw new Error(response.message || 'Error en el login');
  },

  async logout(): Promise<void> {
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('Error al cerrar sesión:', error);
    } finally {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
      }
    }
  },

  getUser(): User | null {
    if (typeof window === 'undefined') return null;
    
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;
    
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  },
```

El método `login` almacena los tokens y la información del usuario en `localStorage` para persistir la sesión entre recargas de página. El método `getUser` verifica si el código se ejecuta en el navegador (usando `typeof window !== 'undefined'`) antes de acceder a `localStorage`, lo cual es necesario debido a que Next.js renderiza componentes tanto en el servidor como en el cliente.

### Página de Login

La página de login utiliza el App Router de Next.js 14:

```9:43:frontend/app/login/page.tsx
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await authService.login(username, password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Error al iniciar sesión');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>Iniciar Sesión</h1>
        
        {error && (
          <div className={styles.errorMessage}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="username" className={styles.label}>
              Usuario
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={styles.input}
              required
              disabled={isLoading}
              placeholder="Ingrese su usuario"
            />
          </div>
```

El componente utiliza el hook `useRouter` de Next.js para la navegación programática. Después de un login exitoso, redirige al usuario al dashboard. El estado de carga se maneja para deshabilitar el formulario durante la petición y mostrar un mensaje apropiado al usuario.

### Página del Dashboard

El dashboard verifica la autenticación antes de renderizar el contenido:

```12:25:frontend/app/dashboard/page.tsx
  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }

    const currentUser = authService.getUser();
    setUser(currentUser);
    setIsLoading(false);
  }, [router]);

  const handleLogout = async () => {
    await authService.logout();
    router.push('/login');
  };
```

Si el usuario no está autenticado, se redirige automáticamente a la página de login. El dashboard muestra la información del usuario y proporciona un botón para cerrar sesión que limpia los datos almacenados y redirige al login.

### Gestión de Sesión

La sesión se gestiona completamente en el cliente mediante `localStorage`. Los tokens JWT se almacenan localmente y se incluyen automáticamente en cada petición mediante el interceptor de Axios. Esta implementación es adecuada para aplicaciones que no requieren características avanzadas de seguridad como tokens HTTP-only o refresh automático.

## Instalación y Ejecución

### Backend

El backend está configurado para usar SQLite por defecto, lo que facilita el desarrollo sin necesidad de configurar una base de datos externa. La base de datos se creará automáticamente en `backend/db.sqlite3` cuando se ejecuten las migraciones.

1. Navegar al directorio del backend y crear un entorno virtual:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

3. Crear el archivo de variables de entorno:
```bash
cat > .env << EOF
SECRET_KEY=django-insecure-dev-key-change-in-production
DEBUG=True
EOF
```

4. Ejecutar las migraciones (esto creará la base de datos SQLite):
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Crear un superusuario para acceder al admin de Django (opcional):
```bash
python manage.py createsuperuser
```

6. Ejecutar el servidor de desarrollo:
```bash
python manage.py runserver
```

El backend estará disponible en `http://localhost:8000`. La base de datos SQLite se ubicará en `backend/db.sqlite3`.

### Frontend

1. Navegar al directorio del frontend e instalar las dependencias:
```bash
cd frontend
npm install
```

2. Configurar las variables de entorno:
```bash
cp .env.local.example .env.local
```

Editar `.env.local` y asegurarse de que la URL de la API sea correcta:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

3. Ejecutar el servidor de desarrollo:
```bash
npm run dev
```

El frontend estará disponible en `http://localhost:3000`.

## Flujo de Autenticación

1. El usuario accede a la aplicación y es redirigido a `/login` si no está autenticado.
2. El usuario ingresa su usuario y contraseña y envía el formulario.
3. El frontend realiza una petición `POST` a `/api/auth/login/` con las credenciales.
4. El backend valida las credenciales y retorna los tokens JWT junto con la información del usuario.
5. El frontend almacena los tokens y la información del usuario en `localStorage`.
6. El usuario es redirigido al dashboard.
7. Las peticiones subsiguientes incluyen automáticamente el token de acceso en el header `Authorization`.
8. Si el token expira, el frontend puede usar el token de refresh para obtener un nuevo token de acceso.
9. Al cerrar sesión, los tokens se eliminan de `localStorage` y el usuario es redirigido al login.

## Consideraciones de Seguridad

La implementación actual utiliza tokens JWT almacenados en `localStorage`. Aunque esto es funcional para aplicaciones básicas, para aplicaciones de producción se recomienda considerar:

- Almacenar tokens en cookies HTTP-only para prevenir ataques XSS.
- Implementar refresh automático de tokens antes de que expiren.
- Agregar protección CSRF si se utilizan cookies.
- Implementar rate limiting en los endpoints de autenticación.
- Utilizar HTTPS en producción.

## Cambios Realizados

1. **Backend Django REST Framework**: Se creó una aplicación Django con autenticación JWT, incluyendo modelo de usuario personalizado, serializadores, vistas y endpoints de autenticación.

2. **Frontend Next.js**: Se implementó una aplicación Next.js con TypeScript que incluye página de login, dashboard, cliente API con interceptores, y gestión de sesión mediante localStorage.

3. **Integración**: Se configuró CORS para permitir la comunicación entre frontend y backend, y se implementó el flujo completo de autenticación desde el login hasta el dashboard.

4. **Documentación**: Se creó documentación completa del proyecto explicando la arquitectura, implementación y uso del sistema.

