'use client';

import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';
import { useMemoDetail, useMemos } from '@/lib/hooks';
import { useAuthStore } from '@/lib/store';
import { memosService } from '@/lib/memos';
import LayoutProtected from '@/components/LayoutProtected';

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
import Link from 'next/link';

export default function MemoDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = parseInt(params.id as string);
  const { memo, isLoading, mutate } = useMemoDetail(id);
  const { user } = useAuthStore();
  const [isProcessing, setIsProcessing] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');

  const handleSubmit = async () => {
    if (!memo) return;
    
    // Validaciones previas en el frontend
    if (!memo.approver) {
      toast.error('Debe asignar un aprobador antes de enviar el memo');
      return;
    }
    
    if (!memo.recipients || memo.recipients.length === 0) {
      toast.error('Debe asignar al menos un destinatario antes de enviar el memo');
      return;
    }
    
    setIsProcessing(true);
    try {
      await memosService.submitMemo(memo.id);
      toast.success('Memo enviado a aprobación exitosamente');
      mutate();
      router.push('/dashboard/drafts');
    } catch (error: any) {
      // Extraer el mensaje del error de la respuesta
      let errorMessage = 'Error al enviar el memo';
      if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      toast.error(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApprove = async () => {
    if (!memo) return;
    setIsProcessing(true);
    try {
      await memosService.approveMemo(memo.id);
      toast.success('Memo aprobado y distribuido');
      mutate();
      router.push('/dashboard/inbox');
    } catch (error: any) {
      toast.error(error.message || 'Error al aprobar el memo');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!memo) return;
    setIsProcessing(true);
    try {
      await memosService.rejectMemo(memo.id, rejectionReason);
      toast.success('Memo rechazado');
      setShowRejectModal(false);
      setRejectionReason('');
      mutate();
      router.push('/dashboard/inbox');
    } catch (error: any) {
      toast.error(error.message || 'Error al rechazar el memo');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReply = async () => {
    if (!memo) return;
    router.push(`/memos/new?parent_id=${memo.id}`);
  };

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

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      'DRAFT': 'Borrador',
      'PENDING_APPROVAL': 'Pendiente de Aprobación',
      'APPROVED': 'Aprobado',
      'REJECTED': 'Rechazado',
    };
    return labels[status] || status;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'DRAFT': '#3498db',
      'PENDING_APPROVAL': '#f39c12',
      'APPROVED': '#27ae60',
      'REJECTED': '#e74c3c',
    };
    return colors[status] || '#95a5a6';
  };

  const canEdit = user?.role === 'SECONDARY_USER' && memo.status === 'DRAFT' && memo.author.id === user.id;
  const canSubmit = user?.role === 'SECONDARY_USER' && memo.status === 'DRAFT' && memo.author.id === user.id;
  const canApprove = user?.role === 'DIRECTOR' && memo.status === 'PENDING_APPROVAL' && memo.approver?.id === user.id;
  const canReject = user?.role === 'DIRECTOR' && memo.status === 'PENDING_APPROVAL' && memo.approver?.id === user.id;
  const canReply = memo.status === 'APPROVED';

  return (
    <LayoutProtected>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h1 style={{ margin: 0, fontSize: '28px', fontWeight: 'bold' }}>Detalle del Memorándum</h1>
          <span
            style={{
              padding: '8px 16px',
              borderRadius: '20px',
              fontSize: '14px',
              fontWeight: 'bold',
              backgroundColor: getStatusColor(memo.status),
              color: 'white',
            }}
          >
            {getStatusLabel(memo.status)}
          </span>
        </div>

        <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', marginBottom: '20px' }}>
          <h2 style={{ marginTop: 0, marginBottom: '20px', fontSize: '24px', color: '#2c3e50' }}>
            {memo.subject}
          </h2>

          <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '15px', fontSize: '14px' }}>
              <div>
                <strong>Autor:</strong> {memo.author.first_name || memo.author.username}
              </div>
              <div>
                <strong>Fecha de creación:</strong> {new Date(memo.created_at).toLocaleString('es-ES')}
              </div>
              {memo.approver && (
                <div>
                  <strong>Aprobador:</strong> {memo.approver.first_name || memo.approver.username}
                </div>
              )}
              {memo.approved_at && (
                <div>
                  <strong>Fecha de aprobación:</strong> {new Date(memo.approved_at).toLocaleString('es-ES')}
                </div>
              )}
            </div>
            {memo.recipients.length > 0 && (
              <div style={{ marginTop: '10px' }}>
                <strong>Destinatarios:</strong>{' '}
                {memo.recipients.map(r => r.first_name || r.username).join(', ')}
              </div>
            )}
          </div>

          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ marginBottom: '10px', fontSize: '18px' }}>Contenido:</h3>
            <div
              dangerouslySetInnerHTML={{ __html: memo.body }}
              style={{
                padding: '15px',
                backgroundColor: '#f8f9fa',
                borderRadius: '5px',
                lineHeight: '1.6',
              }}
            />
          </div>

          {memo.rejection_reason && (
            <div style={{
              marginBottom: '20px',
              padding: '15px',
              backgroundColor: '#fee',
              borderRadius: '5px',
              borderLeft: '4px solid #e74c3c',
            }}>
              <strong>Motivo de rechazo:</strong> {memo.rejection_reason}
            </div>
          )}

          {memo.attachments && memo.attachments.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ marginBottom: '10px', fontSize: '18px' }}>Adjuntos:</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {memo.attachments.map((attachment) => (
                  <a
                    key={attachment.id}
                    href={attachment.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      padding: '10px',
                      backgroundColor: '#e8f4f8',
                      borderRadius: '5px',
                      textDecoration: 'none',
                      color: '#3498db',
                    }}
                  >
                    📎 {attachment.file}
                  </a>
                ))}
              </div>
            </div>
          )}

          {memo.signed_file_url && (
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ marginBottom: '10px', fontSize: '18px' }}>PDF Firmado:</h3>
              <a
                href={memo.signed_file_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'inline-block',
                  padding: '10px 20px',
                  backgroundColor: '#27ae60',
                  color: 'white',
                  textDecoration: 'none',
                  borderRadius: '5px',
                  fontWeight: 'bold',
                }}
              >
                📄 Ver PDF Firmado
              </a>
            </div>
          )}

          {memo.parent_memo && (
            <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#e8f4f8', borderRadius: '5px' }}>
              <strong>Memo padre:</strong>{' '}
              <Link href={`/memos/${memo.parent_memo.id}`} style={{ color: '#3498db' }}>
                {memo.parent_memo.subject}
              </Link>
            </div>
          )}

          {memo.replies && memo.replies.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ marginBottom: '10px', fontSize: '18px' }}>Respuestas:</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {memo.replies.map((reply) => (
                  <Link
                    key={reply.id}
                    href={`/memos/${reply.id}`}
                    style={{
                      padding: '10px',
                      backgroundColor: '#f8f9fa',
                      borderRadius: '5px',
                      textDecoration: 'none',
                      color: '#2c3e50',
                    }}
                  >
                    {reply.subject} - {getStatusLabel(reply.status)}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          {canEdit && (
            <Link
              href={`/memos/edit/${memo.id}`}
              style={{
                padding: '10px 20px',
                backgroundColor: '#3498db',
                color: 'white',
                textDecoration: 'none',
                borderRadius: '5px',
                fontWeight: 'bold',
              }}
            >
              Editar
            </Link>
          )}
          {canSubmit && (
            <button
              onClick={handleSubmit}
              disabled={isProcessing}
              style={{
                padding: '10px 20px',
                backgroundColor: isProcessing ? '#95a5a6' : '#f39c12',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                fontWeight: 'bold',
              }}
            >
              {isProcessing ? 'Enviando...' : 'Enviar a Aprobación'}
            </button>
          )}
          {canApprove && (
            <button
              onClick={handleApprove}
              disabled={isProcessing}
              style={{
                padding: '10px 20px',
                backgroundColor: isProcessing ? '#95a5a6' : '#27ae60',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                fontWeight: 'bold',
              }}
            >
              {isProcessing ? 'Aprobando...' : 'Aprobar'}
            </button>
          )}
          {canReject && (
            <>
              <button
                onClick={() => setShowRejectModal(true)}
                disabled={isProcessing}
                style={{
                  padding: '10px 20px',
                  backgroundColor: isProcessing ? '#95a5a6' : '#e74c3c',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: isProcessing ? 'not-allowed' : 'pointer',
                  fontWeight: 'bold',
                }}
              >
                Rechazar
              </button>
              {showRejectModal && (
                <div style={{
                  position: 'fixed',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  backgroundColor: 'rgba(0,0,0,0.5)',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  zIndex: 1000,
                }}>
                  <div style={{
                    backgroundColor: 'white',
                    padding: '30px',
                    borderRadius: '8px',
                    maxWidth: '500px',
                    width: '90%',
                  }}>
                    <h3 style={{ marginTop: 0 }}>Motivo de Rechazo</h3>
                    <textarea
                      value={rejectionReason}
                      onChange={(e) => setRejectionReason(e.target.value)}
                      placeholder="Ingrese el motivo del rechazo..."
                      style={{
                        width: '100%',
                        minHeight: '100px',
                        padding: '10px',
                        marginBottom: '20px',
                        border: '1px solid #ddd',
                        borderRadius: '5px',
                      }}
                    />
                    <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                      <button
                        onClick={() => {
                          setShowRejectModal(false);
                          setRejectionReason('');
                        }}
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
                        onClick={handleReject}
                        disabled={isProcessing}
                        style={{
                          padding: '10px 20px',
                          backgroundColor: '#e74c3c',
                          color: 'white',
                          border: 'none',
                          borderRadius: '5px',
                          cursor: isProcessing ? 'not-allowed' : 'pointer',
                        }}
                      >
                        {isProcessing ? 'Rechazando...' : 'Rechazar'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          {canReply && (
            <button
              onClick={handleReply}
              style={{
                padding: '10px 20px',
                backgroundColor: '#9b59b6',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer',
                fontWeight: 'bold',
              }}
            >
              Responder
            </button>
          )}
        </div>
      </div>
    </LayoutProtected>
  );
}

