"""
backend/services/sunat_ple_service.py
Generador oficial del Libro de Activos Fijos - Formato 7.1 (SUNAT PLE 7.1).
Estructura el archivo plano normativo (.txt) con separador pleca (|)
cumpliendo las especificaciones de la Resolución de Superintendencia SUNAT.
"""

import os
from datetime import date
from decimal import Decimal
from typing import Dict, Any, Tuple
from sqlalchemy import text

from backend.config.db_connection import get_engine


def generate_ple_7_1_content(anio: int) -> Tuple[str, str, int]:
    """
    Genera el contenido y nombre oficial del archivo PLE 7.1 para el año solicitado.
    Retorna: (filename, content_txt, total_registros)
    """
    engine = get_engine()
    ruc_empresa = os.getenv("EMPRESA_RUC", "20123456789").strip()

    filename = f"LE{ruc_empresa}{anio}0000070100001111.txt"

    with engine.connect() as conn:
        query = text(
            """
            SELECT 
                a.id_activo,
                a.codigo,
                COALESCE(a.catalogo_tipo_id, '9') AS catalogo_tipo_id,
                COALESCE(a.codigo_osce, a.codigo) AS codigo_bien,
                COALESCE(a.tipo_activo_ple, '04') AS tipo_activo_ple,
                c.codigo AS cuenta_contable,
                COALESCE(a.estado_activo_ple, '1') AS estado_activo_ple,
                a.descripcion,
                COALESCE(a.marca, '-') AS marca,
                COALESCE(a.modelo, '-') AS modelo,
                COALESCE(a.numero_serie, '-') AS numero_serie,
                COALESCE(a.metodo_depreciacion, '1') AS metodo_depreciacion,
                a.fecha_adquisicion,
                a.fecha_inicio_uso,
                cat.tasa_anual,
                a.costo_adquisicion,
                COALESCE(SUM(m.monto), 0) AS total_mejoras,
                -- Depreciación acumulada a fin de año
                COALESCE(dep_tot.depreciacion_acum, 0) AS dep_acum_total,
                -- Depreciación ocurrida dentro de este año específico
                COALESCE(dep_ej.dep_ejercicio, 0) AS dep_ejercicio,
                -- Valor neto
                COALESCE(dep_tot.valor_neto, a.costo_adquisicion) AS valor_neto,
                b.id_baja,
                b.motivo AS motivo_baja,
                b.fecha AS fecha_baja
            FROM activo_fijo a
            JOIN categoria_activo cat ON a.id_categoria = cat.id_categoria
            JOIN cuenta_contable c ON cat.id_cuenta_activo = c.id_cuenta
            LEFT JOIN mejora_activo m ON a.id_activo = m.id_activo AND EXTRACT(YEAR FROM m.fecha) <= :anio
            LEFT JOIN baja_activo b ON a.id_activo = b.id_activo
            -- Subquery depreciación acumulada a fin de año
            LEFT JOIN LATERAL (
                SELECT dep.depreciacion_acum, dep.valor_neto
                FROM depreciacion dep
                JOIN periodo_contable p ON dep.id_periodo = p.id_periodo
                WHERE dep.id_activo = a.id_activo AND p.anio <= :anio
                ORDER BY p.anio DESC, p.mes DESC
                LIMIT 1
            ) dep_tot ON true
            -- Subquery depreciación devengada sólo en este ejercicio
            LEFT JOIN LATERAL (
                SELECT SUM(dep.monto_periodo) AS dep_ejercicio
                FROM depreciacion dep
                JOIN periodo_contable p ON dep.id_periodo = p.id_periodo
                WHERE dep.id_activo = a.id_activo AND p.anio = :anio
            ) dep_ej ON true
            WHERE EXTRACT(YEAR FROM a.fecha_adquisicion) <= :anio
            GROUP BY a.id_activo, a.codigo, a.catalogo_tipo_id, a.codigo_osce, a.tipo_activo_ple,
                     c.codigo, a.estado_activo_ple, a.descripcion, a.marca, a.modelo,
                     a.numero_serie, a.metodo_depreciacion, a.fecha_adquisicion, a.fecha_inicio_uso,
                     cat.tasa_anual, a.costo_adquisicion, dep_tot.depreciacion_acum, dep_tot.valor_neto,
                     dep_ej.dep_ejercicio, b.id_baja, b.motivo, b.fecha
            ORDER BY a.codigo ASC;
            """
        )
        rows = conn.execute(query, {"anio": anio}).fetchall()

    lines = []
    correlativo = 1

    for row in rows:
        periodo_campo = f"{anio}0000"
        cuo = f"AS{row[0]:06d}"
        correlativo_asiento = f"M{correlativo:04d}"
        codigo_patrimonial = str(row[1])
        catalogo_tipo = str(row[2])
        codigo_bien = str(row[3])
        tipo_activo_ple = str(row[4])
        cuenta_contable = str(row[5])
        
        # Estado PLE
        estado_ple = "8" if row[20] is not None else ("9" if float(row[19]) == 0 else "1")

        descripcion = str(row[7]).replace("|", "/").strip()
        marca = str(row[8]).replace("|", "/").strip()
        modelo = str(row[9]).replace("|", "/").strip()
        num_serie = str(row[10]).replace("|", "/").strip()
        metodo_deprec = str(row[11])

        fecha_adq_str = row[12].strftime("%d/%m/%Y") if row[12] else ""
        fecha_uso_str = row[13].strftime("%d/%m/%Y") if row[13] else ""
        tasa_deprec = f"{float(row[14]):.2f}"

        costo_historico = float(row[15])
        mejoras = float(row[16])
        costo_total = costo_historico + mejoras
        dep_acum_total = float(row[17])
        dep_ejercicio = float(row[18])
        vnl = float(row[19])

        costo_str = f"{costo_total:.2f}"
        dep_acum_str = f"{dep_acum_total:.2f}"
        dep_ejercicio_str = f"{dep_ejercicio:.2f}"
        vnl_str = f"{vnl:.2f}"

        fields = [
            periodo_campo,              # 1. Periodo
            cuo,                        # 2. CUO
            correlativo_asiento,        # 3. Correlativo de asiento
            codigo_patrimonial,         # 4. Código propio
            catalogo_tipo,              # 5. Catálogo (Tabla 13: 3=OSCE, 9=Propio)
            codigo_bien,                # 6. Código catálogo
            tipo_activo_ple,            # 7. Tipo de activo (Tabla 18)
            cuenta_contable,            # 8. Código cuenta contable PCGE
            estado_ple,                 # 9. Estado del activo (Tabla 19)
            descripcion,                # 10. Descripción
            marca,                      # 11. Marca
            modelo,                     # 12. Modelo
            num_serie,                  # 13. Número de serie
            costo_str,                  # 14. Saldo inicial costo
            "0.00",                     # 15. Adquisiciones
            mejoras if mejoras else "0.00", # 16. Mejoras
            "0.00",                     # 17. Retiros o bajas
            "0.00",                     # 18. Otros ajustes
            "0.00",                     # 19. Ajuste por inflación costo
            costo_str,                  # 20. Costo histórico total
            "0.00",                     # 21. Ajuste revaluación voluntaria
            "0.00",                     # 22. Ajuste revaluación sin efecto
            fecha_adq_str,              # 23. Fecha de adquisición
            fecha_uso_str,              # 24. Fecha de inicio de uso
            metodo_deprec,              # 25. Método depreciación (Tabla 20)
            tasa_deprec,                # 26. Porcentaje depreciación
            dep_acum_str,               # 27. Depreciación acumulada histórica
            dep_ejercicio_str,          # 28. Depreciación del ejercicio
            "0.00",                     # 29. Depreciación de retiros
            "0.00",                     # 30. Depreciación de otros ajustes
            "0.00",                     # 31. Ajuste inflación depreciación
            dep_acum_str,               # 32. Depreciación acumulada total
            "0.00",                     # 33. Depreciación revaluación voluntaria
            "0.00",                     # 34. Depreciación revaluación sin efecto
            "1",                        # 35. Estado de la operación (1=Normal)
        ]

        line = "|".join(str(f) for f in fields) + "|"
        lines.append(line)
        correlativo += 1

    content_txt = "\r\n".join(lines) + ("\r\n" if lines else "")
    return filename, content_txt, len(lines)