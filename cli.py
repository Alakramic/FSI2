"""
cli.py
Interfaz de Consola de Comandos (CLI-First) para el SGAF.
Permite administrar la base de datos, diagnósticos, ingesta con IA,
cálculos de depreciación y reportes de bajas.
"""

from typing import Optional, List
from pathlib import Path
from datetime import date
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from sqlalchemy import text

from backend.config.db_connection import (
    get_active_profile,
    switch_profile,
    ping_db,
    get_engine,
)
from backend.database.migrator import run_migrations
from backend.database.seed import seed_database
from backend.services.ai_extractor import extract_from_invoice
from backend.services.ingestion_service import persist_ingested_invoice
from backend.services.depreciation_service import calculate_and_close_monthly_depreciation
from backend.services.bajas_service import preview_baja_financiera, register_baja_activo

app = typer.Typer(
    name="sgaf",
    help="Sistema de Gestión de Activos Fijos (SGAF) - Consola de Operaciones",
    add_completion=False,
)
db_app = typer.Typer(name="db", help="Comandos de gestión y diagnóstico de Base de Datos")
app.add_typer(db_app, name="db")

console = Console()


# ----------------------------------------------------------------------------
# COMANDOS DE BASE DE DATOS (FASE 1)
# ----------------------------------------------------------------------------

@db_app.command("ping")
def db_ping(
    perfil: Optional[str] = typer.Option(
        None, "--perfil", "-p", help="Perfil específico a diagnosticar (local, supabase, dev_team)"
    )
):
    """Verifica latencia, versión de PostgreSQL y perfil de conexión activo."""
    with console.status("[bold green]Verificando conexión con el motor de base de datos..."):
        diag = ping_db(perfil)

    table = Table(title="Diagnóstico de Conexión a Base de Datos - SGAF", show_header=True)
    table.add_column("Propiedad", style="cyan", no_wrap=True)
    table.add_column("Detalle", style="white")

    table.add_row("Estado", "[bold green]ONLINE[/bold green]" if diag["status"] == "ok" else "[bold red]ERROR[/bold red]")
    table.add_row("Perfil Solicitado", diag["profile"])
    table.add_row("URL de Conexión", diag["database_url"])
    table.add_row("Latencia", f"{diag['latency_ms']} ms")

    if diag["status"] == "ok":
        table.add_row("Versión PostgreSQL", diag["version"])
        console.print(table)
    else:
        table.add_row("Detalle Error", f"[red]{diag['error']}[/red]")
        console.print(table)
        raise typer.Exit(code=1)


@db_app.command("switch")
def db_switch(
    perfil: str = typer.Option(..., "--perfil", "-p", help="Nombre del nuevo perfil (local, supabase, dev_team)")
):
    """Cambia el perfil de conexión activo en .env y valida conectividad inmediata."""
    try:
        switch_profile(perfil)
        console.print(f"[bold green][OK] Perfil conmutado exitosamente a:[/bold green] [bold yellow]{perfil}[/bold yellow]")
        diag = ping_db(perfil)
        if diag["status"] == "ok":
            console.print(f"[green][OK] Conectividad verificada ({diag['latency_ms']} ms) con PostgreSQL.[/green]")
        else:
            console.print(f"[yellow][AVISO] Perfil cambiado pero la base de datos reportó un error de ping: {diag['error']}[/yellow]")
    except Exception as exc:
        console.print(f"[bold red][ERROR] Error al cambiar perfil:[/bold red] {exc}")
        raise typer.Exit(code=1)


@db_app.command("migrate")
def db_migrate():
    """Aplica el script DDL con las 17 tablas, restricciones CHECK e índices en PostgreSQL."""
    active_profile = get_active_profile()
    console.print(f"[cyan]Iniciando migración DDL en perfil activo:[/cyan] [bold]{active_profile}[/bold]")
    try:
        run_migrations()
        console.print("[bold green][OK] Migración DDL aplicada exitosamente para las 17 tablas relacionales.[/bold green]")
    except Exception as exc:
        console.print(f"[bold red][ERROR] Error aplicando migración DDL:[/bold red] {exc}")
        raise typer.Exit(code=1)


@db_app.command("seed")
def db_seed():
    """Puebla los catálogos base (estados, cuentas PCGE 33/39/68, categorías, centros de costo y ubicaciones)."""
    active_profile = get_active_profile()
    console.print(f"[cyan]Ejecutando semillero de datos en perfil:[/cyan] [bold]{active_profile}[/bold]")
    try:
        results = seed_database()
        console.print("[bold green][OK] Semillero ejecutado exitosamente:[/bold green]")
        for key, count in results.items():
            console.print(f"  - [yellow]{key}[/yellow]: {count} registros insertados")
    except Exception as exc:
        console.print(f"[bold red][ERROR] Error en semillero de datos:[/bold red] {exc}")
        raise typer.Exit(code=1)


