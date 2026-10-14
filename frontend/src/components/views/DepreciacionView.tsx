"use client";

import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cerrarMesDepreciacion, getPleDownloadUrl } from "@/lib/api";
import {
  Calculator,
  Lock,
  Download,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  FileSpreadsheet,
  ArrowRight,
  RefreshCw,
  Info,
} from "lucide-react";

export default function DepreciacionView() {
  const queryClient = useQueryClient();
  const [anio, setAnio] = useState<number>(new Date().getFullYear());
  const [mes, setMes] = useState<number>(new Date().getMonth() + 1);
  const [forzar, setForzar] = useState<boolean>(false);

  const [modalConfirmOpen, setModalConfirmOpen] = useState(false);
  const [resultadoCierre, setResultadoCierre] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const cierreMutation = useMutation({
    mutationFn: () => cerrarMesDepreciacion(anio, mes, forzar),
    onSuccess: (data) => {
      setResultadoCierre(data);
      setErrorMsg(null);
      setModalConfirmOpen(false);
      queryClient.invalidateQueries({ queryKey: ["dashboard-kpis"] });
      queryClient.invalidateQueries({ queryKey: ["activos"] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || "Error al cerrar el periodo contable");
      setModalConfirmOpen(false);
    },
  });

  return (
    <div className="space-y-5 max-w-5xl">
      
      <div className="border-b border-slate-200 dark:border-slate-800 pb-3.5">
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
          <Calculator className="w-5 h-5 text-blue-700 dark:text-blue-400" />
          Consola de Depreciación Mensual & SUNAT PLE 7.1
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Motor contable de devengo en línea recta, bloqueo secuencial de periodos y exportación oficial para SUNAT (Libro PLE 7.1).
        </p>
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 dark:bg-rose-950/40 dark:border-rose-800/60 dark:text-rose-200 rounded-lg text-xs flex items-center gap-2.5 shadow-xs">
          <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
          <span className="font-medium">{errorMsg}</span>
        </div>
      )}

      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-4 shadow-xs relative">
        <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider font-mono mb-3.5 flex items-center gap-2">
          <Lock className="w-3.5 h-3.5 text-blue-700 dark:text-blue-400" /> Parámetros del Periodo Contable
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 items-end">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Año Gravable</label>
            <input
              type="number"
              value={anio}
              onChange={(e) => setAnio(Number(e.target.value))}
              className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-2 px-3 text-xs text-slate-900 dark:text-white font-mono focus:outline-none focus:ring-1 focus:ring-blue-600"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Mes Contable</label>
            <select
              value={mes}
              onChange={(e) => setMes(Number(e.target.value))}
              className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-2 px-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              {[
                "1 - Enero",
                "2 - Febrero",
                "3 - Marzo",
                "4 - Abril",
                "5 - Mayo",
                "6 - Junio",
                "7 - Julio",
                "8 - Agosto",
                "9 - Setiembre",
                "10 - Octubre",
                "11 - Noviembre",
                "12 - Diciembre",
              ].map((m, idx) => (
                <option key={idx + 1} value={idx + 1}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          <div>
            <button
              type="button"
              onClick={() => setModalConfirmOpen(true)}
              disabled={cierreMutation.isPending}
              className="w-full py-2 px-4 bg-blue-700 hover:bg-blue-800 text-white font-semibold text-xs rounded shadow-xs transition flex items-center justify-center gap-2"
            >
              <Lock className="w-3.5 h-3.5" /> Ejecutar Cierre Mensual
            </button>
          </div>
        </div>

        <div className="mt-3.5 flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
          <input
            type="checkbox"
            id="chkForzar"
            checked={forzar}
            onChange={(e) => setForzar(e.target.checked)}
            className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="chkForzar" className="cursor-pointer text-[11px]">
            Forzar recálculo si el periodo contable ya se encuentra en estado CERRADO
          </label>
        </div>
      </div>

      {resultadoCierre && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-4 shadow-xs">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-3.5">
              <div>
                <span className="text-[11px] uppercase font-bold text-emerald-700 dark:text-emerald-400 font-mono">
                  Periodo Bloqueado y Cerrado
                </span>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-0.5">
                  Periodo {resultadoCierre.anio}-{String(resultadoCierre.mes).padStart(2, "0")}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Total procesados: <strong className="text-slate-800 dark:text-slate-200 font-mono">{resultadoCierre.activos_procesados}</strong> activos fijos
                </p>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase block font-semibold font-mono">Gasto del Mes</span>
                  <span className="text-lg font-bold font-mono text-slate-900 dark:text-white">
                    S/ {resultadoCierre.total_depreciacion_mes?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <a
                  href={getPleDownloadUrl(resultadoCierre.anio)}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3.5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold rounded shadow-xs transition flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" /> Descargar PLE 7.1 (.txt)
                </a>
              </div>
            </div>

            <div className="mt-4 overflow-x-auto rounded border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-950/80 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-800 uppercase tracking-wider">
                  <tr>
                    <th className="p-2.5">Código</th>
                    <th className="p-2.5">Descripción</th>
                    <th className="p-2.5 text-right">Cuota Devengada</th>
                    <th className="p-2.5 text-right">Deprec. Acumulada</th>
                    <th className="p-2.5 text-right">Valor Neto (VNL)</th>
                    <th className="p-2.5 text-center">Estado del Bien</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 bg-white dark:bg-slate-900/40">
                  {resultadoCierre.detalles?.map((d: any) => (
                    <tr key={d.id_activo} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/30 transition">
                      <td className="p-2.5 font-mono font-bold text-blue-700 dark:text-blue-400">{d.codigo}</td>
                      <td className="p-2.5 text-slate-800 dark:text-slate-200 max-w-xs truncate" title={d.descripcion}>{d.descripcion}</td>
                      <td className="p-2.5 text-right font-mono text-slate-900 dark:text-white font-bold">
                        S/ {d.cuota_mes?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="p-2.5 text-right font-mono text-slate-700 dark:text-slate-300 font-medium">
                        S/ {d.depreciacion_acum?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="p-2.5 text-right font-mono text-slate-900 dark:text-white font-bold">
                        S/ {d.valor_neto?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="p-2.5 text-center">
                        {d.totalmente_depreciado ? (
                          <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 text-[10px] font-mono font-semibold">
                            Totalmente Depreciado
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/20 text-[10px] font-mono font-semibold">
                            En Depreciación
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {modalConfirmOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg max-w-md w-full p-5 space-y-4 shadow-xl">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 rounded-lg flex items-center justify-center border border-amber-200 dark:border-amber-500/20">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">¿Confirmar Cierre de Depreciación Mensual?</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Periodo Contable {anio}-{String(mes).padStart(2, "0")}
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              Esta acción devengará la cuota mensual de depreciación lineal para todos los activos en uso según la NIC 16, calculará el gasto del periodo y bloqueará el mes para generar el libro oficial PLE 7.1 de SUNAT.
            </p>

            <div className="flex justify-end gap-2 pt-1 border-t border-slate-100 dark:border-slate-800">
              <button
                type="button"
                onClick={() => setModalConfirmOpen(false)}
                className="px-3.5 py-1.5 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs rounded border border-slate-300 dark:border-slate-700 font-semibold"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => cierreMutation.mutate()}
                disabled={cierreMutation.isPending}
                className="px-4 py-1.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded shadow-xs flex items-center gap-2"
              >
                {cierreMutation.isPending ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Calculando devengo...</span>
                  </>
                ) : (
                  <span>Confirmar & Bloquear Periodo</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
