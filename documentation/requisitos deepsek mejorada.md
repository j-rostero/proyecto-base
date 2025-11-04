# **FLUJO OPTIMIZADO DE GESTIÓN DE MEMORANDOS**

## **1. AUTENTICACIÓN Y ROLES MEJORADOS**

### **1.1. Proceso de Login Optimizado**
```typescript
interface LoginFlow {
    usuario: string;      // Email corporativo
    contraseña: string;   // Encriptada bcrypt
    departamento: string; // Asignación automática
    rol: 'DIRECTOR' | 'USUARIO_SECUNDARIO';
}
```

### **1.2. Roles y Permisos Detallados**

#### **Director de Departamento**
```typescript
const permisosDirector = {
    aprobaciones: {
        aprobar: true,
        rechazar: true,
        solicitarModificaciones: true,
        delegarTemporalmente: true
    },
    consultas: {
        todosMemorandosDepartamento: true,
        reportes: true,
        metricas: true
    },
    configuracion: {
        secuencial: true,
        plantillas: true
    }
};
```

#### **Usuario Secundario**
```typescript
const permisosUsuario = {
    memorandos: {
        crear: true,
        editarPropios: true,
        borradores: true,
        adjuntarArchivos: true,
        responder: true
    },
    consultas: {
        memorandosPropios: true,
        memorandosRecibidos: true,
        historial: true
    }
};
```

## **2. SISTEMA CORRELATIVO MEJORADO POR DEPARTAMENTO**

### **2.1. Estructura Avanzada del Correlativo**
```
[COD_DEPTO]-[AÑO]-[MES]-[SECUENCIAL]
```
**Ejemplo:** `FIN-2024-03-0042`

### **2.2. Mecanismo de Generación Robusto**
```sql
-- Tabla mejorada de secuencias
CREATE TABLE secuencias_memorandos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    departamento_id UUID NOT NULL REFERENCES departamentos(id),
    año INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    ultima_secuencia INTEGER DEFAULT 0,
    prefijo VARCHAR(10) NOT NULL,
    creado_en TIMESTAMP DEFAULT NOW(),
    actualizado_en TIMESTAMP DEFAULT NOW(),
    UNIQUE(departamento_id, año, mes)
);
```

### **2.3. Algoritmo Mejorado con Bloqueo**
```javascript
class GeneradorCorrelativo {
    async generarNuevoCorrelativo(departamentoId) {
        const transaction = await prisma.$transaction(async (tx) => {
            const ahora = new Date();
            const año = ahora.getFullYear();
            const mes = ahora.getMonth() + 1;
            
            // Bloquea la fila para evitar duplicados
            const secuencia = await tx.secuencias_memorandos.upsert({
                where: {
                    departamento_id_año_mes: {
                        departamento_id: departamentoId,
                        año: año,
                        mes: mes
                    }
                },
                update: {
                    ultima_secuencia: { increment: 1 },
                    actualizado_en: ahora
                },
                create: {
                    departamento_id: departamentoId,
                    año: año,
                    mes: mes,
                    ultima_secuencia: 1,
                    prefijo: await this.obtenerPrefijo(departamentoId)
                }
            });
            
            return `${secuencia.prefijo}-${año}-${mes.toString().padStart(2, '0')}-${secuencia.ultima_secuencia.toString().padStart(4, '0')}`;
        });
        
        return transaction;
    }
}
```

## **3. FLUJO PRINCIPAL OPTIMIZADO**

### **3.1. Creación del Memorando (Flujo Completo)**

#### **Paso 1: Inicio del Memorando**
```typescript
interface NuevoMemorando {
    asunto: string;                    // Requerido, máximo 200 caracteres
    contenido: string;                 // Requerido, editor enriquecido
    destinatarios: Destinatario[];     // Mínimo 1, máximo 15
    prioridad: 'BAJA' | 'NORMAL' | 'ALTA' | 'URGENTE';
    archivosAdjuntos: Archivo[];       // Máximo 5 archivos, 10MB c/u
    confidencial: boolean;             // Restringe acceso
    requiereAcuseRecibo: boolean;      // Confirmación de lectura
}
```

