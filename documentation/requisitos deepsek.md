# **FLUJO DETALLADO DEL PROCESO DE MEMORANDOS**

## **1. AUTENTICACIÓN Y ROLES DEL SISTEMA**

### **1.1. Proceso de Login**
```
Usuario ingresa credenciales →
Sistema valida en base de datos →
Asigna token de sesión JWT →
Redirige según rol →
Registra log de acceso
```

### **1.2. Roles y Permisos**

#### **Director de Departamento**
- Aprobar/rechazar memorandos del departamento
- Firmar digitalmente memorandos
- Delegar aprobaciones (opcional)
- Consultar todos los memorandos del departamento
- Generar reportes del área

#### **Usuario Secundario (Colaborador)**
- Crear memorandos en estado "Borrador"
- Editar sus propios borradores
- Enviar memorandos para aprobación
- Cargar archivos adjuntos
- Consultar memorandos propios
- Responder memorandos (crear memorandos hijos)

#### **Administrador del Sistema**
- Gestionar usuarios y departamentos
- Configurar secuencias correlativas
- Monitorear flujos y estadísticas
- Resolver incidencias del sistema

## **2. GENERACIÓN DE CORRELATIVO ÚNICO POR DEPARTAMENTO**

### **2.1. Estructura del Número de Memorando**
```
[Prefijo Departamento]-[Año]-[Secuencial]
```
**Ejemplo:** `FIN-2024-0015`

### **2.2. Mecanismo de Generación**
```sql
-- Tabla de control de secuencias
CREATE TABLE secuencias_memorandos (
    departamento_id UUID REFERENCES departamentos(id),
    año INTEGER NOT NULL,
    ultima_secuencia INTEGER DEFAULT 0,
    PRIMARY KEY (departamento_id, año)
);
```

### **2.3. Algoritmo de Asignación**
```javascript
async function generarCorrelativo(departamentoId, año) {
    // Buscar o crear secuencia para el departamento/año
    const secuencia = await Secuencia.findOneAndUpdate(
        { departamento_id: departamentoId, año: año },
        { $inc: { ultima_secuencia: 1 } },
        { upsert: true, new: true }
    );
    
    const prefijo = await obtenerPrefijoDepartamento(departamentoId);
    return `${prefijo}-${año}-${secuencia.ultima_secuencia.toString().padStart(4, '0')}`;
}
```

## **3. FLUJO DETALLADO DEL MEMORANDO**

### **3.1. Creación del Memorando (Usuario Secundario)**

#### **Paso 1: Formulario de Creación**
```typescript
interface MemorandoForm {
    asunto: string;
    contenido: string;
    destinatarios: Usuario[];  // Usuarios o departamentos
    prioridad: 'baja' | 'normal' | 'alta' | 'urgente';
    archivos_adjuntos: File[];
    confidencial: boolean;
}
```

#### **Paso 2: Validación y Guardado**
```
Usuario completa formulario →
Sistema valida campos obligatorios →
Genera número correlativo automáticamente →
Guarda en estado "BORRADOR" →
Asigna fecha de creación →
Permite carga de archivos PDF (máx. 10MB cada uno)
```

#### **Paso 3: Carga de Archivos Adjuntos**
- Formatos permitidos: PDF, DOC, DOCX, XLS, XLSX
- Tamaño máximo: 10MB por archivo
- Límite: 5 archivos por memorando
- Se almacenan en Amazon S3 con encriptación

### **3.2. Envío para Aprobación**

#### **Flujo de Transición**
```
Estado: BORRADOR → PENDIENTE_APROBACION
```
**Acciones:**
1. Usuario hace clic en "Enviar para Aprobación"
2. Sistema valida que tenga:
   - Asunto completo
   - Contenido mínimo
   - Destinatarios seleccionados
3. Se asigna automáticamente al Director del departamento
4. Se genera notificación al Director

### **3.3. Proceso de Aprobación (Director)**

#### **Opciones del Director:**
```typescript
interface AccionesAprobacion {
    aprobar: () => void;
    rechazar: (motivo: string) => void;
    solicitarModificaciones: (comentarios: string) => void;
    delegar: (usuarioId: string) => void;  // Opcional
}
```

