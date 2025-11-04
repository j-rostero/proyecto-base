# Módulo de Registro de Usuarios

## Resumen

Este documento describe la implementación completa del módulo de registro de usuarios para el sistema de gestión de memorándums. El módulo permite a los usuarios crear nuevas cuentas con validación de datos en el backend y una interfaz de usuario intuitiva en el frontend.

## Backend: Django REST Framework

### Serializer de Registro

Se creó el `RegisterSerializer` en `backend/accounts/serializers.py` que extiende `ModelSerializer` y gestiona la validación y creación de nuevos usuarios. El serializer incluye validaciones para garantizar la integridad de los datos:

```35:77:backend/accounts/serializers.py
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 
                  'first_name', 'last_name', 'role']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este email ya está registrado.')
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Este usuario ya existe.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user
```

El serializer utiliza `validate_password` de Django para aplicar las reglas de validación de contraseñas configuradas en el proyecto. Los métodos `validate_email` y `validate_username` verifican que no existan usuarios con el mismo email o nombre de usuario. El método `validate` comprueba que las contraseñas coincidan, y `create` utiliza `create_user` de Django para crear el usuario con la contraseña correctamente hasheada.

### Vista de Registro

La vista `register_view` en `backend/accounts/views.py` maneja las peticiones POST para el registro de usuarios:

```116:146:backend/accounts/views.py
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Endpoint para registro de nuevos usuarios.
    Recibe username, email, password, password_confirm y opcionalmente first_name, last_name, role.
    Retorna tokens JWT y datos del usuario.
    """
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Usuario registrado exitosamente',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': 'Error en el registro',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)
```

La vista utiliza el decorador `@permission_classes([AllowAny])` para permitir que usuarios no autenticados puedan registrarse. Al validar correctamente los datos, crea el usuario y genera tokens JWT automáticamente, permitiendo que el usuario quede autenticado inmediatamente después del registro sin necesidad de hacer login por separado.

### Configuración de Rutas

Se agregó la ruta de registro en `backend/accounts/urls.py`:

```9:9:backend/accounts/urls.py
    path('auth/register/', views.register_view, name='register'),
```

El endpoint está disponible en `POST /api/auth/register/` y acepta un objeto JSON con los campos del formulario de registro.

## Frontend: Next.js con TypeScript

### Cliente API

Se agregó el método `register` en `frontend/lib/api.ts` para realizar las peticiones de registro:

```68:84:frontend/lib/api.ts
  async register(data: {
    username: string;
    email: string;
    password: string;
    password_confirm: string;
    first_name?: string;
    last_name?: string;
    role?: 'SECONDARY_USER' | 'DIRECTOR' | 'AREA_USER';
  }): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.post('/auth/register/', data);
      return response.data;
    } catch (error: any) {
      console.error('Error en registro:', error);
      throw this.handleError(error);
    }
  }
```

El método acepta un objeto con los datos del formulario y realiza una petición POST al endpoint de registro. El manejo de errores captura las respuestas del backend y las transforma en excepciones con mensajes descriptivos.

### Servicio de Autenticación

Se extendió el servicio `authService` en `frontend/lib/auth.ts` con el método `register`:

```37:61:frontend/lib/auth.ts
  async register(data: {
    username: string;
    email: string;
    password: string;
    password_confirm: string;
    first_name?: string;
    last_name?: string;
    role?: 'SECONDARY_USER' | 'DIRECTOR' | 'AREA_USER';
  }): Promise<{ user: User; tokens: AuthTokens }> {
    const response = await apiClient.register(data);
    
    if (response.success && response.data) {
      const { user, tokens } = response.data;
      
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
        localStorage.setItem('user', JSON.stringify(user));
      }
      
      return { user, tokens };
    }
    
    throw new Error(response.message || 'Error en el registro');
  },
```

El método procesa la respuesta del servidor, almacena los tokens y la información del usuario en `localStorage`, y actualiza el estado de autenticación. Esto permite que el usuario quede autenticado inmediatamente después del registro.

### Página de Registro

Se creó la página de registro en `frontend/app/register/page.tsx` utilizando el App Router de Next.js. La página incluye un formulario completo con validación en el cliente y manejo de errores del backend:

La página utiliza React hooks para gestionar el estado del formulario, los errores de validación y el estado de carga. El formulario incluye campos para username, email, nombre, apellido, rol, contraseña y confirmación de contraseña. Los campos opcionales permiten flexibilidad en el registro, mientras que los campos requeridos garantizan la integridad de los datos.

El componente maneja los errores de validación del backend mostrando mensajes específicos para cada campo. Cuando el backend retorna errores de validación, estos se extraen y se muestran junto al campo correspondiente, proporcionando retroalimentación inmediata al usuario.

Después de un registro exitoso, el usuario es redirigido automáticamente al dashboard y queda autenticado en el sistema. El estado de autenticación se actualiza mediante el store de Zustand, sincronizando la información del usuario en toda la aplicación.