#### **Paso 2: Validación Inteligente**
```javascript
class ValidadorMemorando {
    validarAntesDeGuardar(memorando) {
        const errores = [];
        
        if (!memorando.asunto?.trim()) {
            errores.push('El asunto es obligatorio');
        }
        
        if (memorando.contenido.length < 10) {
            errores.push('El contenido debe tener al menos 10 caracteres');
        }
        
        if (memorando.destinatarios.length === 0) {
            errores.push('Debe seleccionar al menos un destinatario');
        }
        
        if (memorando.archivosAdjuntos.length > 5) {
            errores.push('Máximo 5 archivos adjuntos permitidos');
        }
        
        return errores;
    }
}
```

#### **Paso 3: Guardado como Borrador**
```
Usuario completa formulario →
Sistema valida en tiempo real →
Genera correlativo provisional →
Guarda en estado "BORRADOR" →
Permite múltiples ediciones →
Mantiene historial de cambios
```

### **3.2. Flujo de Aprobación Mejorado**

#### **Transición a Aprobación**
```javascript
class TransicionAprobacion {
    async enviarParaAprobacion(memorandoId, usuarioId) {
        const memorando = await this.validarPuedeEnviar(memorandoId, usuarioId);
        
        return await prisma.$transaction(async (tx) => {
            // Actualizar estado
            const memoActualizado = await tx.memorandos.update({
                where: { id: memorandoId },
                data: {
                    estado: 'PENDIENTE_APROBACION',
                    fecha_envio_aprobacion: new Date(),
                    version_aprobacion: memorando.version
                }
            });
            
            // Crear registro de aprobación
            await tx.aprobaciones.create({
                data: {
                    memorandum_id: memorandoId,
                    aprobador_id: memorando.departamento.director_id,
                    orden: 1,
                    estado: 'PENDIENTE',
                    fecha_asignacion: new Date()
                }
            });
            
            // Notificar al director
            await this.notificarAprobacionPendiente(memoActualizado);
            
            return memoActualizado;
        });
    }
}
```

#### **Proceso de Decisión del Director**
```typescript
interface DecisionDirector {
    tipo: 'APROBAR' | 'RECHAZAR' | 'MODIFICAR';
    memorandumId: string;
    comentarios?: string;
    firmarDigitalmente: boolean;
    delegarA?: string; // Usuario ID para delegación
}
```

### **3.3. Firma Digital Avanzada**

#### **Implementación de Firma con Sello Tiempo**
```javascript
class ServicioFirmaDigital {
    async firmarMemorando(memorandoId, directorId) {
        const memorando = await this.obtenerMemorandoCompleto(memorandoId);
        const director = await this.obtenerDirector(directorId);
        
        const selloDigital = {
            version: '1.0',
            director: {
                id: director.id,
                nombre: director.nombre_completo,
                cargo: director.cargo,
                departamento: director.departamento.nombre
            },
            timestamp: new Date().toISOString(),
            hashDocumento: this.generarHashDocumento(memorando),
            codigoVerificacion: this.generarCodigoUnico(),
            metadatos: {
                ip: await this.obtenerIP(),
                userAgent: await this.obtenerUserAgent(),
                ubicacion: await this.obtenerUbicacionAproximada()
            }
        };
        
        // Guardar firma en base de datos
        await prisma.firmas_digitales.create({
            data: {
                id: uuidv4(),
                memorandum_id: memorandoId,
                sello_digital: selloDigital,
                firma_criptografica: await this.generarFirmaCriptografica(selloDigital),
                valido_desde: new Date(),
                valido_hasta: this.calcularExpiracion(1) // 1 año
            }
        });
        
        // Actualizar estado del memorando
        await prisma.memorandos.update({
            where: { id: memorandoId },
            data: {
                estado: 'APROBADO',
                fecha_aprobacion: new Date(),
                firmado_por: directorId
            }
        });
        
        return selloDigital;
    }
}
```

