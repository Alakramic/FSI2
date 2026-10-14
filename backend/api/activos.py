"""
backend/api/activos.py
Endpoints Operativos para la Gestión del Padrón y Ciclo de Vida de Activos Fijos:
- Traslados físicos entre sedes.
- Órdenes de mantenimiento (preventivo y correctivo).
- Hoja de vida y trazabilidad completa del bien.
- Reporte y liquidación de bajas patrimoniales.
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from backend.config.db_connection import get_engine
from backend.services.bajas_service import register_baja_activo, preview_baja_financiera
from backend.services.depreciation_service import get_asset_vnl

router = APIRouter(prefix="/activos", tags=["Activos Fijos"])


class TrasladoRequest(BaseModel):
    id_ubicacion_destino: int
    motivo: str = Field(..., min_length=3, max_length=200)
    id_autorizado_por: int
    fecha: Optional[date] = None


class MantenimientoRequest(BaseModel):
    tipo: str = Field(..., pattern="^(PREVENTIVO|CORRECTIVO)$")
    descripcion: str = Field(..., min_length=5, max_length=300)
    costo: Decimal = Field(default=Decimal("0.00"), ge=0)
    fecha: Optional[date] = None
    id_proveedor: Optional[int] = None


class BajaRequest(BaseModel):
    motivo: str = Field(..., pattern="^(OBSOLESCENCIA|ROBO|SINIESTRO|VENTA|DONACION)$")
    valor_venta: Optional[float] = None
    fecha: Optional[date] = None
    observacion: Optional[str] = None


@router.get("")
def list_activos(
    categoria_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    ubicacion_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None, description="Búsqueda en código o descripción"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Lista el padrón de activos fijos con filtros multicriterio."""
    engine = get_engine()
    with engine.connect() as conn:
        conditions = ["1=1"]
        params = {"limit": limit, "offset": offset}

        if categoria_id:
            conditions.append("a.id_categoria = :cat_id")
            params["cat_id"] = categoria_id
        if estado:
            conditions.append("est.nombre = :est_nom")
            params["est_nom"] = estado.upper()
        if ubicacion_id:
            conditions.append("a.id_ubicacion = :ub_id")
            params["ub_id"] = ubicacion_id
        if q:
            conditions.append("(a.codigo ILIKE :q OR a.descripcion ILIKE :q)")
            params["q"] = f"%{q}%"

        where_clause = " AND ".join(conditions)

        count_sql = text(
            f"""
            SELECT COUNT(*) 
            FROM activo_fijo a
            JOIN estado_activo est ON a.id_estado = est.id_estado
            WHERE {where_clause};
            """
        )
        total = conn.execute(count_sql, params).scalar()

        data_sql = text(
            f"""
            SELECT 
                a.id_activo,
                a.codigo,
                a.descripcion,
                a.marca,
                a.modelo,
                a.numero_serie,
                cat.nombre AS categoria,
                est.nombre AS estado,
                u.nombre || ' (' || u.sede || ')' AS ubicacion,
                emp.nombres || ' ' || emp.apellidos AS custodio,
                a.costo_adquisicion,
                a.fecha_inicio_uso,
                a.vida_util_meses
            FROM activo_fijo a
            JOIN categoria_activo cat ON a.id_categoria = cat.id_categoria
            JOIN estado_activo est ON a.id_estado = est.id_estado
            JOIN ubicacion u ON a.id_ubicacion = u.id_ubicacion
            JOIN empleado emp ON a.id_responsable = emp.id_empleado
            WHERE {where_clause}
            ORDER BY a.id_activo DESC
            LIMIT :limit OFFSET :offset;
            """
        )
        rows = conn.execute(data_sql, params).fetchall()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id_activo": r[0],
                "codigo": r[1],
                "descripcion": r[2],
                "marca": r[3],
                "modelo": r[4],
                "numero_serie": r[5],
                "categoria": r[6],
                "estado": r[7],
                "ubicacion": r[8],
                "custodio": r[9],
                "costo_adquisicion": float(r[10]),
                "fecha_inicio_uso": str(r[11]),
                "vida_util_meses": r[12],
            }
            for r in rows
        ],
    }


