'use client';

import { useState, FormEvent, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import styles from './login.module.css';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('testuser');
  const [password, setPassword] = useState('testpass123');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiUrl, setApiUrl] = useState('');

  useEffect(() => {
    // Mostrar la URL de la API para debugging
    const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
    setApiUrl(url);
    console.log('API URL configurada:', url);
  }, []);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await authService.login(username, password);
      router.push('/dashboard');
    } catch (err: any) {
      console.error('Error en login:', err);
      setError(err.message || 'Error al iniciar sesión');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseDemoCredentials = () => {
    setUsername('testuser');
    setPassword('testpass123');
    setError('');
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>Iniciar Sesión</h1>
        
        {process.env.NODE_ENV === 'development' && (
          <div style={{ 
            fontSize: '12px', 
            color: '#666', 
            marginBottom: '10px',
            padding: '8px',
            background: '#f5f5f5',
            borderRadius: '4px'
          }}>
            API: {apiUrl}
          </div>
        )}

        <div style={{ 
          fontSize: '13px', 
          color: '#667eea', 
          marginBottom: '15px',
          padding: '12px',
          background: 'linear-gradient(135deg, #e8f0fe 0%, #f0f7ff 100%)',
          borderRadius: '8px',
          border: '1px solid #b3d9ff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <strong>👤 Usuario de Prueba:</strong> testuser / testpass123
          </div>
          <button
            type="button"
            onClick={handleUseDemoCredentials}
            style={{
              padding: '6px 12px',
              background: '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = '#5568d3';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = '#667eea';
            }}
          >
            Usar
          </button>
        </div>
        
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

          <div className={styles.formGroup}>
            <label htmlFor="password" className={styles.label}>
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={styles.input}
              required
              disabled={isLoading}
              placeholder="Ingrese su contraseña"
            />
          </div>

          <button
            type="submit"
            className={styles.button}
            disabled={isLoading}
          >
            {isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </button>
        </form>
      </div>
    </div>
  );
}