# ----------------------------------------------------------------------------
# COMANDOS DE INGESTA INTELIGENTE CON IA (FASE 2)
# ----------------------------------------------------------------------------

@app.command("ingestar-factura")
def ingestar_factura(
    archivo: Path = typer.Option(..., "--archivo", "-a", help="Ruta al archivo PDF, imagen o JSON del comprobante"),
    responsable_id: Optional[int] = typer.Option(None, "--responsable-id", "-r", help="ID del custodio/empleado"),
    ubicacion_id: Optional[int] = typer.Option(None, "--ubicacion-id", "-u", help="ID de la ubicación física inicial"),
    auto_confirmar: bool = typer.Option(False, "--auto-confirmar", "-y", help="Confirmar automáticamente sin pausas interactivas"),
    mock: bool = typer.Option(False, "--mock", help="Procesar en modo simulado para pruebas locales"),
):
    """
    Ingesta automatizada de facturas mediante IA:
    - Extrae datos fiscales de proveedor y comprobante.
    - Discrimina semánticamente activos fijos vs consumibles.
    - Permite asignación interactiva de custodio y sede.
    - Persiste atómicamente en PostgreSQL generando códigos patrimoniales.
    """
    if not archivo.exists():
        console.print(f"[bold red][ERROR] El archivo no existe:[/bold red] {archivo}")
        raise typer.Exit(code=1)

    with console.status("[bold cyan]Analizando comprobante con IA y discriminando bienes duraderos..."):
        try:
            resultado = extract_from_invoice(archivo, mock_mode=mock)
        except Exception as exc:
            console.print(f"[bold red][ERROR] Error durante la extracción con IA:[/bold red] {exc}")
            raise typer.Exit(code=1)

    # 1. Mostrar resumen de Proveedor y Comprobante
    prov = resultado.proveedor
    doc = resultado.documento
    info_doc = (
        f"[bold]Proveedor:[/bold] {prov.razon_social} (RUC/DOC: {prov.ruc})\n"
        f"[bold]Comprobante:[/bold] {doc.tipo_documento} {doc.numero} | "
        f"[bold]Fecha:[/bold] {doc.fecha_emision} | [bold]Moneda:[/bold] {doc.moneda}\n"
        f"[bold]Monto Total Facturado:[/bold] {doc.moneda} {doc.monto_total:,.2f}"
    )
    console.print(Panel(info_doc, title="[bold green]Datos del Comprobante Extraído[/bold green]"))

    # 2. Mostrar tabla de Activos Fijos Identificados
    if resultado.activos:
        tab_activos = Table(title="Bienes Identificados como Activo Fijo (NIC 16 / SUNAT)", show_header=True)
        tab_activos.add_column("#", style="cyan", width=3)
        tab_activos.add_column("Descripción", style="white")
        tab_activos.add_column("Marca", style="yellow")
        tab_activos.add_column("Modelo", style="yellow")
        tab_activos.add_column("N° Serie", style="green")
        tab_activos.add_column("Cant.", justify="right")
        tab_activos.add_column("Costo Unit.", justify="right", style="green")
        tab_activos.add_column("Categoría Sugerida", style="magenta")

        for idx, act in enumerate(resultado.activos, start=1):
            tab_activos.add_row(
                str(idx),
                act.descripcion,
                act.marca or "-",
                act.modelo or "-",
                act.numero_serie or "-",
                str(act.cantidad),
                f"{doc.moneda} {act.costo_unitario:,.2f}",
                act.categoria_sugerida,
            )
        console.print(tab_activos)
    else:
        console.print("[bold yellow][AVISO] No se identificaron activos fijos tangibles en el comprobante.[/bold yellow]")

    # 3. Mostrar consumibles descartados
    if resultado.consumibles_descartados:
        console.print(
            f"[bold blue]ℹ Consumibles y Suministros descartados automáticamente ({len(resultado.consumibles_descartados)}):[/bold blue] "
            + ", ".join(f"[dim]{c}[/dim]" for c in resultado.consumibles_descartados)
        )

    if not resultado.activos:
        console.print("[yellow]Operación finalizada: no hay activos para registrar.[/yellow]")
        return

    # 4. Asignación Asistida o Interactiva de Custodio y Ubicación
    engine = get_engine()
    with engine.connect() as conn:
        if not responsable_id:
            empleados = conn.execute(
                text("SELECT id_empleado, dni, nombres || ' ' || apellidos AS nombre FROM empleado ORDER BY id_empleado;")
            ).fetchall()
            if not empleados:
                console.print("[bold red][ERROR] No hay empleados registrados en la base de datos para asignar custodia.[/bold red]")
                raise typer.Exit(code=1)
            if auto_confirmar:
                responsable_id = empleados[0][0]
            else:
                console.print("\n[bold cyan]Seleccione el Custodio/Responsable Inicial:[/bold cyan]")
                for emp in empleados:
                    console.print(f"  [{emp[0]}] {emp[2]} (DNI: {emp[1]})")
                responsable_id = int(Prompt.ask("Ingrese ID del Empleado", default=str(empleados[0][0])))

        if not ubicacion_id:
            ubicaciones = conn.execute(
                text("SELECT id_ubicacion, nombre, sede FROM ubicacion ORDER BY id_ubicacion;")
            ).fetchall()
            if not ubicaciones:
                console.print("[bold red][ERROR] No hay ubicaciones registradas en la base de datos.[/bold red]")
                raise typer.Exit(code=1)
            if auto_confirmar:
                ubicacion_id = ubicaciones[0][0]
            else:
                console.print("\n[bold cyan]Seleccione la Ubicación Física Inicial:[/bold cyan]")
                for ub in ubicaciones:
                    console.print(f"  [{ub[0]}] {ub[1]} - {ub[2]}")
                ubicacion_id = int(Prompt.ask("Ingrese ID de la Ubicación", default=str(ubicaciones[0][0])))

    # 5. Confirmación Humana
    if not auto_confirmar:
        confirmar = Confirm.ask("\n[bold yellow]¿Desea registrar e incorporar estos activos al patrimonio de la empresa?[/bold yellow]")
        if not confirmar:
            console.print("[bold red]Operación cancelada por el usuario.[/bold red]")
            return

    # 6. Persistencia Transaccional Atómica
    with console.status("[bold green]Guardando datos en PostgreSQL y generando códigos patrimoniales..."):
        try:
            guardado = persist_ingested_invoice(
                extraction=resultado,
                id_responsable=responsable_id,
                id_ubicacion=ubicacion_id,
            )
        except Exception as exc:
            console.print(f"[bold red][ERROR] Error en persistencia transaccional:[/bold red] {exc}")
            raise typer.Exit(code=1)

    # 7. Resumen de éxito
    tab_confirm = Table(title="[bold green][OK] Activos Fijos Registrados en Patrimonio[/bold green]", show_header=True)
    tab_confirm.add_column("Código Patrimonial", style="bold green")
    tab_confirm.add_column("Descripción", style="white")
    tab_confirm.add_column("N° Serie", style="yellow")
    tab_confirm.add_column("Costo", justify="right", style="green")
    tab_confirm.add_column("Vida Útil", justify="right", style="cyan")

    for act in guardado["activos"]:
        tab_confirm.add_row(
            act["codigo"],
            act["descripcion"],
            act.get("numero_serie") or "-",
            f"{doc.moneda} {act['costo']:,.2f}",
            f"{act['vida_util_meses']} meses",
        )

    console.print(tab_confirm)
    console.print(f"[bold green][OK] Total registrados:[/bold green] {guardado['total_activos_creados']} bienes patrimoniales.")


