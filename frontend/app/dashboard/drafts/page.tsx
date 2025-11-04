'use client';

import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { useMemos } from '@/lib/hooks';
import { useEffect } from 'react';
import LayoutProtected from '@/components/LayoutProtected';
import Link from 'next/link';

export default function DraftsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const { memos: drafts, isLoading: isLoadingDrafts } = useMemos('DRAFT');
  const { memos: rejected, isLoading: isLoadingRejected } = useMemos('REJECTED');
  const isLoading = isLoadingDrafts || isLoadingRejected;
  const allMemos = [...drafts, ...rejected];

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated || !user || user.role !== 'SECONDARY_USER') {
    return null;
  }

  return (
    <LayoutProtected>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h1 style={{ margin: 0, fontSize: '28px', fontWeight: 'bold' }}>Borradores y Rechazados</h1>
          <Link
            href="/memos/new"
            style={{
              padding: '10px 20px',
              backgroundColor: '#3498db',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '5px',
              fontWeight: 'bold',
            }}
          >
            Nuevo Memo
          </Link>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <p>Cargando memos...</p>
          </div>
        ) : allMemos.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <p style={{ color: '#7f8c8d', fontSize: '16px' }}>No hay borradores o memos rechazados</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            {allMemos.map((memo) => (
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
                  borderLeft: `4px solid ${memo.status === 'REJECTED' ? '#e74c3c' : '#3498db'}`,
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
                      backgroundColor: memo.status === 'REJECTED' ? '#e74c3c' : '#3498db',
                      color: 'white',
                    }}
                  >
                    {memo.status === 'REJECTED' ? 'Rechazado' : 'Borrador'}
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
                {memo.status === 'REJECTED' && memo.rejection_reason && (
                  <div style={{
                    marginTop: '10px',
                    padding: '10px',
                    backgroundColor: '#fee',
                    borderRadius: '5px',
                    borderLeft: '3px solid #e74c3c',
                  }}>
                    <strong>Motivo de rechazo:</strong> {memo.rejection_reason}
                  </div>
                )}
                <div style={{ display: 'flex', gap: '20px', fontSize: '12px', color: '#95a5a6', marginTop: '10px' }}>
                  <span>Fecha: {new Date(memo.created_at).toLocaleDateString('es-ES')}</span>
                  {memo.attachments_count && memo.attachments_count > 0 && (
                    <span>Adjuntos: {memo.attachments_count}</span>
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

