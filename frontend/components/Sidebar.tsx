'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { User } from '@/lib/auth';
import { useAuthStore } from '@/lib/store';

interface SidebarProps {
  user: User;
}

export default function Sidebar({ user }: SidebarProps) {
  const pathname = usePathname();
  const { logout } = useAuthStore();

  const isActive = (path: string) => pathname === path;

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

  const getNavigationItems = () => {
    const items: Array<{ path: string; label: string }> = [];

    if (user.role === 'SECONDARY_USER') {
      items.push(
        { path: '/dashboard', label: 'Dashboard' },
        { path: '/dashboard/drafts', label: 'Borradores' },
        { path: '/dashboard/sent', label: 'Enviados' },
        { path: '/memos/new', label: 'Nuevo Memo' }
      );
    } else if (user.role === 'DIRECTOR') {
      items.push(
        { path: '/dashboard', label: 'Dashboard' },
        { path: '/dashboard/inbox', label: 'Pendientes' },
        { path: '/dashboard/approved', label: 'Aprobados' }
      );
    } else if (user.role === 'AREA_USER') {
      items.push(
        { path: '/dashboard', label: 'Dashboard' },
        { path: '/dashboard/inbox', label: 'Bandeja de Entrada' }
      );
    }

    return items;
  };

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  return (
    <aside style={{
      width: '250px',
      backgroundColor: '#2c3e50',
      color: 'white',
      padding: '20px',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <div style={{ marginBottom: '30px' }}>
        <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>
          Sistema de Memos
        </h2>
        <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#bdc3c7' }}>
          {getRoleLabel(user.role)}
        </p>
        <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#95a5a6' }}>
          {user.username}
        </p>
      </div>

      <nav style={{ flex: 1 }}>
        {getNavigationItems().map((item) => (
          <Link
            key={item.path}
            href={item.path}
            style={{
              display: 'block',
              padding: '12px 15px',
              marginBottom: '5px',
              borderRadius: '5px',
              textDecoration: 'none',
              color: isActive(item.path) ? '#2c3e50' : 'white',
              backgroundColor: isActive(item.path) ? '#ecf0f1' : 'transparent',
              fontWeight: isActive(item.path) ? 'bold' : 'normal',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              if (!isActive(item.path)) {
                e.currentTarget.style.backgroundColor = '#34495e';
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive(item.path)) {
                e.currentTarget.style.backgroundColor = 'transparent';
              }
            }}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <button
        onClick={handleLogout}
        style={{
          padding: '12px 15px',
          marginTop: '20px',
          backgroundColor: '#e74c3c',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          fontWeight: 'bold',
          width: '100%',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = '#c0392b';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = '#e74c3c';
        }}
      >
        Cerrar Sesión
      </button>
    </aside>
  );
}

