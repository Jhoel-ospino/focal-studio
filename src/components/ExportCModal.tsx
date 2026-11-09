import { useState } from 'react';
import { ScreenLayout } from '../types/designer';
import { exportScreenToC } from '../utils/c_exporter';
import { X, Copy, Check, Download, FileCode } from 'lucide-react';

interface ExportCModalProps {
  screen: ScreenLayout;
  onClose: () => void;
  isDark: boolean;
}

export function ExportCModal({ screen, onClose, isDark }: ExportCModalProps) {
  const [copied, setCopied] = useState(false);
  const cCode = exportScreenToC(screen);

  const handleCopy = () => {
    navigator.clipboard.writeText(cCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([cCode], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `focal_ui_${screen.id}.c`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const bgCard = isDark ? '#1A1D24' : '#FFFFFF';
  const borderSubtle = isDark ? '#2D333F' : '#E5E7EB';

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6 select-none">
      <div
        className="w-full max-w-3xl max-h-[85vh] rounded-2xl border shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150"
        style={{ backgroundColor: bgCard, borderColor: borderSubtle }}
      >
        {/* Modal Header */}
        <div className="p-4 border-b flex items-center justify-between" style={{ borderColor: borderSubtle }}>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <FileCode size={18} />
            </div>
            <div>
              <div className="text-sm font-bold text-white">
                Exportar Pantalla a C / LVGL
              </div>
              <div className="text-[11px] text-gray-400">
                Archivo: <span className="font-mono text-emerald-400">focal_ui_{screen.id}.c</span> • {screen.elements.length} elementos
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className="px-3 py-1.5 rounded-lg bg-blue-500 hover:bg-blue-600 text-white text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-sm"
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
              <span>{copied ? '¡Copiado!' : 'Copiar Código'}</span>
            </button>

            <button
              type="button"
              onClick={handleDownload}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-sm"
            >
              <Download size={14} />
              <span>Descargar .c</span>
            </button>

            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700/50 cursor-pointer"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Code Content View */}
        <div className="flex-1 overflow-auto p-4 bg-[#0A0C10] font-mono text-xs text-gray-300 leading-relaxed">
          <pre className="select-text">{cCode}</pre>
        </div>

        {/* Modal Footer */}
        <div className="p-3 border-t bg-black/20 flex items-center justify-between text-[11px] text-gray-400" style={{ borderColor: borderSubtle }}>
          <span>Compatible con LVGL v8 / v9 y LovyanGFX en firmware ESP32-S3</span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg border border-gray-600 text-gray-300 hover:text-white text-xs cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}
