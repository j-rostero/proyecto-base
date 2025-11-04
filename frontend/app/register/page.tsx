'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authService } from '@/lib/auth';
import { useAuthStore } from '@/lib/store';
import styles from './register.module.css';

export default function RegisterPage() {
  const router = useRouter();
  const { setUser } = useAuthStore();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    role: 'SECONDARY_USER' as 'SECONDARY_USER' | 'DIRECTOR' | 'AREA_USER',
  });
  const [error, setError] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Limpiar error específico cuando el usuario empieza a escribir
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setErrors({});
    setIsLoading(true);

    try {
      const { user } = await authService.register(formData);
      // Actualizar el store
      setUser(user);
      router.push('/dashboard');
    } catch (err: any) {
      console.error('Error en registro:', err);
      
      // Manejar errores de validación del backend
      if (err.response?.data?.errors) {
        const backendErrors = err.response.data.errors;
        const formattedErrors: Record<string, string> = {};
        
        Object.keys(backendErrors).forEach(key => {
          if (Array.isArray(backendErrors[key])) {
            formattedErrors[key] = backendErrors[key][0];
          } else {
            formattedErrors[key] = backendErrors[key];
          }
        });
        
        setErrors(formattedErrors);
      } else {
        setError(err.message || 'Error al registrar usuario');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>Registro de Usuario</h1>
        
        {error && (
          <div className={styles.errorMessage}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="username" className={styles.label}>
              Usuario <span className={styles.required}>*</span>
            </label>
            <input
              id="username"
              name="username"
              type="text"
              value={formData.username}
              onChange={handleChange}
              className={`${styles.input} ${errors.username ? styles.inputError : ''}`}
              required
              disabled={isLoading}
              placeholder="Ingrese su usuario"
            />
            {errors.username && (
              <span className={styles.fieldError}>{errors.username}</span>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="email" className={styles.label}>
              Email <span className={styles.required}>*</span>
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              className={`${styles.input} ${errors.email ? styles.inputError : ''}`}
              required
              disabled={isLoading}
              placeholder="correo@ejemplo.com"
            />
            {errors.email && (
              <span className={styles.fieldError}>{errors.email}</span>
            )}
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label htmlFor="first_name" className={styles.label}>
                Nombre
              </label>
              <input
                id="first_name"
                name="first_name"
                type="text"
                value={formData.first_name}
                onChange={handleChange}
                className={styles.input}
                disabled={isLoading}
                placeholder="Nombre"
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="last_name" className={styles.label}>
                Apellido
              </label>
              <input
                id="last_name"
                name="last_name"
                type="text"
                value={formData.last_name}
                onChange={handleChange}
                className={styles.input}
                disabled={isLoading}
                placeholder="Apellido"
              />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="role" className={styles.label}>
              Rol <span className={styles.required}>*</span>
            </label>
            <select
              id="role"
              name="role"
              value={formData.role}
              onChange={handleChange}
              className={styles.input}
              required
              disabled={isLoading}
            >
              <option value="SECONDARY_USER">Redactor</option>
              <option value="DIRECTOR">Aprobador</option>
              <option value="AREA_USER">Receptor</option>
            </select>
            {errors.role && (
              <span className={styles.fieldError}>{errors.role}</span>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password" className={styles.label}>
              Contraseña <span className={styles.required}>*</span>
            </label>
            <input
              id="password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              className={`${styles.input} ${errors.password ? styles.inputError : ''}`}
              required
              disabled={isLoading}
              placeholder="Mínimo 8 caracteres"
            />
            {errors.password && (
              <span className={styles.fieldError}>{errors.password}</span>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password_confirm" className={styles.label}>
              Confirmar Contraseña <span className={styles.required}>*</span>
            </label>
            <input
              id="password_confirm"
              name="password_confirm"
              type="password"
              value={formData.password_confirm}
              onChange={handleChange}
              className={`${styles.input} ${errors.password_confirm ? styles.inputError : ''}`}
              required
              disabled={isLoading}
              placeholder="Repita su contraseña"
            />
            {errors.password_confirm && (
              <span className={styles.fieldError}>{errors.password_confirm}</span>
            )}
          </div>

          <button
            type="submit"
            className={styles.button}
            disabled={isLoading}
          >
            {isLoading ? 'Registrando...' : 'Registrarse'}
          </button>

          <div className={styles.loginLink}>
            ¿Ya tienes una cuenta?{' '}
            <Link href="/login" className={styles.link}>
              Inicia sesión aquí
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}

