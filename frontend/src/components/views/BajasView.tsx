"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchActivos, previewBaja, registrarBaja } from "@/lib/api";
import {
  Trash2,
  DollarSign,
  AlertTriangle,
  FileText,
  Calculator,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  CheckCircle2,
  HelpCircle,
  Calendar,
  Layers,
  Search,
  RefreshCw,
} from "lucide-react";

interface BajasViewProps {
  initialActivoId?: number | null;
}

const MOTIVOS = [
  { id: "OBSOLESCENCIA", label: "Obsolescencia Tecnológica", desc: "Pérdida de capacidad operativa frente a nuevas tecnologías" },
  { id: "DESUSO", label: "Desuso Total / Inoperatividad", desc: "El bien ya no genera beneficios económicos a la entidad" },
  { id: "SINIESTRO", label: "Siniestro o Pérdida Fortuita", desc: "Destrucción por accidente, robo o caso fortuito" },
  { id: "VENTA", label: "Enajenación / Venta Comercial", desc: "Transferencia onerosa a terceros con precio de venta" },
];

export default function BajasView({ initialActivoId }: BajasViewProps) {
  const queryClient = useQueryClient();

  const [selectedActivoId, setSelectedActivoId] = useState<number | null>(initialActivoId || null);
  const [motivo, setMotivo] = useState<string>("OBSOLESCENCIA");
  const [valorVenta, setValorVenta] = useState<number | "">("");
  const [fechaBaja, setFechaBaja] = useState<string>(new Date().toISOString().split("T")[0]);
  const [observacion, setObservacion] = useState<string>("");
  const [searchFilter, setSearchFilter] = useState<string>("");
  const [resultadoBaja, setResultadoBaja] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (initialActivoId) {
      setSelectedActivoId(initialActivoId);
    }
  }, [initialActivoId]);

  const { data: activosData, isLoading: loadingActivos } = useQuery({
    queryKey: ["activos-para-baja"],
    queryFn: () => fetchActivos({ limit: 100 }),
  });

  const activosDisponibles = (activosData?.items || []).filter(
    (a: any) =>
      a.estado !== "DADO_DE_BAJA" &&
      a.estado !== "VENDIDO" &&
      (a.codigo.toLowerCase().includes(searchFilter.toLowerCase()) ||
        a.descripcion.toLowerCase().includes(searchFilter.toLowerCase()))
  );

  const activoSeleccionado = (activosData?.items || []).find(
    (a: any) => a.id_activo === selectedActivoId
  );

  const { data: previewData, isLoading: loadingPreview } = useQuery({
    queryKey: ["preview-baja", selectedActivoId, motivo, valorVenta],
    queryFn: () => {
      if (!selectedActivoId) return null;
      return previewBaja(selectedActivoId, {
        motivo,
        valor_venta: motivo === "VENTA" && valorVenta !== "" ? Number(valorVenta) : undefined,
      });
    },
    enabled: !!selectedActivoId,
  });

  const bajaMutation = useMutation({
    mutationFn: async () => {
      if (!selectedActivoId) throw new Error("Debe seleccionar un bien para la baja");
      return registrarBaja(selectedActivoId, {
        motivo,
        valor_venta: motivo === "VENTA" && valorVenta !== "" ? Number(valorVenta) : undefined,
        fecha: fechaBaja,
        observacion: observacion || undefined,
      });
    },
    onSuccess: (data) => {
      setResultadoBaja(data);
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ["dashboard-kpis"] });
      queryClient.invalidateQueries({ queryKey: ["activos"] });
      queryClient.invalidateQueries({ queryKey: ["activos-para-baja"] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || "Error al procesar la baja patrimonial");
    },
  });

  const handleReset = () => {
    setResultadoBaja(null);
    setSelectedActivoId(null);
    setValorVenta("");
    setObservacion("");
    setErrorMsg(null);
  };

  return (
    <div className="space-y-5 max-w-6xl">
      
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-3.5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Trash2 className="w-5 h-5 text-rose-700 dark:text-rose-400" />
            Liquidación Contable de Bajas (NIC 16)
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Desincorporación de bienes patrimoniales, cese de depreciación y determinación de resultado por enajenación o retiro.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded text-xs font-mono bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 shadow-xs">
            Norma: <strong className="text-slate-800 dark:text-slate-200 font-semibold">NIC 16 p. 67-72</strong>
          </span>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 dark:bg-rose-950/40 dark:border-rose-800/60 dark:text-rose-200 text-xs flex items-center gap-2.5 shadow-xs">
          <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
          <span className="font-medium">{errorMsg}</span>
        </div>
      )}

      {resultadoBaja ? (
        /* Pantalla de Éxito */
        <div className="p-6 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 max-w-xl mx-auto text-center space-y-4 shadow-sm">
          <div className="w-11 h-11 rounded-full bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/30 text-emerald-600 dark:text-emerald-400 mx-auto flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">Baja Patrimonial Completada con Éxito</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              El bien ha sido liquidado en libros y su estado en el Libro PLE 7.1 se actualizó a &apos;8 (Baja)&apos;.
            </p>
          </div>

          <div className="p-3.5 rounded bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 text-left space-y-2 font-mono text-xs">
            <div className="flex justify-between border-b border-slate-200 dark:border-slate-800 pb-1.5">
              <span className="text-slate-600 dark:text-slate-400 font-sans">Activo:</span>
              <span className="text-slate-900 dark:text-slate-200 font-semibold">{resultadoBaja.codigo} - {resultadoBaja.descripcion}</span>
            </div>
            <div className="flex justify-between border-b border-slate-200 dark:border-slate-800 pb-1.5">
              <span className="text-slate-600 dark:text-slate-400 font-sans">Causal de Baja:</span>
              <span className="text-amber-700 dark:text-amber-400 font-semibold">{resultadoBaja.motivo}</span>
            </div>
            <div className="flex justify-between border-b border-slate-200 dark:border-slate-800 pb-1.5">
              <span className="text-slate-600 dark:text-slate-400 font-sans">Valor Neto en Libros (VNL):</span>
              <span className="text-slate-900 dark:text-slate-200 font-semibold">S/ {resultadoBaja.vnl?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}</span>
            </div>
            {resultadoBaja.valor_venta !== null && (
              <div className="flex justify-between border-b border-slate-200 dark:border-slate-800 pb-1.5">
                <span className="text-slate-600 dark:text-slate-400 font-sans">Precio de Enajenación:</span>
                <span className="text-slate-900 dark:text-white font-semibold font-mono">S/ {resultadoBaja.valor_venta?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}</span>
              </div>
            )}
            <div className="flex justify-between pt-0.5 font-sans">
              <span className="text-slate-600 dark:text-slate-400">Impacto Contable:</span>
              <span className={`font-bold ${resultadoBaja.tipo_impacto === "GANANCIA" ? "text-emerald-700 dark:text-emerald-400" : "text-rose-700 dark:text-rose-400"}`}>
                {resultadoBaja.mensaje}
              </span>
            </div>
          </div>

          <div className="flex justify-center pt-1">
            <button
              onClick={handleReset}
              className="px-4 py-2 rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-semibold text-xs border border-slate-300 dark:border-slate-700 transition shadow-xs"
            >
              Registrar Otra Baja
            </button>
          </div>
        </div>
      ) : (
        /* Formulario de Liquidación */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          
          <div className="lg:col-span-7 space-y-4">
            
            <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3 shadow-xs">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <span className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[10px] flex items-center justify-center font-bold">1</span>
                  Seleccionar Activo Fijo a Liquidar
                </label>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                  {activosDisponibles.length} activos elegibles
                </span>
              </div>

              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  placeholder="Filtrar por código o descripción..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600"
                />
              </div>

              <div className="max-h-52 overflow-y-auto space-y-1.5 pr-1 custom-scrollbar">
                {loadingActivos ? (
                  <div className="text-center py-6 text-slate-500 text-xs flex items-center justify-center gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin" /> Cargando catálogo de bienes...
                  </div>
                ) : activosDisponibles.length === 0 ? (
                  <div className="text-center py-6 text-slate-500 text-xs">
                    No se encontraron activos activos disponibles para baja.
                  </div>
                ) : (
                  activosDisponibles.map((a: any) => {
                    const isSelected = a.id_activo === selectedActivoId;
                    return (
                      <button
                        key={a.id_activo}
                        type="button"
                        onClick={() => setSelectedActivoId(a.id_activo)}
                        className={`w-full text-left p-2.5 rounded border transition flex items-center justify-between ${
                          isSelected
                            ? "bg-blue-50 dark:bg-blue-950/40 border-blue-400 dark:border-blue-600 shadow-xs"
                            : "bg-slate-50/70 hover:bg-slate-100 dark:bg-slate-950/50 dark:hover:bg-slate-800/40 border-slate-200 dark:border-slate-800"
                        }`}
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-blue-700 dark:text-blue-400">{a.codigo}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 font-sans">
                              {a.categoria}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5 line-clamp-1">{a.descripcion}</p>
                        </div>
                        <div className="text-right">
                          <span className="text-xs font-mono font-bold text-slate-900 dark:text-white">
                            S/ {Number(a.costo_adquisicion).toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                          </span>
                          <span className="block text-[10px] text-slate-500 dark:text-slate-400 font-mono">{a.estado}</span>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </div>

            <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3.5 shadow-xs">
              <label className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider font-mono flex items-center gap-1.5">
                <span className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[10px] flex items-center justify-center font-bold">2</span>
                Causal y Condiciones de la Baja
              </label>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {MOTIVOS.map((m) => {
                  const isSelected = motivo === m.id;
                  return (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => setMotivo(m.id)}
                      className={`p-2.5 rounded border text-left text-xs transition ${
                        isSelected
                          ? "border-blue-600 bg-blue-50 dark:bg-blue-950/40 text-blue-900 dark:text-blue-200 font-semibold shadow-xs"
                          : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 text-slate-700 dark:text-slate-300 hover:border-slate-300"
                      }`}
                    >
                      <div className="font-semibold">{m.label}</div>
                      <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">{m.desc}</div>
                    </button>
                  );
                })}
              </div>

              {motivo === "VENTA" && (
                <div className="p-3 rounded bg-blue-50/60 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/40 space-y-1.5">
                  <label className="text-xs font-semibold text-blue-900 dark:text-blue-300 flex items-center gap-1">
                    <DollarSign className="w-3.5 h-3.5" />
                    Valor de Venta Pactado (Base Imponible sin IGV):
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-xs text-slate-400 font-mono">S/</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      placeholder="0.00"
                      value={valorVenta}
                      onChange={(e) => setValorVenta(e.target.value === "" ? "" : Number(e.target.value))}
                      className="w-full pl-8 pr-3 py-1.5 bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded text-xs font-mono text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600"
                    />
                  </div>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400">
                    Se comparará contra el Valor Neto en Libros (VNL) para reconocer el resultado por enajenación.
                  </p>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="text-[11px] text-slate-600 dark:text-slate-400 block mb-1">Fecha de Baja Contable:</label>
                  <input
                    type="date"
                    value={fechaBaja}
                    onChange={(e) => setFechaBaja(e.target.value)}
                    className="w-full px-3 py-1.5 bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded text-xs text-slate-900 dark:text-slate-200 font-mono focus:outline-none focus:ring-1 focus:ring-blue-600"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-slate-600 dark:text-slate-400 block mb-1">Informe Técnico / Resolución:</label>
                  <input
                    type="text"
                    placeholder="Ej. Informe Técnico IT-2026-088"
                    value={observacion}
                    onChange={(e) => setObservacion(e.target.value)}
                    className="w-full px-3 py-1.5 bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded text-xs text-slate-900 dark:text-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 space-y-4">
            <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3.5 shadow-xs sticky top-4">
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2.5">
                <label className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <span className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[10px] flex items-center justify-center font-bold">3</span>
                  Simulación Contable (NIC 16)
                </label>
                <Calculator className="w-4 h-4 text-slate-400" />
              </div>

              {!activoSeleccionado ? (
                <div className="p-8 text-center text-slate-500 text-xs border border-dashed border-slate-300 dark:border-slate-800 rounded">
                  Seleccione un activo en el panel izquierdo para proyectar el asiento contable de desincorporación.
                </div>
              ) : loadingPreview ? (
                <div className="p-8 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-blue-600" /> Calculando impacto...
                </div>
              ) : previewData ? (
                <div className="space-y-3.5">
                  <div>
                    <span className="text-[10px] font-mono font-bold text-blue-700 dark:text-blue-400">{previewData.codigo}</span>
                    <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">{previewData.descripcion}</h3>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                      Categoría: {previewData.categoria}
                    </p>
                  </div>

                  <div className="p-3 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800 space-y-2 text-xs font-mono">
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400 font-sans">Costo de Adquisición:</span>
                      <span className="text-slate-900 dark:text-white font-bold">S/ {previewData.costo_adquisicion?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400 font-sans">(-) Deprec. Acumulada:</span>
                      <span className="text-slate-700 dark:text-slate-300 font-medium">(-) S/ {previewData.depreciacion_acumulada?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div className="flex justify-between border-t border-slate-200 dark:border-slate-800 pt-2 font-bold">
                      <span className="text-slate-800 dark:text-slate-200 font-sans">Valor Neto Libros (VNL):</span>
                      <span className="text-slate-900 dark:text-white">S/ {previewData.vnl?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}</span>
                    </div>
                    {previewData.valor_venta !== null && (
                      <div className="flex justify-between border-t border-slate-200 dark:border-slate-800 pt-1.5">
                        <span className="text-slate-600 dark:text-slate-400 font-sans">Precio de Venta (sin IGV):</span>
                        <span className="text-slate-900 dark:text-white font-bold">S/ {previewData.valor_venta?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}</span>
                      </div>
                    )}
                  </div>

                  <div
                    className={`p-3 rounded border text-xs ${
                      previewData.tipo_impacto === "GANANCIA"
                        ? "bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/30 dark:border-emerald-800/40 dark:text-emerald-300"
                        : "bg-rose-50 border-rose-200 text-rose-800 dark:bg-rose-950/30 dark:border-rose-800/40 dark:text-rose-300"
                    }`}
                  >
                    <div className="flex items-center gap-1.5 font-bold mb-1">
                      {previewData.tipo_impacto === "GANANCIA" ? (
                        <TrendingUp className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                      ) : (
                        <TrendingDown className="w-4 h-4 text-rose-600 dark:text-rose-400" />
                      )}
                      <span>Resultado: {previewData.tipo_impacto}</span>
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      {previewData.mensaje}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => bajaMutation.mutate()}
                    disabled={bajaMutation.isPending}
                    className="w-full py-2.5 rounded bg-rose-700 hover:bg-rose-800 text-white font-semibold text-xs shadow-xs transition flex items-center justify-center gap-2"
                  >
                    {bajaMutation.isPending ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Desincorporando bien de libros...</span>
                      </>
                    ) : (
                      <>
                        <Trash2 className="w-3.5 h-3.5" />
                        <span>Confirmar & Liquidar Baja Definitiva</span>
                      </>
                    )}
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