# ----------------------------------------------------------------------------
# COMANDOS DE MOTOR CONTABLE Y BAJAS (FASE 3)
# ----------------------------------------------------------------------------

depreciacion_app = typer.Typer(name="depreciacion", help="Motor contable de depreciación mensual")
app.add_typer(depreciacion_app, name="depreciacion")


@depreciacion_app.command("cerrar-mes")
def depreciacion_cerrar_mes(
    anio: int = typer.Option(..., "--anio", "-y", help="Año contable (ej: 2026)"),
    mes: int = typer.Option(..., "--mes", "-m", help="Mes contable (1 al 12)"),
    forzar: bool = typer.Option(False, "--forzar", "-f", help="Forzar recálculo si el periodo ya estaba cerrado"),
):
    """
    Ejecuta el devengo de depreciación mensual en línea recta:
    - Procesa todos los activos activos secuencial y atómicamente.
    - Respeta la regla de bien totalmente depreciado (cuota = 0, activo en uso).
    - Bloquea y cierra el periodo contable en PostgreSQL.
    """
    console.print(f"[cyan]Iniciando proceso de cierre de depreciación mensual para el periodo:[/cyan] [bold]{anio}-{mes:02d}[/bold]")
    try:
        resumen = calculate_and_close_monthly_depreciation(anio, mes, force_recalculate=forzar)
    except Exception as exc:
        console.print(f"[bold red][ERROR] Error en cierre de depreciación:[/bold red] {exc}")
        raise typer.Exit(code=1)

    tab = Table(title=f"[bold green]Cierre Contable Periodo {anio}-{mes:02d} (CERRADO)[/bold green]", show_header=True)
    tab.add_column("Código", style="cyan")
    tab.add_column("Descripción", style="white")
    tab.add_column("Cuota Mes", justify="right", style="green")
    tab.add_column("Deprec. Acum.", justify="right", style="yellow")
    tab.add_column("VNL (Neto)", justify="right", style="bold white")
    tab.add_column("Estado Deprec.", style="magenta")

    for d in resumen["detalles"]:
        estado_dep = "[dim]Totalmente Deprec.[/dim]" if d["totalmente_depreciado"] else "En Depreciación"
        tab.add_row(
            d["codigo"],
            d["descripcion"],
            f"S/ {d['cuota_mes']:,.2f}",
            f"S/ {d['depreciacion_acum']:,.2f}",
            f"S/ {d['valor_neto']:,.2f}",
            estado_dep,
        )

    console.print(tab)
    console.print(
        f"[bold green][OK] Periodo cerrado exitosamente:[/bold green] {resumen['activos_procesados']} activos procesados | "
        f"[bold]Total Gasto Depreciación del Mes:[/bold] S/ {resumen['total_depreciacion_mes']:,.2f}"
    )