### **3.4. Distribución Inteligente**

#### **Proceso de Distribución Mejorado**
```javascript
class DistribuidorMemorandos {
    async distribuirMemorando(memorandoId) {
        const memorando = await this.obtenerMemorandoConDestinatarios(memorandoId);
        
        const resultados = [];
        
        for (const destinatario of memorando.destinatarios) {
            try {
                // Crear registro de distribución
                const distribucion = await prisma.distribuciones.create({
                    data: {
                        memorandum_id: memorandoId,
                        destinatario_id: destinatario.id,
                        tipo_destinatario: destinatario.tipo,
                        fecha_envio: new Date(),
                        metodo: 'SISTEMA',
                        estado: 'ENVIADO'
                    }
                });
                
                // Enviar notificación
                await this.enviarNotificacionCompleta(destinatario, memorando);
                
                // Registrar éxito
                resultados.push({
                    destinatario: destinatario.nombre,
                    estado: 'ENTREGADO',
                    distribucionId: distribucion.id
                });
                
            } catch (error) {
                // Registrar error y continuar con otros destinatarios
                resultados.push({
                    destinatario: destinatario.nombre,
                    estado: 'ERROR',
                    error: error.message
                });
            }
        }
        
        // Actualizar estado general del memorando
        await prisma.memorandos.update({
            where: { id: memorandoId },
            data: {
                estado: 'DISTRIBUIDO',
                fecha_distribucion: new Date(),
                metadatos_distribucion: { resultados }
            }
        });
        
        return resultados;
    }
}
```

## **4. SISTEMA DE RESPUESTAS (MEMORANDOS HIJOS) MEJORADO**

### **4.1. Creación de Respuesta con Contexto**
```javascript
class ServicioRespuestas {
    async crearRespuesta(memorandoPadreId, usuarioRespondedor) {
        const memorandoPadre = await this.obtenerMemorandoPadre(memorandoPadreId);
        
        // Validar que el usuario puede responder
        if (!this.puedeResponder(memorandoPadre, usuarioRespondedor)) {
            throw new Error('No tiene permisos para responder este memorando');
        }
        
        // Crear memorando hijo con contexto
        const memorandoHijo = await prisma.memorandos.create({
            data: {
                asunto: `RE: ${memorandoPadre.asunto}`,
                contenido: this.generarContenidoRespuesta(memorandoPadre),
                remitente_id: usuarioRespondedor.id,
                departamento_id: usuarioRespondedor.departamento_id,
                estado: 'BORRADOR',
                prioridad: memorandoPadre.prioridad,
                memorando_padre_id: memorandoPadreId,
                destinatarios: {
                    create: this.generarDestinatariosRespuesta(memorandoPadre, usuarioRespondedor)
                },
                metadatos: {
                    es_respuesta: true,
                    memorando_original: memorandoPadre.numero_correlativo,
                    respondido_por: usuarioRespondedor.nombre_completo
                }
            }
        });
        
        // Generar correlativo para la respuesta
        const correlativo = await generadorCorrelativo.generarNuevoCorrelativo(
            usuarioRespondedor.departamento_id
        );
        
        // Actualizar con correlativo real
        await prisma.memorandos.update({
            where: { id: memorandoHijo.id },
            data: { numero_correlativo: correlativo }
        });
        
        return memorandoHijo;
    }
    
    generarDestinatariosRespuesta(memorandoPadre, usuarioRespondedor) {
        const destinatarios = [];
        
        // El remitente original siempre recibe la respuesta
        destinatarios.push({
            usuario_id: memorandoPadre.remitente_id,
            tipo: 'PRINCIPAL'
        });
        
        // Opcional: incluir otros destinatarios del original
        if (memorandoPadre.incluir_todos_destinatarios) {
            for (const dest of memorandoPadre.destinatarios) {
                if (dest.usuario_id !== usuarioRespondedor.id) {
                    destinatarios.push({
                        usuario_id: dest.usuario_id,
                        tipo: 'COPIA'
                    });
                }
            }
        }
        
        return destinatarios;
    }
}
```