#### **Flujo de Aprobación:**
```
Director recibe notificación →
Revisa contenido y adjuntos →
Toma decisión (Aprobar/Rechazar/Modificar) →
Si APRUEBA: procede a firma digital
Si RECHAZA: notifica con motivo al usuario
Si SOLICITA MODIFICACIONES: retorna a borrador con comentarios
```

### **3.4. Firma Digital y Sello**

#### **Implementación de Firma Digital:**
```javascript
class FirmaDigital {
    async firmarMemorando(memorandoId, directorId) {
        const memorando = await Memorando.findById(memorandoId);
        const director = await Usuario.findById(directorId);
        
        const selloDigital = {
            director: director.nombre_completo,
            cargo: director.cargo,
            departamento: director.departamento.nombre,
            fechaFirma: new Date(),
            hash: this.generarHash(memorando),
            codigoVerificacion: this.generarCodigoVerificacion()
        };
        
        await Memorando.updateOne(
            { _id: memorandoId },
            { 
                estado: 'APROBADO',
                sello_digital: selloDigital,
                fecha_aprobacion: new Date()
            }
        );
        
        return selloDigital;
    }
    
    generarHash(memorando) {
        return crypto
            .createHash('sha256')
            .update(JSON.stringify(memorando))
            .digest('hex');
    }
}
```

#### **Sello Visual en PDF:**
```
"Certificado digitalmente por: [Nombre Director]
Cargo: [Cargo Director] 
Departamento: [Nombre Departamento]
Fecha: [Fecha Aprobación]
Código de Verificación: [Código Único]"
```

### **3.5. Distribución a Áreas Involucradas**

#### **Proceso de Distribución:**
```
Memorando aprobado y firmado →
Sistema identifica destinatarios →
Envía notificaciones por correo y sistema →
Registra fecha de distribución →
Cambia estado a "DISTRIBUIDO"
```

#### **Notificación a Destinatarios:**
```javascript
class NotificacionService {
    async notificarDestinatarios(memorandoId) {
        const memorando = await Memorando.findById(memorandoId)
            .populate('destinatarios');
        
        for (const destinatario of memorando.destinatarios) {
            await this.enviarEmail({
                to: destinatario.email,
                subject: `Nuevo Memorando: ${memorando.asunto}`,
                template: 'nuevo_memorando',
                data: {
                    numero: memorando.numero_correlativo,
                    asunto: memorando.asunto,
                    remitente: memorando.remitente.nombre,
                    departamento: memorando.departamento.nombre,
                    enlace: `${process.env.APP_URL}/memorandos/${memorando.id}`
                }
            });
            
            await this.crearNotificacionSistema(
                destinatario.id,
                'Tienes un nuevo memorando',
                'memorando',
                memorando.id
            );
        }
    }
}
```

### **3.6. Seguimiento de Estados**

#### **Diagrama de Estados:**
```
BORRADOR → PENDIENTE_APROBACION → APROBADO → DISTRIBUIDO
    ↑              ↓
    ←── RECHAZADO ──
    ←── MODIFICACION_SOLICITADA ──
```

#### **Tabla de Estados:**
| Estado | Descripción | Quién Puede Cambiarlo |
|--------|-------------|----------------------|
| BORRADOR | En edición por usuario | Usuario secundario |
| PENDIENTE_APROBACION | Esperando aprobación del director | Sistema (al enviar) |
| APROBADO | Aprobado por director | Director |
| RECHAZADO | Rechazado por director | Director |
| MODIFICACION_SOLICITADA | Requiere cambios | Director |
| DISTRIBUIDO | Enviado a destinatarios | Sistema (automático) |

## **4. PROCESO DE RESPUESTA (MEMORANDO HIJO)**

### **4.1. Creación de Memorando como Respuesta**

#### **Inicio de Respuesta:**
```
Destinatario selecciona "Responder" →
Sistema crea nuevo memorando con:
- Asunto: "RE: [Asunto original]"
- Memorando padre: ID del memorando original
- Destinatario: Remitente original + otros opcionales
- Contenido pre-cargado con referencia al original
```

