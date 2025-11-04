'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService, User } from '@/lib/auth';
import styles from './dashboard.module.css';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <p>Cargando...</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.headerTitle}>Dashboard</h1>
          <button onClick={handleLogout} className={styles.logoutButton}>
            Cerrar Sesión
          </button>
        </div>
      </header>

      <main className={styles.main}>
        <div className={styles.welcomeCard}>
          <h2 className={styles.welcomeTitle}>
            Bienvenido, {user.first_name || user.username}!
          </h2>
          <p className={styles.welcomeText}>
            Has iniciado sesión exitosamente en el sistema.
          </p>
        </div>

        <div className={styles.grid}>
          <div className={styles.card}>
            <h3 className={styles.cardTitle}>Información del Usuario</h3>
            <div className={styles.cardContent}>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Usuario:</span>
                <span className={styles.infoValue}>{user.username}</span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Email:</span>
                <span className={styles.infoValue}>{user.email}</span>
              </div>
              {user.first_name && (
                <div className={styles.infoRow}>
                  <span className={styles.infoLabel}>Nombre:</span>
                  <span className={styles.infoValue}>
                    {user.first_name} {user.last_name || ''}
                  </span>
                </div>
              )}
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Fecha de registro:</span>
                <span className={styles.infoValue}>
                  {new Date(user.created_at).toLocaleDateString('es-ES')}
                </span>
              </div>
            </div>
          </div>

          <div className={styles.card}>
            <h3 className={styles.cardTitle}>Estado de la Sesión</h3>
            <div className={styles.cardContent}>
              <div className={styles.statusBadge}>
                <span className={styles.statusDot}></span>
                Sesión activa
              </div>
              <p className={styles.statusText}>
                Tu sesión está activa y segura. Puedes navegar por el sistema
                sin problemas.
              </p>
            </div>
          </div>

          <div className={styles.card}>
            <h3 className={styles.cardTitle}>Accesos Rápidos</h3>
            <div className={styles.cardContent}>
              <div className={styles.quickLinks}>
                <button className={styles.quickLinkButton}>
                  Ver Perfil
                </button>
                <button className={styles.quickLinkButton}>
                  Configuración
                </button>
                <button className={styles.quickLinkButton}>
                  Ayuda
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