### Estilos de la Página de Registro

Se crearon estilos personalizados en `frontend/app/register/register.module.css` que mantienen consistencia visual con la página de login. Los estilos incluyen:

- Diseño responsive que se adapta a diferentes tamaños de pantalla
- Indicadores visuales para campos con errores (borde rojo)
- Mensajes de error específicos por campo
- Diseño en dos columnas para nombre y apellido en pantallas grandes
- Transiciones suaves para mejorar la experiencia de usuario

El diseño utiliza gradientes y sombras consistentes con el resto de la aplicación, creando una experiencia visual coherente.

## Flujo de Registro

El flujo completo de registro funciona de la siguiente manera:

1. El usuario accede a la página `/register` y completa el formulario con sus datos.
2. Al enviar el formulario, el frontend realiza una petición POST a `/api/auth/register/` con los datos del formulario.
3. El backend valida los datos utilizando el `RegisterSerializer`, verificando que el email y username no existan, que las contraseñas coincidan, y que la contraseña cumpla con los requisitos de seguridad.
4. Si la validación es exitosa, se crea el usuario en la base de datos y se generan tokens JWT.
5. El backend retorna los tokens y la información del usuario al frontend.
6. El frontend almacena los tokens en `localStorage` y actualiza el estado de autenticación.
7. El usuario es redirigido automáticamente al dashboard, quedando autenticado en el sistema.

Si ocurren errores de validación, el backend retorna un objeto con los errores específicos por campo, y el frontend los muestra junto a cada campo correspondiente, permitiendo al usuario corregir los errores sin perder los datos ya ingresados.

## Validaciones Implementadas

### Backend

- Validación de email único: Verifica que no exista otro usuario con el mismo email.
- Validación de username único: Verifica que no exista otro usuario con el mismo username.
- Validación de contraseñas coincidentes: Verifica que `password` y `password_confirm` sean iguales.
- Validación de contraseña segura: Utiliza los validadores de Django para asegurar que la contraseña cumpla con los requisitos de seguridad configurados.
- Campos requeridos: `username`, `email`, `password`, `password_confirm` y `role` son obligatorios.

### Frontend

- Validación HTML5: Los campos requeridos utilizan el atributo `required` para validación nativa del navegador.
- Validación de tipo: El campo email utiliza `type="email"` para validación de formato.
- Manejo de errores del backend: Los errores retornados por el backend se muestran junto a cada campo correspondiente.
- Limpieza de errores: Los errores se limpian automáticamente cuando el usuario comienza a editar un campo.

## Integración con el Sistema de Autenticación

El módulo de registro está completamente integrado con el sistema de autenticación existente. Después de un registro exitoso, el usuario recibe tokens JWT que se almacenan en `localStorage` de la misma manera que en el proceso de login. Esto permite que el usuario pueda utilizar todas las funcionalidades de la aplicación inmediatamente después del registro.

El módulo respeta la estructura de roles del sistema, permitiendo que los usuarios se registren con cualquiera de los tres roles disponibles: `SECONDARY_USER` (Redactor), `DIRECTOR` (Aprobador), o `AREA_USER` (Receptor). El rol por defecto es `SECONDARY_USER` según la configuración del modelo.

## Consideraciones de Seguridad

La implementación incluye varias medidas de seguridad:

- Las contraseñas se hashean automáticamente utilizando el sistema de autenticación de Django antes de almacenarse en la base de datos.
- La validación de contraseñas utiliza los validadores configurados en Django, que pueden incluir requisitos de longitud, complejidad y caracteres especiales.
- Los tokens JWT se generan utilizando la misma configuración que el sistema de login, garantizando consistencia en la seguridad.
- El endpoint de registro está protegido contra ataques de fuerza bruta mediante las validaciones del serializer y la estructura de respuesta consistente.

Para producción, se recomienda considerar implementaciones adicionales como:

- Rate limiting en el endpoint de registro para prevenir abuso.
- Verificación de email mediante tokens de confirmación.
- Implementación de CAPTCHA para prevenir registros automatizados.
- Políticas de contraseña más estrictas según los requisitos de seguridad de la organización.

## Cambios Realizados

1. **Backend Django REST Framework**: Se creó el `RegisterSerializer` con validaciones completas, la vista `register_view` que maneja el registro y genera tokens JWT automáticamente, y se agregó la ruta `/api/auth/register/` en las URLs.

2. **Frontend Next.js**: Se agregó el método `register` en el cliente API y en el servicio de autenticación, se creó la página de registro con formulario completo y manejo de errores, y se implementaron estilos consistentes con el diseño de la aplicación.

3. **Integración**: El módulo está completamente integrado con el sistema de autenticación existente, permitiendo que los usuarios queden autenticados inmediatamente después del registro.

4. **Documentación**: Se creó documentación completa del módulo explicando la implementación, el flujo de registro y las validaciones implementadas.

