'use client';

import { useState, useEffect } from 'react';
import { memosService, CreateMemoData, UpdateMemoData, Memo } from '@/lib/memos';
import { useRouter } from 'next/navigation';

// Importación dinámica de react-toastify
let toast: any = null;
try {
  const toastify = require('react-toastify');
  toast = toastify.toast;
} catch (e) {
  console.warn('react-toastify no está instalado. Ejecuta: npm install');
  // Fallback: función toast que no hace nada
  toast = {
    success: (msg: string) => console.log('SUCCESS:', msg),
    error: (msg: string) => console.error('ERROR:', msg),
    info: (msg: string) => console.log('INFO:', msg),
    warning: (msg: string) => console.warn('WARNING:', msg),
  };
}

// react-quill no está disponible - usando textarea simple
// Para instalar: cd frontend && npm install react-quill
// Una vez instalado, puedes descomentar las líneas de abajo y usar ReactQuill
// const ReactQuill = dynamic(() => import('react-quill'), { ssr: false });
const reactQuillAvailable = false;

interface MemoFormProps {
  memo?: Memo;
  onSuccess?: () => void;
}

export default function MemoForm({ memo, onSuccess }: MemoFormProps) {
  const router = useRouter();
  const [subject, setSubject] = useState(memo?.subject || '');
  const [body, setBody] = useState(memo?.body || '');
  const [recipientIds, setRecipientIds] = useState<number[]>(memo?.recipients.map(r => r.id) || []);
  const [approverId, setApproverId] = useState<number | null>(memo?.approver?.id || null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [errors, setErrors] = useState<{ subject?: string; body?: string }>({});

  useEffect(() => {
    // Cargar usuarios desde la API
    const loadUsers = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('http://localhost:8000/api/users/', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        const data = await response.json();
        if (data.success && data.data) {
          setUsers(data.data);
        }
      } catch (error) {
        console.error('Error loading users:', error);
      }
    };
    loadUsers();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validación básica
    const newErrors: { subject?: string; body?: string } = {};
    if (!subject.trim()) {
      newErrors.subject = 'El asunto es requerido';
    }
    if (!body.trim()) {
      newErrors.body = 'El contenido es requerido';
    }
    
    setErrors(newErrors);
    
    if (Object.keys(newErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      const submitData: any = {
        subject: subject.trim(),
        body: body.trim(),
      };
      
      if (recipientIds.length > 0) {
        submitData.recipient_ids = recipientIds;
      }
      
      if (approverId) {
        submitData.approver_id = approverId;
      }
      
      if (memo) {
        await memosService.updateMemo(memo.id, submitData);
        toast.success('Memo actualizado exitosamente');
      } else {
        await memosService.createMemo(submitData);
        toast.success('Memo creado exitosamente');
      }
      if (onSuccess) {
        onSuccess();
      } else {
        router.push('/dashboard/drafts');
      }
    } catch (error: any) {
      toast.error(error.message || 'Error al guardar el memo');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleFileUpload = async () => {
    if (!memo || !selectedFile) return;

    setIsUploading(true);
    try {
      await memosService.uploadAttachment(memo.id, selectedFile);
      toast.success('Archivo subido exitosamente');
      setSelectedFile(null);
    } catch (error: any) {
      toast.error(error.message || 'Error al subir el archivo');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRecipientChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedOptions = Array.from(e.target.selectedOptions);
    const ids = selectedOptions.map(option => parseInt(option.value));
    setRecipientIds(ids);
  };

  const recipients = users.filter(u => u.role === 'AREA_USER');
  const approvers = users.filter(u => u.role === 'DIRECTOR');

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
          Asunto *
        </label>
        <input
          type="text"
          value={subject}
          onChange={(e) => {
            setSubject(e.target.value);
            if (errors.subject) {
              setErrors({ ...errors, subject: undefined });
            }
          }}
          style={{
            width: '100%',
            padding: '10px',
            border: errors.subject ? '1px solid #e74c3c' : '1px solid #ddd',
            borderRadius: '5px',
            fontSize: '16px',
          }}
          placeholder="Ingrese el asunto del memo"
        />
        {errors.subject && (
          <span style={{ color: '#e74c3c', fontSize: '14px', display: 'block', marginTop: '5px' }}>
            {errors.subject}
          </span>
        )}
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
          Contenido *
        </label>
        <textarea
          value={body}
          onChange={(e) => {
            setBody(e.target.value);
            if (errors.body) {
              setErrors({ ...errors, body: undefined });
            }
          }}
          style={{
            width: '100%',
            minHeight: '200px',
            padding: '10px',
            border: errors.body ? '1px solid #e74c3c' : '1px solid #ddd',
            borderRadius: '5px',
            fontSize: '16px',
            marginBottom: '50px',
            fontFamily: 'inherit',
            resize: 'vertical',
          }}
          placeholder="Ingrese el contenido del memo"
        />
        {!reactQuillAvailable && (
          <small style={{ color: '#7f8c8d', fontSize: '12px', display: 'block', marginTop: '5px' }}>
            💡 Para un editor de texto enriquecido, instala react-quill: cd frontend && npm install
          </small>
        )}
        {errors.body && (
          <span style={{ color: '#e74c3c', fontSize: '14px', display: 'block', marginTop: '5px' }}>
            {errors.body}
          </span>
        )}
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
          Destinatarios
        </label>
        <select
          multiple
          value={recipientIds.map(String)}
          onChange={handleRecipientChange}
          style={{
            width: '100%',
            padding: '10px',
            border: '1px solid #ddd',
            borderRadius: '5px',
            fontSize: '16px',
            minHeight: '100px',
          }}
        >
          {recipients.map((user) => (
            <option key={user.id} value={user.id}>
              {user.first_name || ''} {user.last_name || ''} ({user.username})
            </option>
          ))}
        </select>
        <small style={{ color: '#7f8c8d', fontSize: '12px' }}>
          Mantén presionado Ctrl (o Cmd en Mac) para seleccionar múltiples destinatarios
        </small>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
          Aprobador
        </label>
        <select
          value={approverId || ''}
          onChange={(e) => setApproverId(e.target.value ? parseInt(e.target.value) : null)}
          style={{
            width: '100%',
            padding: '10px',
            border: '1px solid #ddd',
            borderRadius: '5px',
            fontSize: '16px',
          }}
        >
          <option value="">Seleccione un aprobador</option>
          {approvers.map((user) => (
            <option key={user.id} value={user.id}>
              {user.first_name || ''} {user.last_name || ''} ({user.username})
            </option>
          ))}
        </select>
      </div>

      {memo && memo.status === 'DRAFT' && (
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Subir Adjunto (PDF)
          </label>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              style={{ flex: 1 }}
            />
            <button
              type="button"
              onClick={handleFileUpload}
              disabled={!selectedFile || isUploading}
              style={{
                padding: '10px 20px',
                backgroundColor: selectedFile && !isUploading ? '#3498db' : '#95a5a6',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: selectedFile && !isUploading ? 'pointer' : 'not-allowed',
              }}
            >
              {isUploading ? 'Subiendo...' : 'Subir'}
            </button>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
        <button
          type="button"
          onClick={() => router.back()}
          style={{
            padding: '10px 20px',
            backgroundColor: '#95a5a6',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
          }}
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            padding: '10px 20px',
            backgroundColor: isSubmitting ? '#95a5a6' : '#27ae60',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: isSubmitting ? 'not-allowed' : 'pointer',
          }}
        >
          {isSubmitting ? 'Guardando...' : memo ? 'Actualizar Borrador' : 'Guardar Borrador'}
        </button>
      </div>
    </form>
  );
}