activo_app = typer.Typer(name="activo", help="Gestión patrimonial y liquidación de bajas")
app.add_typer(activo_app, name="activo")


@activo_app.command("reportar-baja")
def activo_reportar_baja(
    id_activo: int = typer.Option(..., "--id", help="ID del activo fijo a dar de baja"),
    motivo: str = typer.Option(..., "--motivo", help="Motivo: OBSOLESCENCIA, ROBO, SINIESTRO, VENTA, DONACION"),
    precio_venta: Optional[float] = typer.Option(None, "--precio-venta", help="Importe de venta si el motivo es VENTA"),
    fecha_baja: Optional[str] = typer.Option(None, "--fecha", help="Fecha de baja YYYY-MM-DD (por defecto hoy)"),
    observacion: Optional[str] = typer.Option(None, "--observacion", help="Nota o sustento técnico"),
    auto_confirmar: bool = typer.Option(False, "--auto-confirmar", "-y", help="Confirmar sin solicitar interacción"),
):
    """
    Liquidación patrimonial y reporte de baja:
    - Calcula en tiempo real el VNL (Valor Neto en Libros) restante.
    - Informa el impacto financiero exacto (Pérdida o Ganancia contable).
    - Da de baja el bien y finaliza las custodias activas.
    """
    try:
        preview = preview_baja_financiera(id_activo, motivo, precio_venta)
    except Exception as exc:
        console.print(f"[bold red][ERROR] Error calculando impacto de baja:[/bold red] {exc}")
        raise typer.Exit(code=1)

    panel_text = (
        f"[bold]Activo:[/bold] {preview['codigo']} - {preview['descripcion']}\n"
        f"[bold]Costo Adquisición Total:[/bold] S/ {preview['costo_adquisicion']:,.2f}\n"
        f"[bold]Depreciación Acumulada:[/bold] S/ {preview['depreciacion_acumulada']:,.2f}\n"
        f"[bold]Valor Neto en Libros (VNL):[/bold] [bold yellow]S/ {preview['vnl']:,.2f}[/bold yellow]\n\n"
        f"[bold]Motivo de Baja:[/bold] {preview['motivo']}\n"
    )
    if preview["valor_venta"] is not None:
        panel_text += f"[bold]Precio de Venta:[/bold] S/ {preview['valor_venta']:,.2f}\n"
    panel_text += f"[bold red]{preview['mensaje']}[/bold red]"

    console.print(Panel(panel_text, title="[bold red]Impacto Financiero de Liquidación de Baja[/bold red]"))

    if not auto_confirmar:
        confirmar = Confirm.ask("[bold yellow]¿Confirma la baja definitiva de este bien patrimonial?[/bold yellow]")
        if not confirmar:
            console.print("[yellow]Baja cancelada por el usuario.[/yellow]")
            return

    parsed_date = date.fromisoformat(fecha_baja) if fecha_baja else None

    try:
        baja_res = register_baja_activo(
            id_activo=id_activo,
            motivo=motivo,
            fecha_baja=parsed_date,
            valor_venta=precio_venta,
            observacion=observacion,
        )
        console.print(
            f"[bold green][OK] Activo {baja_res['codigo']} dado de baja exitosamente.[/bold green]\n"
            f"Nuevo estado: [bold yellow]{baja_res['estado_final']}[/bold yellow] | "
            f"Custodia finalizada | Fecha: {baja_res['fecha_baja']}"
        )
    except Exception as exc:
        console.print(f"[bold red][ERROR] Error al registrar baja:[/bold red] {exc}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()