#### **Estructura de Relación:**
```sql
CREATE TABLE relacion_memorandos (
    memorando_padre_id UUID REFERENCES memorandos(id),
    memorando_hijo_id UUID REFERENCES memorandos(id),
    tipo_relacion ENUM('respuesta', 'seguimiento', 'referencia'),
    PRIMARY KEY (memorando_padre_id, memorando_hijo_id)
);
```

### **4.2. Flujo de la Respuesta**

```
Usuario responde memorando →
Sistema crea nuevo memorando hijo →
Sigue el mismo flujo completo:
  1. Borrador (usuario secundario)
  2. Envío a aprobación (director)
  3. Aprobación y firma (director)
  4. Distribución (sistema)
```

### **4.3. Visualización de Hilos**
```typescript
interface HiloMemorando {
    memorando_principal: Memorando;
    respuestas: Memorando[];
    profundidad: number;
    tiene_respuestas_pendientes: boolean;
}
```

## **5. NOTIFICACIONES DEL SISTEMA**

### **5.1. Tipos de Notificación**

#### **Notificaciones por Email:**
- Nuevo memorando para aprobar (Director)
- Memorando aprobado/rechazado (Usuario)
- Nuevo memorando recibido (Destinatarios)
- Recordatorio de aprobación pendiente (Director)

#### **Notificaciones en Sistema:**
- Badge en icono de memorandos
- Lista de notificaciones en panel principal
- Recordatorios automáticos

### **5.2. Configuración de Notificaciones**
```javascript
const configuracionNotificaciones = {
    aprobacion_pendiente: {
        email: true,
        sistema: true,
        recordatorio: '24h'
    },
    memorando_aprobado: {
        email: true,
        sistema: true
    },
    nuevo_memorando: {
        email: true,
        sistema: true
    }
};
```

## **6. REGLAS DE NEGOCIO ESPECÍFICAS**

### **6.1. Validaciones de Negocio**

```javascript
class ReglasNegocioMemorandos {
    static puedeEditar(usuario, memorando) {
        return memorando.estado === 'BORRADOR' && 
               memorando.remitente_id === usuario.id;
    }
    
    static puedeAprobar(usuario, memorando) {
        return usuario.rol === 'DIRECTOR' && 
               usuario.departamento_id === memorando.departamento_id &&
               memorando.estado === 'PENDIENTE_APROBACION';
    }
    
    static puedeResponder(usuario, memorando) {
        return memorando.estado === 'DISTRIBUIDO' &&
               memorando.destinatarios.includes(usuario.id);
    }
}
```

### **6.2. Límites y Restricciones**
- Máximo 10 destinatarios por memorando
- Tiempo máximo en borrador: 30 días (luego se archiva)
- Tiempo para aprobación: 72 horas (luego recordatorio)
- Historial de cambios se mantiene por 5 años

## **7. DIAGRAMA DE FLUJO COMPLETO**

```
[INICIO]
    ↓
Usuario Secundario Login
    ↓
Crear Nuevo Memorando
    ↓
Completar Formulario + Adjuntos
    ↓
Guardar como BORRADOR ←───┐
    ↓ (editar)            │
Enviar para Aprobación    │
    ↓                     │
Estado: PENDIENTE_APROBACION │
    ↓                     │
Notificar al Director     │
    ↓                     │
Director Revisa           │
    ↓                     │
¿Aprobar? ──SÍ──→ Firmar Digitalmente
    │ NO                  │
    ↓                     │
¿Rechazar? ─SÍ─→ Notificar Rechazo
    │ NO                  │
    ↓                     │
Solicitar Modificaciones  │
    ↓                     │
Notificar Usuario ────────┘
    ↓
Estado: APROBADO
    ↓
Distribuir a Destinatarios
    ↓
Notificar Recepción
    ↓
Estado: DISTRIBUIDO
    ↓
¿Respuesta? ─SÍ─→ Crear Memorando Hijo
    │ NO
    ↓
[FIN]
```

Este flujo garantiza un control completo del proceso de memorandos, con trazabilidad, seguridad y eficiencia en cada etapa del ciclo de vida del documento.