@router.get("/{id_activo}")
def get_activo_detalle(id_activo: int):
    """Retorna la Hoja de Vida completa del activo, incluyendo su historial de traslados, mantenimientos y VNL."""
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT 
                    a.id_activo, a.codigo, a.descripcion, a.marca, a.modelo, a.numero_serie,
                    cat.id_categoria, cat.nombre AS categoria,
                    est.nombre AS estado,
                    u.id_ubicacion, u.nombre AS ubicacion_nombre, u.sede,
                    emp.id_empleado, emp.nombres || ' ' || emp.apellidos AS custodio,
                    doc.tipo_documento, doc.numero AS numero_doc, doc.fecha_emision AS fecha_doc,
                    prov.razon_social AS proveedor,
                    a.costo_adquisicion, a.valor_residual, a.vida_util_meses,
                    a.fecha_adquisicion, a.fecha_inicio_uso
                FROM activo_fijo a
                JOIN categoria_activo cat ON a.id_categoria = cat.id_categoria
                JOIN estado_activo est ON a.id_estado = est.id_estado
                JOIN ubicacion u ON a.id_ubicacion = u.id_ubicacion
                JOIN empleado emp ON a.id_responsable = emp.id_empleado
                JOIN documento_adquisicion doc ON a.id_documento = doc.id_documento
                JOIN proveedor prov ON doc.id_proveedor = prov.id_proveedor
                WHERE a.id_activo = :id_act;
                """
            ),
            {"id_act": id_activo},
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"No existe el activo con ID: {id_activo}")

        # Trazabilidad: Traslados
        traslados = conn.execute(
            text(
                """
                SELECT t.fecha, u_orig.nombre AS origen, u_dest.nombre AS destino, t.motivo,
                       emp.nombres || ' ' || emp.apellidos AS autorizado_por
                FROM traslado_activo t
                JOIN ubicacion u_orig ON t.id_ubicacion_origen = u_orig.id_ubicacion
                JOIN ubicacion u_dest ON t.id_ubicacion_destino = u_dest.id_ubicacion
                JOIN empleado emp ON t.id_autorizado_por = emp.id_empleado
                WHERE t.id_activo = :id_act
                ORDER BY t.fecha DESC;
                """
            ),
            {"id_act": id_activo},
        ).fetchall()

        # Trazabilidad: Mantenimientos
        mantenimientos = conn.execute(
            text(
                """
                SELECT m.fecha, m.tipo, m.costo, m.descripcion, COALESCE(p.razon_social, 'Interno') AS proveedor
                FROM mantenimiento m
                LEFT JOIN proveedor p ON m.id_proveedor = p.id_proveedor
                WHERE m.id_activo = :id_act
                ORDER BY m.fecha DESC;
                """
            ),
            {"id_act": id_activo},
        ).fetchall()

    vnl_info = get_asset_vnl(id_activo)

    return {
        "id_activo": row[0],
        "codigo": row[1],
        "descripcion": row[2],
        "marca": row[3],
        "modelo": row[4],
        "numero_serie": row[5],
        "categoria": row[7],
        "estado": row[8],
        "ubicacion": f"{row[10]} - {row[11]}",
        "custodio": row[13],
        "documento_origen": f"{row[14]} {row[15]} ({row[16]}) - {row[17]}",
        "costo_adquisicion": float(row[18]),
        "valor_residual": float(row[19]),
        "vida_util_meses": row[20],
        "fecha_adquisicion": str(row[21]),
        "fecha_inicio_uso": str(row[22]),
        "situacion_financiera": {
            "depreciacion_acumulada": vnl_info["depreciacion_acum"],
            "valor_neto_en_libros": vnl_info["vnl"],
            "mejoras_capitalizadas": vnl_info["mejoras"],
        },
        "historial_traslados": [
            {
                "fecha": str(t[0]),
                "origen": t[1],
                "destino": t[2],
                "motivo": t[3],
                "autorizado_por": t[4],
            }
            for t in traslados
        ],
        "historial_mantenimientos": [
            {
                "fecha": str(m[0]),
                "tipo": m[1],
                "costo": float(m[2]),
                "descripcion": m[3],
                "proveedor": m[4],
            }
            for m in mantenimientos
        ],
    }


@router.post("/{id_activo}/traslados")
def registrar_traslado(id_activo: int, req: TrasladoRequest):
    """Registra el traslado físico del bien entre ubicaciones y actualiza su sede actual."""
    engine = get_engine()
    fecha_traslado = req.fecha or date.today()

    with engine.begin() as conn:
        # Obtener ubicación actual
        row_act = conn.execute(
            text("SELECT id_ubicacion, codigo FROM activo_fijo WHERE id_activo = :id_act;"),
            {"id_act": id_activo},
        ).fetchone()

        if not row_act:
            raise HTTPException(status_code=404, detail=f"No existe el activo con ID: {id_activo}")

        id_ubicacion_origen = row_act[0]
        codigo_activo = row_act[1]

        if id_ubicacion_origen == req.id_ubicacion_destino:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La ubicación de destino debe ser diferente a la ubicación de origen.",
            )

        # Validar destino
        dest_exists = conn.execute(
            text("SELECT 1 FROM ubicacion WHERE id_ubicacion = :id_ub;"),
            {"id_ub": req.id_ubicacion_destino},
        ).scalar()
        if not dest_exists:
            raise HTTPException(status_code=400, detail="Ubicación de destino no existe.")

        # Insertar traslado
        id_traslado = conn.execute(
            text(
                """
                INSERT INTO traslado_activo (
                    id_activo, id_ubicacion_origen, id_ubicacion_destino, fecha, motivo, id_autorizado_por
                ) VALUES (
                    :id_act, :orig, :dest, :fecha, :motivo, :aut
                ) RETURNING id_traslado;
                """
            ),
            {
                "id_act": id_activo,
                "orig": id_ubicacion_origen,
                "dest": req.id_ubicacion_destino,
                "fecha": fecha_traslado,
                "motivo": req.motivo,
                "aut": req.id_autorizado_por,
            },
        ).scalar()

        # Actualizar ubicación del activo
        conn.execute(
            text("UPDATE activo_fijo SET id_ubicacion = :dest WHERE id_activo = :id_act;"),
            {"dest": req.id_ubicacion_destino, "id_act": id_activo},
        )

    return {
        "status": "ok",
        "mensaje": "Traslado registrado exitosamente.",
        "id_traslado": id_traslado,
        "id_activo": id_activo,
        "codigo_activo": codigo_activo,
        "id_ubicacion_nueva": req.id_ubicacion_destino,
    }


@router.post("/{id_activo}/mantenimientos")
def registrar_mantenimiento(id_activo: int, req: MantenimientoRequest):
    """Registra una orden de mantenimiento preventivo o correctivo."""
    engine = get_engine()
    fecha_mant = req.fecha or date.today()

    with engine.begin() as conn:
        row_act = conn.execute(
            text("SELECT codigo FROM activo_fijo WHERE id_activo = :id_act;"),
            {"id_act": id_activo},
        ).fetchone()

        if not row_act:
            raise HTTPException(status_code=404, detail=f"No existe el activo con ID: {id_activo}")

        id_mant = conn.execute(
            text(
                """
                INSERT INTO mantenimiento (
                    id_activo, id_proveedor, tipo, fecha, costo, descripcion
                ) VALUES (
                    :id_act, :id_prov, :tipo, :fecha, :costo, :desc
                ) RETURNING id_mantenimiento;
                """
            ),
            {
                "id_act": id_activo,
                "id_prov": req.id_proveedor,
                "tipo": req.tipo,
                "fecha": fecha_mant,
                "costo": req.costo,
                "desc": req.descripcion,
            },
        ).scalar()

    return {
        "status": "ok",
        "mensaje": f"Mantenimiento {req.tipo} registrado exitosamente.",
        "id_mantenimiento": id_mant,
        "id_activo": id_activo,
        "codigo_activo": row_act[0],
    }


@router.post("/{id_activo}/baja")
def registrar_baja(id_activo: int, req: BajaRequest):
    """Reporta y ejecuta la baja contable y patrimonial del bien."""
    try:
        resultado = register_baja_activo(
            id_activo=id_activo,
            motivo=req.motivo,
            fecha_baja=req.fecha,
            valor_venta=req.valor_venta,
            observacion=req.observacion,
        )
        return resultado
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

@router.get("/{id_activo}/baja/preview")
def preview_baja(
    id_activo: int,
    motivo: str = Query(..., pattern="^(OBSOLESCENCIA|ROBO|SINIESTRO|VENTA|DONACION)$"),
    valor_venta: Optional[float] = Query(None),
):
    """Calcula el impacto contable previo a la confirmaci?n de la baja."""
    try:
        resultado = preview_baja_financiera(
            id_activo=id_activo,
            motivo=motivo,
            valor_venta=valor_venta,
        )
        return resultado
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
