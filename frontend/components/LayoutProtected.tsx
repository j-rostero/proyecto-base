'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import Sidebar from './Sidebar';

// ToastContainer se cargará dinámicamente solo si react-toastify está instalado
// Por ahora, comentado hasta que se instalen las dependencias
// Para instalar: cd frontend && npm install

interface LayoutProtectedProps {
  children: React.ReactNode;
}

export default function LayoutProtected({ children }: LayoutProtectedProps) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '18px'
      }}>
        Cargando...
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar user={user} />
      <main style={{ flex: 1, padding: '20px', backgroundColor: '#f5f5f5' }}>
        {children}
      </main>
      {/* ToastContainer se mostrará cuando react-toastify esté instalado */}
      {/* Para instalar: cd frontend && npm install */}
    </div>
  );
}