### **4.2. Visualización de Hilos Conversacionales**
```typescript
interface HiloConversacion {
    memorandoRaiz: Memorando;
    respuestas: Array<{
        memorando: Memorando;
        nivel: number;
        tieneRespuestas: boolean;
        ruta: string[]; // IDs del árbol
    }>;
    participantes: Usuario[];
    estadoGeneral: 'ACTIVO' | 'CERRADO' | 'PENDIENTE';
    ultimaActualizacion: Date;
}
```

## **5. NOTIFICACIONES INTELIGENTES MEJORADAS**

### **5.1. Sistema de Notificaciones en Tiempo Real**
```javascript
class ServicioNotificaciones {
    constructor() {
        this.canales = ['SISTEMA', 'EMAIL', 'PUSH'];
    }
    
    async notificarEventoMemorando(evento, memorando, usuarios) {
        const configs = await this.obtenerConfiguracionesNotificacion(usuarios);
        
        for (const usuario of usuarios) {
            const config = configs[usuario.id];
            
            for (const canal of this.canales) {
                if (config[canal] && config[evento.tipo]) {
                    await this.enviarPorCanal(canal, usuario, evento, memorando);
                }
            }
        }
    }
    
    async enviarPorCanal(canal, usuario, evento, memorando) {
        switch (canal) {
            case 'SISTEMA':
                await this.crearNotificacionSistema(usuario, evento, memorando);
                break;
                
            case 'EMAIL':
                await this.enviarEmailNotificacion(usuario, evento, memorando);
                break;
                
            case 'PUSH':
                await this.enviarNotificacionPush(usuario, evento, memorando);
                break;
        }
    }
}
```

### **5.2. Plantillas de Notificación Contextuales**
```typescript
const plantillasNotificacion = {
    APROBACION_PENDIENTE: {
        asunto: 'Tiene un memorando pendiente de aprobación',
        mensaje: 'El memorando {{numero}} de {{departamento}} está pendiente de su revisión',
        urgencia: 'ALTA',
        recordatorio: '24_HORAS'
    },
    MEMORANDO_APROBADO: {
        asunto: 'Su memorando ha sido aprobado',
        mensaje: 'El memorando {{numero}} ha sido aprobado y distribuido',
        urgencia: 'MEDIA',
        recordatorio: null
    },
    NUEVA_RESPUESTA: {
        asunto: 'Nueva respuesta a su memorando',
        mensaje: 'Tiene una nueva respuesta al memorando {{numero}}',
        urgencia: 'MEDIA',
        recordatorio: '12_HORAS'
    }
};
```

## **6. DIAGRAMA DE FLUJO COMPLETO MEJORADO**

