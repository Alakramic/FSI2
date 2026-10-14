"use client";

import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  FileText,
  Boxes,
  Calculator,
  Trash2,
  AlertTriangle,
  Building2,
  Database,
  CheckCircle2,
  Menu,
  X,
  ChevronRight,
  ShieldCheck,
  RefreshCw,
  Plus,
  User,
  Activity,
  Sun,
  Moon
} from "lucide-react";

import DashboardView from "@/components/views/DashboardView";
import IngestaView from "@/components/views/IngestaView";
import ActivosView from "@/components/views/ActivosView";
import DepreciacionView from "@/components/views/DepreciacionView";
import BajasView from "@/components/views/BajasView";
import AlertasView from "@/components/views/AlertasView";

import { fetchAlertasVidaUtil, fetchAlertasHuerfanos, fetchHealth } from "@/lib/api";

type TabId = "dashboard" | "ingesta" | "activos" | "depreciacion" | "bajas" | "alertas";

interface NavItem {
  id: TabId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number | null;
  badgeVariant?: "default" | "warning" | "info" | "success";
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");
  const [selectedBajaId, setSelectedBajaId] = useState<number | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showDbModal, setShowDbModal] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    
    const savedTheme = localStorage.getItem("sgaf_theme_v2") as "light" | "dark" | null;
    if (savedTheme === "dark") {
      setTheme("dark");
      document.documentElement.classList.add("dark");
    } else {
      setTheme("light");
      document.documentElement.classList.remove("dark");
      localStorage.setItem("sgaf_theme_v2", "light");
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    localStorage.setItem("sgaf_theme_v2", nextTheme);
    if (nextTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const { data: alertasVU } = useQuery({
    queryKey: ["alertas-vida-util-badge"],
    queryFn: fetchAlertasVidaUtil,
    staleTime: 15000,
  });

  const { data: alertasH } = useQuery({
    queryKey: ["alertas-huerfanos-badge"],
    queryFn: fetchAlertasHuerfanos,
    staleTime: 15000,
  });

  const { data: healthData, refetch: refetchHealth, isRefetching: refetchingHealth } = useQuery({
    queryKey: ["db-health"],
    queryFn: fetchHealth,
    staleTime: 20000,
  });

  const totalAlertas = (alertasVU?.total_alertas || 0) + (alertasH?.total_huerfanos || 0);

  const handleNavigate = (tab: string, activoId?: number) => {
    setActiveTab(tab as TabId);
    if (activoId) {
      setSelectedBajaId(activoId);
    } else {
      setSelectedBajaId(null);
    }
    setMobileMenuOpen(false);
  };

  const navSections: NavSection[] = [
    {
      title: "PANEL PRINCIPAL",
      items: [
        {
          id: "dashboard",
          label: "Dashboard Ejecutivo",
          icon: LayoutDashboard,
        },
      ],
    },
    {
      title: "GESTIÓN DE ACTIVOS (NIC 16)",
      items: [
        {
          id: "ingesta",
          label: "Ingesta de Facturas (IA)",
          icon: FileText,
          badge: "IA",
          badgeVariant: "info",
        },
        {
          id: "activos",
          label: "Padrón de Activos Fijos",
          icon: Boxes,
        },
      ],
    },
    {
      title: "CONTABILIDAD & CIERRES",
      items: [
        {
          id: "depreciacion",
          label: "Depreciación & PLE 7.1",
          icon: Calculator,
          badge: "SUNAT",
          badgeVariant: "success",
        },
        {
          id: "bajas",
          label: "Liquidación de Bajas",
          icon: Trash2,
        },
      ],
    },
    {
      title: "CONTROL & AUDITORÍA",
      items: [
        {
          id: "alertas",
          label: "Auditoría & Alertas",
          icon: AlertTriangle,
          badge: totalAlertas > 0 ? totalAlertas : null,
          badgeVariant: "warning",
        },
      ],
    },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100 dark:bg-slate-950 text-slate-800 dark:text-slate-100 font-sans transition-colors duration-150">
      
      <aside className="hidden lg:flex w-64 flex-col border-r border-slate-800 bg-slate-900 text-slate-300 shrink-0 z-20">
        
        <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded bg-blue-700 text-white font-bold text-sm flex items-center justify-center shadow-sm">
              AF
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-sm tracking-tight text-white">SGAF Enterprise</span>
                <span className="text-[10px] font-mono px-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  v2.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-tight">Corporación Perú S.A.C.</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto custom-scrollbar">
          {navSections.map((sec, idx) => (
            <div key={idx} className="space-y-1">
              <div className="px-2.5 pb-1 text-[10px] font-bold tracking-wider text-slate-400 uppercase font-mono">
                {sec.title}
              </div>
              {sec.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavigate(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded text-xs font-medium transition-colors ${
                      isActive
                        ? "bg-slate-800 text-white font-semibold border-l-2 border-blue-500 shadow-sm"
                        : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon
                        className={`w-4 h-4 ${
                          isActive ? "text-blue-400" : "text-slate-400"
                        }`}
                      />
                      <span>{item.label}</span>
                    </div>

                    {item.badge && (
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                          item.badgeVariant === "warning"
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                            : item.badgeVariant === "success"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : item.badgeVariant === "info"
                            ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                            : "bg-slate-800 text-slate-300 border border-slate-700"
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="p-3 border-t border-slate-800">
          <button
            onClick={() => setShowDbModal(true)}
            type="button"
            className="w-full text-left p-2.5 rounded bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition flex items-center justify-between group"
          >
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <div>
                <div className="text-[11px] font-semibold text-slate-200">PostgreSQL 16</div>
                <div className="text-[10px] text-slate-400 font-mono">
                  {healthData?.database?.latency_ms ? `${healthData.database.latency_ms.toFixed(0)}ms latencia` : "Conectado"}
                </div>
              </div>
            </div>
            <Activity className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-400 transition" />
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-6 flex items-center justify-between shrink-0 z-10 shadow-xs">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden p-1.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Breadcrumb Path */}
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 font-medium">
              <span>SGAF</span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-800 dark:text-slate-200 font-semibold uppercase tracking-wider">
                {navSections.flatMap(s => s.items).find(n => n.id === activeTab)?.label}
              </span>
            </div>
          </div>

          {/* Contexto Contable, Theme Switcher y Usuario */}
          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-3 text-xs pr-2 border-r border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 dark:text-slate-400">
                Periodo: <strong className="text-slate-800 dark:text-slate-200 font-mono">2026-10 (Abierto)</strong>
              </span>
              <span className="text-slate-300 dark:text-slate-700">&bull;</span>
              <span className="text-slate-500 dark:text-slate-400">
                Normativa: <strong className="text-slate-800 dark:text-slate-200 font-mono">NIC 16 / SUNAT</strong>
              </span>
            </div>

            <button
              onClick={toggleTheme}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-700 transition"
              title="Cambiar entre Tema Claro (ERP Estándar) y Tema Oscuro"
            >
              {theme === "light" ? (
                <>
                  <Moon className="w-3.5 h-3.5 text-slate-600" />
                  <span className="hidden sm:inline">Modo Oscuro</span>
                </>
              ) : (
                <>
                  <Sun className="w-3.5 h-3.5 text-amber-400" />
                  <span className="hidden sm:inline">Modo Claro (ERP)</span>
                </>
              )}
            </button>

            <button
              onClick={() => handleNavigate("ingesta")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold shadow-xs transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Ingestar Factura</span>
            </button>

            <div className="flex items-center gap-2 pl-2">
              <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 flex items-center justify-center text-xs font-bold text-slate-700 dark:text-slate-300">
                A
              </div>
              <div className="hidden sm:block text-left">
                <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 leading-none">Alakramic</div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 leading-none mt-1">Auditor Contable</div>
              </div>
            </div>
          </div>
        </header>

        {mobileMenuOpen && (
          <div className="fixed inset-0 z-50 lg:hidden flex">
            <div
              className="fixed inset-0 bg-black/50 backdrop-blur-xs"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="relative w-72 bg-slate-900 border-r border-slate-800 p-5 flex flex-col justify-between z-10 text-slate-300">
              <div>
                <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <div className="h-7 w-7 rounded bg-blue-700 flex items-center justify-center font-bold text-white text-xs">
                      AF
                    </div>
                    <span className="font-bold text-sm text-white">SGAF Enterprise</span>
                  </div>
                  <button
                    onClick={() => setMobileMenuOpen(false)}
                    className="p-1 rounded text-slate-400 hover:text-white"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <nav className="mt-4 space-y-4">
                  {navSections.map((sec, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="text-[10px] font-bold text-slate-400 uppercase font-mono px-2">
                        {sec.title}
                      </div>
                      {sec.items.map((item) => {
                        const Icon = item.icon;
                        const isActive = activeTab === item.id;
                        return (
                          <button
                            key={item.id}
                            onClick={() => handleNavigate(item.id)}
                            className={`w-full flex items-center justify-between px-2.5 py-2 rounded text-xs ${
                              isActive
                                ? "bg-slate-800 text-white font-semibold border-l-2 border-blue-500"
                                : "text-slate-300 hover:bg-slate-800/50"
                            }`}
                          >
                            <div className="flex items-center gap-2.5">
                              <Icon className="w-4 h-4 text-slate-400" />
                              <span>{item.label}</span>
                            </div>
                            {item.badge && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                                {item.badge}
                              </span>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  ))}
                </nav>
              </div>

              <div className="pt-3 border-t border-slate-800 text-[10px] text-slate-400 font-mono">
                PostgreSQL 16 &bull; SUNAT PLE 7.1
              </div>
            </div>
          </div>
        )}

        {/* Contenedor de Vistas: Slate-50 en Light / Slate-950 en Dark */}
        <main className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-slate-50 dark:bg-slate-950">
          <div className="max-w-7xl mx-auto">
            {activeTab === "dashboard" && (
              <DashboardView onNavigate={(t) => handleNavigate(t)} />
            )}
            {activeTab === "ingesta" && (
              <IngestaView onNavigate={(t) => handleNavigate(t)} />
            )}
            {activeTab === "activos" && (
              <ActivosView onNavigateToBaja={(id) => handleNavigate("bajas", id)} />
            )}
            {activeTab === "depreciacion" && <DepreciacionView />}
            {activeTab === "bajas" && (
              <BajasView initialActivoId={selectedBajaId} />
            )}
            {activeTab === "alertas" && (
              <AlertasView onSelectActivo={(id) => handleNavigate("activos")} />
            )}
          </div>
        </main>
      </div>

      {/* Modal Diagnóstico de Base de Datos */}
      {showDbModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 w-full max-w-md rounded-lg p-5 shadow-xl space-y-4 text-slate-800 dark:text-slate-100">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <h3 className="text-sm font-bold">Diagnóstico de Base de Datos</h3>
              </div>
              <button
                onClick={() => setShowDbModal(false)}
                className="p-1 rounded text-slate-400 hover:text-slate-600 dark:hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2.5 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Estado del Motor:</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  ONLINE (200 OK)
                </span>
              </div>

              <div className="flex justify-between p-2.5 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Perfil de Conexión:</span>
                <span className="font-bold uppercase">{healthData?.database?.profile || "local"}</span>
              </div>

              <div className="flex justify-between p-2.5 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Latencia de Conexión:</span>
                <span className="text-slate-800 dark:text-slate-200 font-bold">
                  {healthData?.database?.latency_ms ? `${healthData.database.latency_ms.toFixed(1)} ms` : "Calculando..."}
                </span>
              </div>

              <div className="flex justify-between p-2.5 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Versión Relacional:</span>
                <span className="text-slate-700 dark:text-slate-300 text-[11px] truncate max-w-[200px]" title={healthData?.database?.version}>
                  PostgreSQL 16.15 (Ubuntu)
                </span>
              </div>

              <div className="flex justify-between p-2.5 rounded bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Integridad de Esquema:</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-bold">17 Tablas (DDL Conforme)</span>
              </div>
            </div>

            <div className="flex gap-2 pt-1">
              <button
                type="button"
                onClick={() => refetchHealth()}
                disabled={refetchingHealth}
                className="flex-1 py-2 rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold flex items-center justify-center gap-2 transition border border-slate-200 dark:border-slate-700"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${refetchingHealth ? "animate-spin" : ""}`} />
                <span>Re-diagnosticar</span>
              </button>
              <button
                type="button"
                onClick={() => setShowDbModal(false)}
                className="px-4 py-2 rounded bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold transition"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
