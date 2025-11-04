'use client';

import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { useMemos } from '@/lib/hooks';
import { useEffect } from 'react';
import LayoutProtected from '@/components/LayoutProtected';
import Link from 'next/link';

export default function ApprovedPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const { memos, isLoading } = useMemos('APPROVED');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated || !user || user.role !== 'DIRECTOR') {
    return null;
  }

  return (
    <LayoutProtected>
      <div>
        <h1 style={{ marginBottom: '20px', fontSize: '28px', fontWeight: 'bold' }}>
          Memos Aprobados
        </h1>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <p>Cargando memos...</p>
          </div>
        ) : memos.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <p style={{ color: '#7f8c8d', fontSize: '16px' }}>No hay memos aprobados</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            {memos.map((memo) => (
              <Link
                key={memo.id}
                href={`/memos/${memo.id}`}
                style={{
                  display: 'block',
                  padding: '20px',
                  backgroundColor: 'white',
                  borderRadius: '8px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                  textDecoration: 'none',
                  color: 'inherit',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
                  <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 'bold', color: '#2c3e50' }}>
                    {memo.subject}
                  </h3>
                  <span
                    style={{
                      padding: '5px 12px',
                      borderRadius: '20px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      backgroundColor: '#27ae60',
                      color: 'white',
                    }}
                  >
                    Aprobado
                  </span>
                </div>
                <p style={{
                  margin: '10px 0',
                  color: '#7f8c8d',
                  fontSize: '14px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                }}>
                  {memo.body}
                </p>
                <div style={{ display: 'flex', gap: '20px', fontSize: '12px', color: '#95a5a6', marginTop: '10px' }}>
                  <span>Autor: {memo.author.first_name || memo.author.username}</span>
                  <span>Fecha: {new Date(memo.created_at).toLocaleDateString('es-ES')}</span>
                  {memo.approved_at && (
                    <span>Aprobado: {new Date(memo.approved_at).toLocaleDateString('es-ES')}</span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </LayoutProtected>
  );
}