```
[INICIO - LOGIN]
    ↓
[VALIDAR CREDENCIALES]
    ↓
[REDIRIGIR SEGÚN ROL]
    ↓           ↓
[DIRECTOR]  [USUARIO]
    ↓           ↓
[DASHBOARD] [DASHBOARD]
    ↓           ↓
               [CREAR MEMORANDO]
               ↓
          [COMPLETAR FORMULARIO]
               ↓
          [VALIDAR Y GENERAR CORRELATIVO]
               ↓
          [GUARDAR COMO BORRADOR] ←───┐
               ↓ (editar múltiple)    │
          [ENVIAR PARA APROBACIÓN]    │
               ↓                      │
          [NOTIFICAR AL DIRECTOR]     │
               ↓                      │
[DIRECTOR: APROBACIONES PENDIENTES]   │
               ↓                      │
          [REVISAR MEMORANDO]         │
               ↓                      │
          [¿DECISIÓN?]                │
               ↓                      │
    ┌─ [APROBAR] → [FIRMAR DIGITALMENTE] 
    │         ↓                      │
    │   [DISTRIBUIR AUTOMÁTICAMENTE] │
    │         ↓                      │
    │   [NOTIFICAR DESTINATARIOS]    │
    │         ↓                      │
    │   [REGISTRAR DISTRIBUCIÓN]     │
    │                                │
    ├─ [RECHAZAR] → [NOTIFICAR USUARIO] 
    │         ↓                      │
    │   [MOTIVO RECHAZO]             │
    │                                │
    └─ [SOLICITAR MODIFICACIONES]    │
               ↓                      │
          [NOTIFICAR USUARIO] ────────┘
               ↓
          [USUARIO: MODIFICAR BORRADOR]
               ↓
          [RE-ENVIAR PARA APROBACIÓN]
               ↓
[DESTINATARIOS: RECIBIR MEMORANDO]
               ↓
          [¿RESPONDER?] ── SÍ ─→ [CREAR MEMORANDO HIJO]
               │                       ↓
               NO             [SEGUIR FLUJO COMPLETO]
               ↓                       ↓
          [ACUSE DE RECIBO]    [NUEVO CICLO]
               ↓
          [ARCHIVAR]
               ↓
            [FIN]
```

## **7. REGLAS DE NEGOCIO MEJORADAS**

### **7.1. Validaciones Avanzadas**
```javascript
class ReglasNegocioMejoradas {
    static validacionesCompletas = {
        puedeCrearMemorando: (usuario) => {
            return usuario.rol === 'USUARIO_SECUNDARIO' && 
                   usuario.estado === 'ACTIVO' &&
                   usuario.departamento.estado === 'ACTIVO';
        },
        
        puedeAprobar: (director, memorando) => {
            return director.departamento_id === memorando.departamento_id &&
                   memorando.estado === 'PENDIENTE_APROBACION' &&
                   !this.tieneConflictoIntereses(director, memorando);
        },
        
        puedeResponder: (usuario, memorando) => {
            return memorando.estado === 'DISTRIBUIDO' &&
                   this.esDestinatario(usuario, memorando) &&
                   memorando.fecha_distribucion >= this.fechaLimiteRespuesta() &&
                   !this.respuestaExiste(usuario, memorando);
        },
        
        tieneConflictoIntereses: (director, memorando) => {
            return director.id === memorando.remitente_id ||
                   this.sonFamiliares(director, memorando.remitente);
        }
    };
}
```

### **7.2. Límites y Cuotas Mejorados**
```typescript
interface LimitesSistema {
    memorandos: {
        maxBorradoresSimultaneos: 50,
        maxDestinatarios: 15,
        maxArchivos: 5,
        maxTamanoArchivo: 10 * 1024 * 1024, // 10MB
        maxTamanoTotal: 25 * 1024 * 1024,   // 25MB
        tiempoMaximoBorrador: 30,           // días
        tiempoMaximoAprobacion: 72          // horas
    },
    respuestas: {
        maxProfundidadHilo: 10,
        maxRespuestasPorMemo: 20,
        tiempoMaximoRespuesta: 90           // días
    }
}
```

Este flujo mejorado garantiza:
- ✅ **Trazabilidad completa** con correlativos únicos por departamento
- ✅ **Control de acceso** basado en roles y departamentos
- ✅ **Proceso de aprobación** robusto con firma digital
- ✅ **Sistema de respuestas** que mantiene el contexto
- ✅ **Notificaciones inteligentes** multi-canal
- ✅ **Validaciones de negocio** para integridad de datos
- ✅ **Manejo de errores** y casos edge