"use client";

import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { extraerFactura, confirmarIngesta, fetchCatalogos } from "@/lib/api";
import {
  UploadCloud,
  FileText,
  Sparkles,
  CheckCircle,
  AlertCircle,
  Cpu,
  Layers,
  MapPin,
  User,
  Trash2,
  FilterX,
  Loader2,
  Building2,
  DollarSign,
  ArrowRight,
} from "lucide-react";

export default function IngestaView({ onNavigate }: { onNavigate: (tab: string) => void }) {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [extraccion, setExtraccion] = useState<any | null>(null);
  const [responsableId, setResponsableId] = useState<number | "">("");
  const [ubicacionId, setUbicacionId] = useState<number | "">("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [resultadoGuardado, setResultadoGuardado] = useState<any | null>(null);

  const { data: catalogos } = useQuery({
    queryKey: ["catalogos-maestros"],
    queryFn: fetchCatalogos,
  });

  const extractMutation = useMutation({
    mutationFn: async ({ file, mock }: { file: File; mock: boolean }) => {
      setErrorMsg(null);
      setResultadoGuardado(null);
      return extraerFactura(file, mock);
    },
    onSuccess: (data) => {
      setExtraccion(data);
      if (catalogos?.empleados?.length > 0 && !responsableId) {
        setResponsableId(catalogos.empleados[0].id);
      }
      if (catalogos?.ubicaciones?.length > 0 && !ubicacionId) {
        setUbicacionId(catalogos.ubicaciones[0].id);
      }
    },
    onError: (err: any) => {
      setErrorMsg(err.message || "Error extrayendo datos con IA");
    },
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!extraccion || !responsableId || !ubicacionId) {
        throw new Error("Debe seleccionar un custodio y una ubicación inicial.");
      }
      return confirmarIngesta({
        extraccion,
        id_responsable: Number(responsableId),
        id_ubicacion: Number(ubicacionId),
      });
    },
    onSuccess: (data) => {
      setResultadoGuardado(data);
      setExtraccion(null);
      setSelectedFile(null);
      queryClient.invalidateQueries({ queryKey: ["dashboard-kpis"] });
      queryClient.invalidateQueries({ queryKey: ["activos"] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || "Error al persistir activos en el patrimonio");
    },
  });

  const handleDemoLoad = () => {
    const demoPayload = {
      proveedor: {
        ruc: "20100128056",
        razon_social: "DELL PERU S.A.C.",
      },
      documento: {
        tipo_documento: "FACTURA ELECTRONICA",
        numero: "F001-00049281",
        fecha_emision: "2026-10-10",
        moneda: "PEN",
        monto_total: 20300.0,
      },
      activos: [
        {
          descripcion: "Servidor Dell PowerEdge R650xs Rack 1U Xeon Gold 32GB RAM",
          marca: "Dell",
          modelo: "PowerEdge R650xs",
          numero_serie: `SRV-${Math.floor(100000 + Math.random() * 900000)}`,
          costo_unitario: 8900.0,
          cantidad: 1,
          categoria_sugerida: "Equipos de Cómputo",
        },
        {
          descripcion: "Switch Administrable Cisco Catalyst 24 Puertos Gigabit",
          marca: "Cisco",
          modelo: "C9200L-24T-4G",
          numero_serie: `SW-${Math.floor(100000 + Math.random() * 900000)}`,
          costo_unitario: 2500.0,
          cantidad: 1,
          categoria_sugerida: "Equipos de Cómputo",
        },
      ],
      consumibles_descartados: [
        "Cable de Red UTP Cat6 305m (Bobina de instalación)",
        "Pack de 100 conectores RJ45 blindados",
        "Servicio de configuración e instalación en rack",
      ],
    };

    const file = new File([JSON.stringify(demoPayload)], "factura_servidores_demo.json", {
      type: "application/json",
    });
    setSelectedFile(file);
    setIsDemo(true);
    extractMutation.mutate({ file, mock: true });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setIsDemo(false);
      extractMutation.mutate({ file, mock: false });
    }
  };

  return (
    <div className="space-y-5 max-w-5xl">
      
      <div className="border-b border-slate-200 dark:border-slate-800 pb-3.5">
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-700 dark:text-blue-400" />
          Ingesta Inteligente de Comprobantes con IA
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Procesamiento automatizado de facturas con Gemini API. Discrimina bienes de activo fijo (NIC 16) y descarta consumibles o suministros.
        </p>
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 dark:bg-rose-950/40 dark:border-rose-800/60 dark:text-rose-200 rounded-lg text-xs flex items-center gap-2.5 shadow-xs">
          <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
          <span className="font-medium">{errorMsg}</span>
        </div>
      )}

      {!extraccion && !resultadoGuardado && (
        <div className="bg-white dark:bg-slate-900 border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-blue-600 dark:hover:border-blue-500 transition rounded-lg p-8 text-center relative overflow-hidden group shadow-xs">
          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.webp,.json"
            onChange={handleFileChange}
            disabled={extractMutation.isPending}
            className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10"
          />
          <div className="flex flex-col items-center justify-center space-y-3.5">
            <div className="p-3 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 rounded-lg group-hover:scale-105 transition duration-200">
              {extractMutation.isPending ? (
                <Loader2 className="w-8 h-8 animate-spin" />
              ) : (
                <UploadCloud className="w-8 h-8" />
              )}
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                {extractMutation.isPending
                  ? "Analizando comprobante con IA..."
                  : "Arrastre o seleccione el comprobante de pago aquí"}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Formatos compatibles: PDF, PNG, JPG, WEBP o JSON de prueba
              </p>
            </div>
            <div className="pt-1 z-20">
              <button
                type="button"
                onClick={handleDemoLoad}
                disabled={extractMutation.isPending}
                className="px-3.5 py-1.5 bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 text-xs font-semibold rounded shadow-xs transition flex items-center gap-1.5"
              >
                <Cpu className="w-3.5 h-3.5 text-blue-600" /> Probar con Factura Demo (Sin subir archivo)
              </button>
            </div>
          </div>
        </div>
      )}

      {extraccion && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 relative shadow-xs">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-3.5">
              <div>
                <span className="text-[11px] uppercase tracking-wider font-semibold font-mono text-blue-700 dark:text-blue-400">Proveedor Emisor</span>
                <h3 className="text-base font-bold text-slate-900 dark:text-white mt-0.5">{extraccion.proveedor.razon_social}</h3>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">RUC: {extraccion.proveedor.ruc}</span>
              </div>
              <div className="text-right">
                <span className="text-[11px] uppercase tracking-wider font-semibold font-mono text-slate-500 dark:text-slate-400">Comprobante</span>
                <h4 className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
                  {extraccion.documento.tipo_documento} {extraccion.documento.numero}
                </h4>
                <div className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                  Fecha: {extraccion.documento.fecha_emision} | Total: {extraccion.documento.moneda} {extraccion.documento.monto_total?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>

            <div className="mt-4">
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider font-mono mb-2.5 flex items-center gap-1.5">
                <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                Bienes Identificados como Activo Fijo ({extraccion.activos?.length || 0})
              </h4>
              <div className="overflow-x-auto rounded border border-slate-200 dark:border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-slate-950/80 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-800 uppercase tracking-wider">
                    <tr>
                      <th className="p-2.5">Descripción</th>
                      <th className="p-2.5">Marca / Modelo</th>
                      <th className="p-2.5">N° Serie</th>
                      <th className="p-2.5 text-right">Cant.</th>
                      <th className="p-2.5 text-right">Costo Unit.</th>
                      <th className="p-2.5">Categoría Asignada</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 bg-white dark:bg-slate-900/40">
                    {extraccion.activos?.map((act: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/30 transition">
                        <td className="p-2.5 font-medium text-slate-800 dark:text-slate-200 max-w-xs">{act.descripcion}</td>
                        <td className="p-2.5 text-slate-600 dark:text-slate-400">
                          {act.marca || "-"} {act.modelo ? `/ ${act.modelo}` : ""}
                        </td>
                        <td className="p-2.5 font-mono text-slate-900 dark:text-white font-bold">{act.numero_serie || "-"}</td>
                        <td className="p-2.5 text-right font-mono text-slate-800 dark:text-slate-200">{act.cantidad}</td>
                        <td className="p-2.5 text-right font-mono font-bold text-slate-900 dark:text-white">
                          {extraccion.documento.moneda} {act.costo_unitario?.toLocaleString("es-PE", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="p-2.5">
                          <span className="px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-800/40 text-[10px] font-semibold font-mono">
                            {act.categoria_sugerida}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {extraccion.consumibles_descartados?.length > 0 && (
              <div className="mt-3.5 p-3 bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 rounded text-xs flex items-start gap-2.5">
                <FilterX className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
                <div>
                  <span className="font-semibold text-slate-700 dark:text-slate-300">Suministros y Consumibles descartados por la IA:</span>
                  <p className="text-slate-500 dark:text-slate-400 mt-0.5 text-[11px]">
                    {extraccion.consumibles_descartados.join(" • ")}
                  </p>
                </div>
              </div>
            )}

            <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-blue-700 dark:text-blue-400" /> Custodio / Responsable Inicial *
                </label>
                <select
                  value={responsableId}
                  onChange={(e) => setResponsableId(Number(e.target.value))}
                  className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-1.5 px-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-600"
                >
                  {catalogos?.empleados?.map((emp: any) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.nombre} - {emp.cargo} (DNI: {emp.dni})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-blue-700 dark:text-blue-400" /> Ubicación Física / Sede *
                </label>
                <select
                  value={ubicacionId}
                  onChange={(e) => setUbicacionId(Number(e.target.value))}
                  className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded py-1.5 px-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-600"
                >
                  {catalogos?.ubicaciones?.map((ub: any) => (
                    <option key={ub.id} value={ub.id}>
                      {ub.nombre} ({ub.sede})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mt-5 flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100 dark:border-slate-800">
              <button
                type="button"
                onClick={() => {
                  setExtraccion(null);
                  setSelectedFile(null);
                }}
                disabled={saveMutation.isPending}
                className="px-3.5 py-1.5 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 text-xs font-semibold rounded shadow-xs"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => saveMutation.mutate()}
                disabled={saveMutation.isPending || !responsableId || !ubicacionId}
                className="px-4 py-1.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded shadow-xs transition flex items-center gap-1.5 disabled:opacity-50"
              >
                {saveMutation.isPending ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" /> Guardando en Patrimonio...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-3.5 h-3.5" /> Incorporar al Patrimonio
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {resultadoGuardado && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-6 text-center space-y-4 shadow-sm">
          <div className="w-12 h-12 bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-full flex items-center justify-center mx-auto border border-emerald-200 dark:border-emerald-500/30">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">¡Activos Incorporados Exitosamente!</h3>
            <p className="text-slate-500 dark:text-slate-400 text-xs mt-0.5">
              Se han generado {resultadoGuardado.total_activos_creados} registros en el padrón con sus códigos patrimoniales y asignación inicial.
            </p>
          </div>

          <div className="max-w-xl mx-auto bg-slate-50 dark:bg-slate-950/80 rounded border border-slate-200 dark:border-slate-800 divide-y divide-slate-200 dark:divide-slate-800 text-left text-xs">
            {resultadoGuardado.activos?.map((act: any) => (
              <div key={act.id_activo} className="p-3 flex justify-between items-center">
                <div>
                  <span className="font-bold text-blue-700 dark:text-blue-400 font-mono text-xs">{act.codigo}</span>
                  <p className="text-slate-800 dark:text-slate-200 text-xs mt-0.5">{act.descripcion}</p>
                </div>
                <div className="text-right">
                  <span className="font-bold font-mono text-slate-900 dark:text-white">S/ {Number(act.costo).toLocaleString("es-PE", { minimumFractionDigits: 2 })}</span>
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-mono">{act.vida_util_meses} meses</span>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-center gap-3 pt-2">
            <button
              onClick={() => setResultadoGuardado(null)}
              className="px-4 py-2 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 text-xs font-semibold rounded shadow-xs transition"
            >
              Ingestar Otra Factura
            </button>
            <button
              onClick={() => onNavigate("activos")}
              className="px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded shadow-xs transition"
            >
              Ver en el Padrón de Activos
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
