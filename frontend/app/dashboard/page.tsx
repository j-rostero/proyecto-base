'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import LayoutProtected from '@/components/LayoutProtected';
import Link from 'next/link';

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated || !user) {
    return null;
  }

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'SECONDARY_USER':
        return 'Redactor';
      case 'DIRECTOR':
        return 'Aprobador';
      case 'AREA_USER':
        return 'Receptor';
      default:
        return role;
    }
  };

  const getQuickLinks = () => {
    if (user.role === 'SECONDARY_USER') {
      return [
        { path: '/dashboard/drafts', label: 'Borradores', icon: '📝' },
        { path: '/dashboard/sent', label: 'Enviados', icon: '📤' },
        { path: '/memos/new', label: 'Nuevo Memo', icon: '➕' },
      ];
    } else if (user.role === 'DIRECTOR') {
      return [
        { path: '/dashboard/inbox', label: 'Pendientes', icon: '📥' },
        { path: '/dashboard/approved', label: 'Aprobados', icon: '✅' },
      ];
    } else {
      return [
        { path: '/dashboard/inbox', label: 'Bandeja de Entrada', icon: '📥' },
      ];
    }
  };

  return (
    <LayoutProtected>
      <div>
        <h1 style={{ marginBottom: '10px', fontSize: '28px', fontWeight: 'bold' }}>
          Bienvenido, {user.first_name || user.username}!
        </h1>
        <p style={{ marginBottom: '30px', color: '#7f8c8d', fontSize: '16px' }}>
          Rol: {getRoleLabel(user.role)}
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '20px',
          marginBottom: '30px',
        }}>
          {getQuickLinks().map((link) => (
            <Link
              key={link.path}
              href={link.path}
              style={{
                display: 'block',
                padding: '30px',
                backgroundColor: 'white',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                textDecoration: 'none',
                color: 'inherit',
                transition: 'transform 0.2s, box-shadow 0.2s',
                textAlign: 'center',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-5px)';
                e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
              }}
            >
              <div style={{ fontSize: '48px', marginBottom: '15px' }}>{link.icon}</div>
              <h3 style={{ margin: 0, fontSize: '20px', fontWeight: 'bold', color: '#2c3e50' }}>
                {link.label}
              </h3>
            </Link>
          ))}
        </div>

        <div style={{
          backgroundColor: 'white',
          padding: '30px',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        }}>
          <h2 style={{ marginTop: 0, marginBottom: '20px', fontSize: '22px' }}>Información del Usuario</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '15px' }}>
            <div>
              <strong>Usuario:</strong> {user.username}
            </div>
            <div>
              <strong>Email:</strong> {user.email}
            </div>
            {user.first_name && (
              <div>
                <strong>Nombre:</strong> {user.first_name} {user.last_name || ''}
              </div>
            )}
            <div>
              <strong>Fecha de registro:</strong> {new Date(user.created_at).toLocaleDateString('es-ES')}
            </div>
          </div>
        </div>
      </div>
    </LayoutProtected>
  );
}

