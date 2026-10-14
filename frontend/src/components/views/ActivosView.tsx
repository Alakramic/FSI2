"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchActivos,
  fetchCatalogos,
  fetchActivoDetalle,
  registrarTraslado,
  registrarMantenimiento,
} from "@/lib/api";
import {
  Search,
  Plus,
  RefreshCw,
  Building2,
  Calendar,
  Layers,
  Wrench,
  ArrowRightLeft,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle,
  Eye,
  Trash2,
  X,
  Loader2,
} from "lucide-react";

export default function ActivosView({ onNavigateToBaja }: { onNavigateToBaja?: (idActivo: number) => void }) {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [categoriaFilter, setCategoriaFilter] = useState("");
  const [estadoFilter, setEstadoFilter] = useState("");
  const [selectedActivoId, setSelectedActivoId] = useState<number | null>(null);

  // Modales internos
  const [modalTrasladoOpen, setModalTrasladoOpen] = useState(false);
  const [modalMantOpen, setModalMantOpen] = useState(false);

  // Form states
  const [trasladoDestino, setTrasladoDestino] = useState<number | "">("");
  const [trasladoMotivo, setTrasladoMotivo] = useState("");
  const [trasladoAutorizado, setTrasladoAutorizado] = useState<number | "">("");

  const [mantTipo, setMantTipo] = useState("PREVENTIVO");
  const [mantDesc, setMantDesc] = useState("");
  const [mantCosto, setMantCosto] = useState<number>(0);

  const [feedbackMsg, setFeedbackMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const { data: catalogos } = useQuery({
    queryKey: ["catalogos-maestros"],
    queryFn: fetchCatalogos,
  });

  const { data: activosData, isLoading: loadingActivos } = useQuery({
    queryKey: ["activos", search, categoriaFilter, estadoFilter],
    queryFn: () =>
      fetchActivos({
        q: search || undefined,
        categoria_id: categoriaFilter || undefined,
        estado: estadoFilter || undefined,
        limit: 100,
      }),
  });

  const { data: detalle, isLoading: loadingDetalle, refetch: refetchDetalle } = useQuery({
    queryKey: ["activo-detalle", selectedActivoId],
    queryFn: () => (selectedActivoId ? fetchActivoDetalle(selectedActivoId) : null),
    enabled: !!selectedActivoId,
  });

  // Mutación de Traslado
  const trasladoMutation = useMutation({
    mutationFn: async () => {
      if (!selectedActivoId || !trasladoDestino || !trasladoMotivo || !trasladoAutorizado) {
        throw new Error("Complete todos los campos del traslado.");
      }
      return registrarTraslado(selectedActivoId, {
        id_ubicacion_destino: Number(trasladoDestino),
        motivo: trasladoMotivo,
        id_autorizado_por: Number(trasladoAutorizado),
      });
    },
    onSuccess: () => {
      setFeedbackMsg({ type: "success", text: "Traslado registrado exitosamente." });
      setModalTrasladoOpen(false);
      setTrasladoMotivo("");
      refetchDetalle();
      queryClient.invalidateQueries({ queryKey: ["activos"] });
    },
    onError: (err: any) => {
      setFeedbackMsg({ type: "error", text: err.message || "Error registrando traslado" });
    },
  });

  // Mutación de Mantenimiento
  const mantMutation = useMutation({
    mutationFn: async () => {
      if (!selectedActivoId || !mantDesc) {
        throw new Error("Describa el servicio de mantenimiento.");
      }
      return registrarMantenimiento(selectedActivoId, {
        tipo: mantTipo,
        descripcion: mantDesc,
        costo: Number(mantCosto) || 0,
      });
    },
    onSuccess: () => {
      setFeedbackMsg({ type: "success", text: "Orden de mantenimiento registrada." });
      setModalMantOpen(false);
      setMantDesc("");
      setMantCosto(0);
      refetchDetalle();
    },
    onError: (err: any) => {
      setFeedbackMsg({ type: "error", text: err.message || "Error registrando mantenimiento" });
    },
  });

  return (
    <div className="space-y-5">
      
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-3.5">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            Padrón de Activos Fijos
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Gestión patrimonial, trazabilidad física entre sedes y hojas de vida técnica según NIC 16.
          </p>
        </div>
        <div className="text-xs text-slate-600 dark:text-slate-400 font-mono bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-3 py-1.5 rounded shadow-xs">
          Total registrados: <strong className="text-blue-700 dark:text-blue-400">{activosData?.total || 0}</strong> bienes
        </div>
      </div>

      {feedbackMsg && (
        <div
          className={`p-3 rounded text-xs flex items-center justify-between gap-3 shadow-xs ${
            feedbackMsg.type === "success"
              ? "bg-emerald-50 border border-emerald-200 text-emerald-800 dark:bg-emerald-950/40 dark:border-emerald-800/60 dark:text-emerald-200"
              : "bg-rose-50 border border-rose-200 text-rose-800 dark:bg-rose-950/40 dark:border-rose-800/60 dark:text-rose-200"
          }`}
        >
          <div className="flex items-center gap-2">
            {feedbackMsg.type === "success" ? (
              <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400" />
            )}
            <span className="font-medium">{feedbackMsg.text}</span>
          </div>
          <button onClick={() => setFeedbackMsg(null)} className="text-slate-400 hover:text-slate-600 dark:hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3.5 rounded-lg shadow-xs flex flex-wrap gap-3 items-center">
        <div className="flex-1 min-w-[240px] relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Buscar por código patrimonial o descripción..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-1.5 pl-9 pr-3 text-xs text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
          />
        </div>

        <select
          value={categoriaFilter}
          onChange={(e) => setCategoriaFilter(e.target.value)}
          className="bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-1.5 px-3 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
        >
          <option value="">Todas las Categorías</option>
          {catalogos?.categorias?.map((c: any) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>

        <select
          value={estadoFilter}
          onChange={(e) => setEstadoFilter(e.target.value)}
          className="bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-1.5 px-3 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
        >
          <option value="">Todos los Estados</option>
          <option value="EN_USO">En Uso</option>
          <option value="EN_MANTENIMIENTO">En Mantenimiento</option>
          <option value="DADO_DE_BAJA">Dado de Baja</option>
          <option value="VENDIDO">Vendido</option>
        </select>
      </div>

      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-950/80 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-800 uppercase tracking-wider">
              <tr>
                <th className="p-3">Código Patrimonial</th>
                <th className="p-3">Descripción</th>
                <th className="p-3">Categoría</th>
                <th className="p-3">Ubicación Actual</th>
                <th className="p-3">Custodio Asignado</th>
                <th className="p-3 text-right">Costo Orig.</th>
                <th className="p-3 text-center">Estado</th>
                <th className="p-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 bg-white dark:bg-slate-900/40">
              {loadingActivos ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-slate-500">
                    <Loader2 className="w-5 h-5 animate-spin mx-auto text-blue-600 mb-2" />
                    Cargando bienes patrimoniales...
                  </td>
                </tr>
              ) : activosData?.items?.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-slate-500">
                    No se encontraron activos con los criterios seleccionados.
                  </td>
                </tr>
              ) : (
                activosData?.items?.map((item: any) => (
                  <tr key={item.id_activo} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition">
                    <td className="p-3 font-mono font-bold text-blue-700 dark:text-blue-400">{item.codigo}</td>
                    <td className="p-3 font-medium text-slate-800 dark:text-slate-200 max-w-xs truncate" title={item.descripcion}>
                      {item.descripcion}
                    </td>
                    <td className="p-3 text-slate-600 dark:text-slate-400">{item.categoria}</td>
                    <td className="p-3 text-slate-600 dark:text-slate-400">{item.ubicacion}</td>
                    <td className="p-3 text-slate-700 dark:text-slate-300">{item.custodio}</td>
                    <td className="p-3 text-right font-mono font-bold text-slate-900 dark:text-white">
                      S/ {Number(item.costo_adquisicion).toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="p-3 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${
                          item.estado === "EN_USO"
                            ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-500/20"
                            : item.estado === "EN_MANTENIMIENTO"
                            ? "bg-amber-50 dark:bg-amber-500/10 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-500/20"
                            : item.estado === "VENDIDO"
                            ? "bg-blue-50 dark:bg-blue-500/10 text-blue-800 dark:text-blue-300 border-blue-200 dark:border-blue-500/20"
                            : "bg-rose-50 dark:bg-rose-500/10 text-rose-800 dark:text-rose-300 border-rose-200 dark:border-rose-500/20"
                        }`}
                      >
                        {item.estado}
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      <button
                        onClick={() => setSelectedActivoId(item.id_activo)}
                        className="px-2.5 py-1 bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 rounded transition text-xs font-semibold flex items-center gap-1 mx-auto shadow-xs"
                      >
                        <Eye className="w-3.5 h-3.5 text-slate-500" /> Hoja de Vida
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Hoja de Vida del Activo */}
      {selectedActivoId && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-5 shadow-xl relative">
            <button
              onClick={() => setSelectedActivoId(null)}
              className="absolute right-4 top-4 p-1.5 rounded text-slate-400 hover:text-slate-600 dark:hover:text-white transition"
            >
              <X className="w-4 h-4" />
            </button>

            {loadingDetalle || !detalle ? (
              <div className="p-12 text-center text-slate-500">
                <Loader2 className="w-7 h-7 animate-spin mx-auto text-blue-600 mb-2" />
                Cargando expediente patrimonial...
              </div>
            ) : (
              <>
                <div className="border-b border-slate-200 dark:border-slate-800 pb-3.5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold px-2 py-0.5 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/40 rounded">
                      {detalle.codigo}
                    </span>
                    <span className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold">
                      {detalle.categoria}
                    </span>
                  </div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white mt-1.5">{detalle.descripcion}</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Marca: <strong className="text-slate-700 dark:text-slate-300">{detalle.marca}</strong> | Modelo:{" "}
                    <strong className="text-slate-700 dark:text-slate-300">{detalle.modelo}</strong> | N° Serie:{" "}
                    <strong className="text-slate-900 dark:text-white font-mono">{detalle.numero_serie}</strong>
                  </p>
                </div>

                {/* Situación Financiera */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="p-3 rounded bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
                    <span className="text-[11px] text-slate-500 dark:text-slate-400 block uppercase font-mono font-semibold">Costo Histórico</span>
                    <span className="text-base font-bold font-mono text-slate-900 dark:text-white mt-0.5 block">
                      S/ {detalle.costo_adquisicion?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="p-3 rounded bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
                    <span className="text-[11px] text-slate-500 dark:text-slate-400 block uppercase font-mono font-semibold">Depreciación Acum.</span>
                    <span className="text-base font-bold font-mono text-slate-900 dark:text-white mt-0.5 block">
                      S/ {detalle.situacion_financiera?.depreciacion_acumulada?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="p-3 rounded bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
                    <span className="text-[11px] text-slate-500 dark:text-slate-400 block uppercase font-mono font-semibold">Valor Neto Libros (VNL)</span>
                    <span className="text-base font-bold font-mono text-slate-900 dark:text-white mt-0.5 block">
                      S/ {detalle.situacion_financiera?.valor_neto_en_libros?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                {/* Custodia y Ubicación */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-slate-50 dark:bg-slate-950/40 p-3.5 rounded border border-slate-200 dark:border-slate-800">
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block font-medium">Custodio Responsable:</span>
                    <span className="text-slate-900 dark:text-white font-semibold mt-0.5 block">{detalle.custodio}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block font-medium">Ubicación Física Actual:</span>
                    <span className="text-slate-900 dark:text-white font-semibold mt-0.5 block">{detalle.ubicacion}</span>
                  </div>
                </div>

                {/* Acciones Rápidas */}
                <div className="flex flex-wrap gap-2 pt-1">
                  <button
                    onClick={() => {
                      if (catalogos?.ubicaciones?.length > 0) {
                        setTrasladoDestino(catalogos.ubicaciones[0].id);
                      }
                      if (catalogos?.empleados?.length > 0) {
                        setTrasladoAutorizado(catalogos.empleados[0].id);
                      }
                      setModalTrasladoOpen(true);
                    }}
                    className="px-3 py-1.5 bg-blue-700 hover:bg-blue-800 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition shadow-xs"
                  >
                    <ArrowRightLeft className="w-3.5 h-3.5" /> Registrar Traslado
                  </button>
                  <button
                    onClick={() => setModalMantOpen(true)}
                    className="px-3 py-1.5 bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded text-xs font-semibold flex items-center gap-1.5 transition border border-slate-300 dark:border-slate-700 shadow-xs"
                  >
                    <Wrench className="w-3.5 h-3.5" /> Orden de Mantenimiento
                  </button>
                  {detalle.estado === "EN_USO" && onNavigateToBaja && (
                    <button
                      onClick={() => {
                        setSelectedActivoId(null);
                        onNavigateToBaja(detalle.id_activo);
                      }}
                      className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 rounded text-xs font-semibold flex items-center gap-1.5 transition border border-rose-300 dark:border-rose-800/40 shadow-xs"
                    >
                      <Trash2 className="w-3.5 h-3.5" /> Liquidar Baja
                    </button>
                  )}
                </div>

                {/* Historial de Traslados */}
                <div className="space-y-1.5 pt-2">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider font-mono">Historial de Traslados</h4>
                  <div className="divide-y divide-slate-200 dark:divide-slate-800 bg-slate-50 dark:bg-slate-950/60 rounded border border-slate-200 dark:border-slate-800 text-xs">
                    {detalle.historial_traslados?.length === 0 ? (
                      <p className="p-3 text-slate-500 italic">Sin traslados registrados (permanece en sede inicial).</p>
                    ) : (
                      detalle.historial_traslados?.map((t: any, i: number) => (
                        <div key={i} className="p-2.5 flex justify-between items-center">
                          <div>
                            <span className="text-slate-900 dark:text-white font-medium">{t.origen} → {t.destino}</span>
                            <span className="text-[11px] text-slate-500 dark:text-slate-400 block mt-0.5">{t.motivo}</span>
                          </div>
                          <span className="text-slate-500 text-[11px] font-mono">{t.fecha}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Historial de Mantenimientos */}
                <div className="space-y-1.5">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider font-mono">Historial de Mantenimientos</h4>
                  <div className="divide-y divide-slate-200 dark:divide-slate-800 bg-slate-50 dark:bg-slate-950/60 rounded border border-slate-200 dark:border-slate-800 text-xs">
                    {detalle.historial_mantenimientos?.length === 0 ? (
                      <p className="p-3 text-slate-500 italic">Sin mantenimientos registrados a la fecha.</p>
                    ) : (
                      detalle.historial_mantenimientos?.map((m: any, i: number) => (
                        <div key={i} className="p-2.5 flex justify-between items-center">
                          <div>
                            <span className="text-slate-900 dark:text-white font-medium">[{m.tipo}] {m.descripcion}</span>
                            <span className="text-[11px] text-slate-500 dark:text-slate-400 block mt-0.5">Proveedor: {m.proveedor}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-slate-900 dark:text-white font-mono font-bold">S/ {Number(m.costo).toLocaleString("es-PE", { minimumFractionDigits: 2 })}</span>
                            <span className="text-slate-500 text-[10px] block font-mono">{m.fecha}</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Submodal Registrar Traslado */}
      {modalTrasladoOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg max-w-md w-full p-5 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <ArrowRightLeft className="w-4 h-4 text-blue-600" /> Registrar Traslado Físico
            </h3>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Nueva Sede / Ubicación Destino *</label>
              <select
                value={trasladoDestino}
                onChange={(e) => setTrasladoDestino(Number(e.target.value))}
                className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-1.5 px-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-600"
              >
                {catalogos?.ubicaciones?.map((ub: any) => (
                  <option key={ub.id} value={ub.id}>
                    {ub.nombre} ({ub.sede})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Motivo del Traslado *</label>
              <input
                type="text"
                placeholder="Ej: Asignación a nueva oficina de gerencia"
                value={trasladoMotivo}
                onChange={(e) => setTrasladoMotivo(e.target.value)}
                className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-1.5 px-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-600"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Autorizado por (Empleado) *</label>
              <select
                value={trasladoAutorizado}
                onChange={(e) => setTrasladoAutorizado(Number(e.target.value))}
                className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-1.5 px-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-600"
              >
                {catalogos?.empleados?.map((emp: any) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setModalTrasladoOpen(false)}
                className="px-3 py-1.5 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs rounded border border-slate-300 dark:border-slate-700"
              >
                Cancelar
              </button>
              <button
                onClick={() => trasladoMutation.mutate()}
                disabled={trasladoMutation.isPending}
                className="px-3 py-1.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded shadow-xs"
              >
                Guardar Traslado
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Submodal Registrar Mantenimiento */}
      {modalMantOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg max-w-md w-full p-5 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Wrench className="w-4 h-4 text-blue-600" /> Registrar Orden de Servicio
            </h3>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Tipo de Mantenimiento</label>
              <select
                value={mantTipo}
                onChange={(e) => setMantTipo(e.target.value)}
                className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-1.5 px-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-600"
              >
                <option value="PREVENTIVO">PREVENTIVO</option>
                <option value="CORRECTIVO">CORRECTIVO</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Descripción del Trabajo *</label>
              <textarea
                rows={3}
                placeholder="Detalle de tareas realizadas..."
                value={mantDesc}
                onChange={(e) => setMantDesc(e.target.value)}
                className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-1.5 px-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-600"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Costo del Mantenimiento (S/)</label>
              <input
                type="number"
                step="0.01"
                value={mantCosto}
                onChange={(e) => setMantCosto(Number(e.target.value))}
                className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-1.5 px-3 text-xs text-slate-900 dark:text-white font-mono focus:outline-none focus:ring-1 focus:ring-blue-600"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setModalMantOpen(false)}
                className="px-3 py-1.5 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs rounded border border-slate-300 dark:border-slate-700"
              >
                Cancelar
              </button>
              <button
                onClick={() => mantMutation.mutate()}
                disabled={mantMutation.isPending}
                className="px-3 py-1.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded shadow-xs"
              >
                Guardar Mantenimiento
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
