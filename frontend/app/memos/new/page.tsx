'use client';

import LayoutProtected from '@/components/LayoutProtected';
import MemoForm from '@/components/MemoForm';

export default function NewMemoPage() {
  return (
    <LayoutProtected>
      <div>
        <h1 style={{ marginBottom: '20px', fontSize: '28px', fontWeight: 'bold' }}>
          Nuevo Memorándum
        </h1>
        <MemoForm />
      </div>
    </LayoutProtected>
  );
}

