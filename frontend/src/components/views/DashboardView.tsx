"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchKpis, fetchAlertasVidaUtil, fetchAlertasHuerfanos, fetchActivos } from "@/lib/api";
import {
  TrendingDown,
  Building2,
  AlertTriangle,
  FileCheck,
  DollarSign,
  Layers,
  ArrowRight,
  ShieldCheck,
  Clock,
  UserX,
  FileSpreadsheet,
  Calendar,
  CheckCircle2,
  RefreshCw
} from "lucide-react";

export default function DashboardView({ onNavigate }: { onNavigate: (tab: string) => void }) {
  const { data: kpis, isLoading: loadingKpis } = useQuery({
    queryKey: ["dashboard-kpis"],
    queryFn: fetchKpis,
  });

  const { data: alertasVU } = useQuery({
    queryKey: ["alertas-vida-util"],
    queryFn: fetchAlertasVidaUtil,
  });

  const { data: alertasHuerfanos } = useQuery({
    queryKey: ["alertas-huerfanos"],
    queryFn: fetchAlertasHuerfanos,
  });

  const { data: ultimosActivos, isLoading: loadingUltimos } = useQuery({
    queryKey: ["dashboard-ultimos-activos"],
    queryFn: () => fetchActivos({ limit: 5 }),
  });

  return (
    <div className="space-y-5">
      
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-3.5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Resumen Ejecutivo Patrimonial y Contable
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Control de inventario de activos duraderos, devengo de depreciación según NIC 16 y libros SUNAT PLE 7.1
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate("depreciacion")}
            className="px-3 py-1.5 rounded bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold border border-slate-300 dark:border-slate-700 shadow-xs transition flex items-center gap-1.5"
          >
            <Calendar className="w-3.5 h-3.5 text-slate-600 dark:text-blue-400" />
            <span>Consola de Cierre</span>
          </button>
          <button
            onClick={() => onNavigate("ingesta")}
            className="px-3 py-1.5 rounded bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold shadow-xs transition flex items-center gap-1.5"
          >
            <span>+ Ingestar Comprobante</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        
        <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">
              Bienes en Custodia
            </span>
            <Layers className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
            {kpis?.total_activos_en_uso || 0}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Bienes operativos en la organización
          </p>
        </div>

        <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">
              Costo Histórico Total
            </span>
            <DollarSign className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
            S/ {(kpis?.costo_patrimonial_total || 0).toLocaleString("es-PE", { minimumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Histórico + S/ {(kpis?.mejoras_capitalizadas || 0).toLocaleString("es-PE")} en mejoras
          </p>
        </div>

        <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">
              Depreciación Acumulada
            </span>
            <TrendingDown className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
            S/ {(kpis?.depreciacion_acumulada_total || 0).toLocaleString("es-PE", { minimumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Desgaste contable devengado acumulado
          </p>
        </div>

        <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">
              Valor Neto en Libros (VNL)
            </span>
            <FileCheck className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
            S/ {(kpis?.valor_neto_en_libros_total || 0).toLocaleString("es-PE", { minimumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Patrimonio neto remanente en libros
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        
        <div className="lg:col-span-7 space-y-5">
          
          <div className="rounded-lg border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-xs">
            <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/60 flex items-center justify-between">
              <div>
                <h2 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider font-mono">
                  Últimos Bienes Registrados en Patrimonio
                </h2>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">Incorporaciones recientes al padrón general</p>
              </div>
              <button
                onClick={() => onNavigate("activos")}
                className="text-[11px] text-blue-700 dark:text-blue-400 hover:text-blue-800 font-semibold flex items-center gap-1 transition"
              >
                <span>Ver Padrón Completo</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-950/80 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 font-semibold">
                  <tr>
                    <th className="px-4 py-2.5">Código</th>
                    <th className="px-3 py-2.5">Descripción del Bien</th>
                    <th className="px-3 py-2.5">Categoría</th>
                    <th className="px-3 py-2.5 text-right">Costo (S/)</th>
                    <th className="px-3 py-2.5 text-center">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
                  {loadingUltimos ? (
                    <tr>
                      <td colSpan={5} className="text-center py-8 text-slate-500 text-xs">
                        <RefreshCw className="w-4 h-4 animate-spin mx-auto mb-1 text-slate-400" />
                        Cargando inventario...
                      </td>
                    </tr>
                  ) : (ultimosActivos?.items || ultimosActivos?.data || []).slice(0, 5).map((a: any) => (
                    <tr key={a.id_activo} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition">
                      <td className="px-4 py-2.5 font-mono font-bold text-slate-800 dark:text-slate-200">
                        {a.codigo}
                      </td>
                      <td className="px-3 py-2.5 text-slate-700 dark:text-slate-300 max-w-[200px] truncate" title={a.descripcion}>
                        {a.descripcion}
                      </td>
                      <td className="px-3 py-2.5 text-slate-500 dark:text-slate-400 text-[11px]">
                        {a.categoria}
                      </td>
                      <td className="px-3 py-2.5 font-mono text-right text-slate-900 dark:text-slate-200 font-semibold">
                        S/ {Number(a.costo_adquisicion).toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${
                          a.estado === "EN_USO"
                            ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-500/20"
                            : a.estado === "DADO_DE_BAJA"
                            ? "bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-500/20"
                            : "bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-500/20"
                        }`}>
                          {a.estado}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-lg border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 space-y-3 shadow-xs">
            <h2 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider font-mono">
              Composición de Cartera por Tipo de Activo Fijo (Tabla 18 SUNAT)
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
              <div className="p-3 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800/80">
                <span className="text-[11px] text-slate-600 dark:text-slate-400 font-medium">Equipos de Cómputo</span>
                <div className="text-base font-bold font-mono text-slate-900 dark:text-white mt-1">S/ 21,450.00</div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">5 unidades activas</div>
              </div>
              <div className="p-3 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800/80">
                <span className="text-[11px] text-slate-600 dark:text-slate-400 font-medium">Muebles y Enseres</span>
                <div className="text-base font-bold font-mono text-slate-900 dark:text-white mt-1">S/ 4,000.00</div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">4 unidades activas</div>
              </div>
              <div className="p-3 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800/80">
                <span className="text-[11px] text-slate-600 dark:text-slate-400 font-medium">Maquinaria y Equipos</span>
                <div className="text-base font-bold font-mono text-slate-900 dark:text-white mt-1">S/ 14,000.00</div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">2 unidades activas</div>
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-5 space-y-5">
          
          <div className="rounded-lg border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-xs space-y-3.5">
            <div className="flex items-center justify-between pb-2.5 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-slate-600 dark:text-blue-400" />
                <h3 className="text-xs font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider font-mono">
                  Periodo Contable y Depreciación
                </h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-500/20">
                Periodo: {kpis?.ultimo_periodo_cerrado || "2026-10"}
              </span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800/70">
                <span className="text-slate-600 dark:text-slate-400 font-sans">Gasto Mensual Devengado:</span>
                <span className="text-slate-900 dark:text-white font-bold">
                  S/ {(kpis?.depreciacion_ultimo_mes || 0).toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between p-2 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800/70">
                <span className="text-slate-600 dark:text-slate-400 font-sans">Bajas Históricas Acumuladas:</span>
                <span className="text-slate-900 dark:text-slate-200 font-bold font-mono">
                  {kpis?.total_bajas_historicas || 0} activos liquidados
                </span>
              </div>
            </div>

            <button
              onClick={() => onNavigate("depreciacion")}
              className="w-full py-2 rounded bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold border border-slate-300 dark:border-slate-700 transition flex items-center justify-center gap-2 shadow-xs"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Gestionar Cierres & Descargar PLE 7.1</span>
            </button>
          </div>

          <div className="rounded-lg border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-xs space-y-3.5">
            <div className="flex items-center justify-between pb-2.5 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                <h3 className="text-xs font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider font-mono">
                  Control & Auditoría Preventiva
                </h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 dark:bg-amber-500/10 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-500/20">
                {(alertasVU?.total_alertas || 0) + (alertasHuerfanos?.total_huerfanos || 0)} Alertas
              </span>
            </div>

            <div className="space-y-2 text-xs">
              {/* Alerta Vida Útil */}
              <div className="p-2.5 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800/70 flex items-start gap-2.5">
                <Clock className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-800 dark:text-slate-200">Vida Útil por Vencer</span>
                    <span className="font-mono font-bold text-slate-900 dark:text-white">
                      {alertasVU?.total_alertas || 0} activos
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                    Bienes a 30 o 60 días de alcanzar su valor residual.
                  </p>
                </div>
              </div>

              {/* Alerta Huérfanos */}
              <div className="p-2.5 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800/70 flex items-start gap-2.5">
                <UserX className="w-4 h-4 text-slate-600 dark:text-slate-400 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-800 dark:text-slate-200">Activos sin Custodio / Sede</span>
                    <span className="font-mono font-bold text-slate-900 dark:text-white">
                      {alertasHuerfanos?.total_huerfanos || 0} inconsistencias
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                    Bienes en uso sin responsable formal asignado.
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={() => onNavigate("alertas")}
              className="w-full py-2 rounded bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold border border-slate-300 dark:border-slate-700 transition flex items-center justify-center gap-1.5 shadow-xs"
            >
              <span>Auditar Todo en Módulo de Control</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
