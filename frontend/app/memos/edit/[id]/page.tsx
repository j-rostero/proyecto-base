'use client';

import { useParams, useRouter } from 'next/navigation';
import { useMemoDetail } from '@/lib/hooks';
import LayoutProtected from '@/components/LayoutProtected';
import MemoForm from '@/components/MemoForm';

export default function EditMemoPage() {
  const params = useParams();
  const router = useRouter();
  const id = parseInt(params.id as string);
  const { memo, isLoading } = useMemoDetail(id);

  if (isLoading) {
    return (
      <LayoutProtected>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <p>Cargando memo...</p>
        </div>
      </LayoutProtected>
    );
  }

  if (!memo) {
    return (
      <LayoutProtected>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <p>Memo no encontrado</p>
        </div>
      </LayoutProtected>
    );
  }

  if (memo.status !== 'DRAFT') {
    return (
      <LayoutProtected>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <p>Este memo no puede ser editado (solo se pueden editar borradores)</p>
          <button
            onClick={() => router.push(`/memos/${id}`)}
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
            }}
          >
            Ver Detalle
          </button>
        </div>
      </LayoutProtected>
    );
  }

  return (
    <LayoutProtected>
      <div>
        <h1 style={{ marginBottom: '20px', fontSize: '28px', fontWeight: 'bold' }}>
          Editar Memorándum
        </h1>
        <MemoForm memo={memo} />
      </div>
    </LayoutProtected>
  );
}

