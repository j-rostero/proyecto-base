from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .models import User


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Endpoint para cerrar sesión.
    """
    return Response({
        'success': True,
        'message': 'Sesión cerrada exitosamente'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    """
    Endpoint para obtener el perfil del usuario autenticado.
    """
    serializer = UserSerializer(request.user)
    return Response({
        'success': True,
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def users_list_view(request):
    """
    Endpoint para obtener la lista de usuarios filtrados por rol.
    """
    role = request.query_params.get('role', None)
    queryset = User.objects.all()
    
    if role:
        queryset = queryset.filter(role=role)
    
    serializer = UserSerializer(queryset, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    Endpoint para refrescar el token de acceso.
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response({
            'success': False,
            'message': 'Token de refresh requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        return Response({
            'success': True,
            'data': {
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Token inválido o expirado',
            'error': str(e)
        }, status=status.HTTP_401_UNAUTHORIZED)


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
