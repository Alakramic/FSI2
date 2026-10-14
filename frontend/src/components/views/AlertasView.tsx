"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAlertasVidaUtil, fetchAlertasHuerfanos } from "@/lib/api";
import {
  AlertTriangle,
  Clock,
  UserX,
  MapPin,
  CheckCircle2,
  RefreshCw,
  Search,
  Filter,
  ArrowRight,
  ShieldAlert,
  AlertCircle,
  Eye,
} from "lucide-react";

interface AlertasViewProps {
  onSelectActivo?: (idActivo: number) => void;
}

export default function AlertasView({ onSelectActivo }: AlertasViewProps) {
  const [activeTab, setActiveTab] = useState<"vida-util" | "huerfanos">("vida-util");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [filtroNivel, setFiltroNivel] = useState<string>("TODOS");

  const {
    data: dataVidaUtil,
    isLoading: loadingVidaUtil,
    refetch: refetchVidaUtil,
    isRefetching: refetchingVidaUtil,
  } = useQuery({
    queryKey: ["alertas-vida-util"],
    queryFn: fetchAlertasVidaUtil,
  });

  const {
    data: dataHuerfanos,
    isLoading: loadingHuerfanos,
    refetch: refetchHuerfanos,
    isRefetching: refetchingHuerfanos,
  } = useQuery({
    queryKey: ["alertas-huerfanos"],
    queryFn: fetchAlertasHuerfanos,
  });

  const totalCriticas = (dataVidaUtil?.alertas || []).filter(
    (a: any) => a.nivel_alerta === "CRITICA_30_DIAS"
  ).length;

  const totalPreventivas = (dataVidaUtil?.alertas || []).filter(
    (a: any) => a.nivel_alerta === "PREVENTIVA_60_DIAS"
  ).length;

  const totalHuerfanos = dataHuerfanos?.total_huerfanos || 0;

  // Filtrado de alertas de vida útil
  const alertasFiltradas = (dataVidaUtil?.alertas || []).filter((a: any) => {
    const matchesNivel = filtroNivel === "TODOS" || a.nivel_alerta === filtroNivel;
    const matchesSearch =
      a.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.descripcion.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.categoria.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesNivel && matchesSearch;
  });

  // Filtrado de huérfanos
  const huerfanosFiltrados = (dataHuerfanos?.activos || []).filter((a: any) => {
    return (
      a.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.descripcion.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.categoria.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  const handleRefreshAll = () => {
    refetchVidaUtil();
    refetchHuerfanos();
  };

  return (
    <div className="space-y-5 max-w-6xl">
      
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-3.5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            Auditoría Patrimonial y Control Preventivo
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Detección oportuna de agotamiento de vida útil contable e inconsistencias de asignación de custodios según NIC 16.
          </p>
        </div>

        <button
          onClick={handleRefreshAll}
          disabled={refetchingVidaUtil || refetchingHuerfanos}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-200 font-semibold transition shadow-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refetchingVidaUtil || refetchingHuerfanos ? "animate-spin" : ""}`} />
          <span>Actualizar Diagnóstico</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">
              Alertas Totales
            </span>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
            {dataVidaUtil?.total_alertas ?? 0}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Bienes por culminar depreciación</p>
        </div>

        <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">
              Crítica (&le; 30 días)
            </span>
            <span className="px-1.5 py-0.5 rounded bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800/40 text-[10px] font-mono font-bold">
              Urgente
            </span>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">{totalCriticas}</div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Requieren evaluación de baja o mejora</p>
        </div>

        <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">
              Preventiva (&le; 60 días)
            </span>
            <span className="px-1.5 py-0.5 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800/40 text-[10px] font-mono font-bold">
              60 días
            </span>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">{totalPreventivas}</div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">En último bimestre de vida útil</p>
        </div>

        <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">
              Activos Huérfanos
            </span>
            <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 text-[10px] font-mono font-bold">
              Control
            </span>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">{totalHuerfanos}</div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Sin custodio o sede asignada</p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("vida-util")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-semibold transition ${
              activeTab === "vida-util"
                ? "bg-white dark:bg-slate-800 text-blue-700 dark:text-blue-300 border border-slate-300 dark:border-slate-700 shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>Vida Útil por Vencer</span>
            <span className="px-1.5 py-0.2 rounded bg-slate-100 dark:bg-slate-950 text-[10px] font-mono text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800">
              {dataVidaUtil?.total_alertas ?? 0}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("huerfanos")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-semibold transition ${
              activeTab === "huerfanos"
                ? "bg-white dark:bg-slate-800 text-blue-700 dark:text-blue-300 border border-slate-300 dark:border-slate-700 shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            <UserX className="w-3.5 h-3.5" />
            <span>Activos Huérfanos</span>
            <span className="px-1.5 py-0.2 rounded bg-slate-100 dark:bg-slate-950 text-[10px] font-mono text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800">
              {totalHuerfanos}
            </span>
          </button>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
            <input
              type="text"
              placeholder="Filtrar por código o descripción..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1 bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded text-xs text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 w-56"
            />
          </div>

          {activeTab === "vida-util" && (
            <select
              value={filtroNivel}
              onChange={(e) => setFiltroNivel(e.target.value)}
              className="px-2.5 py-1 bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              <option value="TODOS">Todos los niveles</option>
              <option value="CRITICA_30_DIAS">Crítica (&le; 30 días)</option>
              <option value="PREVENTIVA_60_DIAS">Preventiva (&le; 60 días)</option>
            </select>
          )}
        </div>
      </div>

      {activeTab === "vida-util" && (
        <div className="space-y-4">
          {loadingVidaUtil ? (
            <div className="text-center py-12 text-slate-500 text-xs flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin" /> Auditando vidas útiles en motor contable...
            </div>
          ) : alertasFiltradas.length === 0 ? (
            <div className="p-8 text-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-500 text-xs shadow-xs">
              <CheckCircle2 className="w-6 h-6 text-emerald-600 dark:text-emerald-400 mx-auto mb-2" />
              No existen alertas de agotamiento de vida útil bajo los filtros seleccionados.
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden shadow-xs">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-950/80 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-800 uppercase tracking-wider">
                  <tr>
                    <th className="p-3">Código</th>
                    <th className="p-3">Descripción del Activo</th>
                    <th className="p-3">Categoría</th>
                    <th className="p-3 text-right">Costo Histórico</th>
                    <th className="p-3 text-right">VNL Actual</th>
                    <th className="p-3 text-center">Nivel de Alerta</th>
                    <th className="p-3 text-right">Días Remanentes</th>
                    <th className="p-3 text-center">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 bg-white dark:bg-slate-900/40">
                  {alertasFiltradas.map((a: any) => (
                    <tr key={a.id_activo} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition">
                      <td className="p-3 font-mono font-bold text-blue-700 dark:text-blue-400">{a.codigo}</td>
                      <td className="p-3 font-medium text-slate-800 dark:text-slate-200 max-w-xs truncate" title={a.descripcion}>
                        {a.descripcion}
                      </td>
                      <td className="p-3 text-slate-600 dark:text-slate-400">{a.categoria}</td>
                      <td className="p-3 text-right font-mono text-slate-900 dark:text-white font-bold">
                        S/ {Number(a.costo_adquisicion).toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="p-3 text-right font-mono text-slate-900 dark:text-white font-bold">
                        S/ {Number(a.vnl_actual).toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="p-3 text-center">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${
                            a.nivel_alerta === "CRITICA_30_DIAS"
                              ? "bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 border-rose-200 dark:border-rose-800/40"
                              : "bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800/40"
                          }`}
                        >
                          {a.nivel_alerta === "CRITICA_30_DIAS" ? "CRÍTICA (≤ 30d)" : "PREVENTIVA (≤ 60d)"}
                        </span>
                      </td>
                      <td className="p-3 text-right font-mono font-bold text-slate-900 dark:text-white">
                        {a.dias_restantes} días
                      </td>
                      <td className="p-3 text-center">
                        {onSelectActivo && (
                          <button
                            onClick={() => onSelectActivo(a.id_activo)}
                            className="px-2 py-1 bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 rounded transition text-xs font-semibold flex items-center gap-1 mx-auto shadow-xs"
                          >
                            <Eye className="w-3 h-3 text-slate-500" /> Ver Hoja
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === "huerfanos" && (
        <div className="space-y-4">
          {loadingHuerfanos ? (
            <div className="text-center py-12 text-slate-500 text-xs flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin" /> Verificando asignaciones físicas de bienes...
            </div>
          ) : huerfanosFiltrados.length === 0 ? (
            <div className="p-8 text-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-500 text-xs shadow-xs">
              <CheckCircle2 className="w-6 h-6 text-emerald-600 dark:text-emerald-400 mx-auto mb-2" />
              Excelente. Todos los activos en uso cuentan con custodio formal y sede física asignada.
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden shadow-xs">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-950/80 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-800 uppercase tracking-wider">
                  <tr>
                    <th className="p-3">Código</th>
                    <th className="p-3">Descripción</th>
                    <th className="p-3">Categoría</th>
                    <th className="p-3">Custodio Actual</th>
                    <th className="p-3">Ubicación / Sede</th>
                    <th className="p-3 text-center">Inconsistencia</th>
                    <th className="p-3 text-center">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 bg-white dark:bg-slate-900/40">
                  {huerfanosFiltrados.map((h: any) => (
                    <tr key={h.id_activo} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition">
                      <td className="p-3 font-mono font-bold text-blue-700 dark:text-blue-400">{h.codigo}</td>
                      <td className="p-3 font-medium text-slate-800 dark:text-slate-200 max-w-xs truncate" title={h.descripcion}>
                        {h.descripcion}
                      </td>
                      <td className="p-3 text-slate-600 dark:text-slate-400">{h.categoria}</td>
                      <td className="p-3">
                        {h.custodio ? (
                          <span className="text-slate-700 dark:text-slate-300">{h.custodio}</span>
                        ) : (
                          <span className="text-rose-700 dark:text-rose-400 font-semibold">[Sin Custodio Asignado]</span>
                        )}
                      </td>
                      <td className="p-3">
                        {h.ubicacion ? (
                          <span className="text-slate-700 dark:text-slate-300">{h.ubicacion}</span>
                        ) : (
                          <span className="text-amber-700 dark:text-amber-400 font-semibold">[Sin Sede Asignada]</span>
                        )}
                      </td>
                      <td className="p-3 text-center">
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/40">
                          {h.inconsistencia || "HUÉRFANO"}
                        </span>
                      </td>
                      <td className="p-3 text-center">
                        {onSelectActivo && (
                          <button
                            onClick={() => onSelectActivo(h.id_activo)}
                            className="px-2 py-1 bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 rounded transition text-xs font-semibold flex items-center gap-1 mx-auto shadow-xs"
                          >
                            <ArrowRight className="w-3 h-3 text-slate-500" /> Regularizar
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
