import {
  Save,
  FileCode,
  PlayCircle,
  Cpu,
  RotateCcw,
  RotateCw,
  Sun,
  Moon,
  Magnet,
  ZoomIn,
} from 'lucide-react';
import { CanvasZoom, SnapGridSize } from '../types/designer';

interface TopBarProps {
  screenName: string;
  isDark: boolean;
  onToggleTheme: () => void;
  zoom: CanvasZoom;
  onChangeZoom: (zoom: CanvasZoom) => void;
  snapGrid: SnapGridSize;
  onChangeSnapGrid: (snap: SnapGridSize) => void;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  onSaveLayout: () => void;
  onExportC: () => void;
  onSimulate: () => void;
  onFlashESP32: () => void;
}

export function TopBar({
  screenName,
  isDark,
  onToggleTheme,
  zoom,
  onChangeZoom,
  snapGrid,
  onChangeSnapGrid,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  onSaveLayout,
  onExportC,
  onSimulate,
  onFlashESP32,
}: TopBarProps) {
  const bgCard = isDark ? '#1A1D24' : '#FFFFFF';
  const bgSubtle = isDark ? '#262A35' : '#F0F2F5';
  const borderSubtle = isDark ? '#2D333F' : '#E5E7EB';
  const textPrimary = isDark ? '#F9FAFB' : '#111827';
  const textSecondary = isDark ? '#9CA3AF' : '#4B5563';

  return (
    <header
      className="h-14 w-full flex items-center justify-between px-4 border-b shrink-0 select-none z-30 transition-colors"
      style={{
        backgroundColor: bgCard,
        borderColor: borderSubtle,
      }}
    >
      {/* Brand & Active Screen Info */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-blue-400 text-white flex items-center justify-center font-bold text-sm shadow-md shadow-blue-500/20">
            F
          </div>
          <div>
            <div className="text-xs font-bold tracking-wider flex items-center gap-1.5" style={{ color: textPrimary }}>
              <span>FOCAL STUDIO DESIGNER</span>
              <span className="px-1.5 py-0.2 text-[9px] rounded font-mono bg-blue-500/15 text-blue-400 font-semibold border border-blue-500/30">
                480×320 (3:2)
              </span>
            </div>
            <div className="text-[10px] text-gray-400">
              Pantalla: <span className="font-semibold text-blue-400">{screenName}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Middle Tools: Undo/Redo, Zoom, Snap, Theme */}
      <div className="flex items-center gap-2">
        {/* Undo / Redo */}
        <div className="flex items-center rounded-xl p-0.5 border" style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}>
          <button
            type="button"
            disabled={!canUndo}
            onClick={onUndo}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white disabled:opacity-30 disabled:hover:text-gray-400 cursor-pointer"
            title="Deshacer (Ctrl+Z / Cmd+Z)"
          >
            <RotateCcw size={14} />
          </button>
          <button
            type="button"
            disabled={!canRedo}
            onClick={onRedo}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white disabled:opacity-30 disabled:hover:text-gray-400 cursor-pointer"
            title="Rehacer (Ctrl+Y / Cmd+Shift+Z)"
          >
            <RotateCw size={14} />
          </button>
        </div>

        {/* Zoom Selector */}
        <div className="flex items-center rounded-xl px-2 py-1 border text-xs gap-1.5" style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}>
          <ZoomIn size={13} className="text-gray-400" />
          <select
            value={zoom}
            onChange={(e) => {
              const val = e.target.value;
              onChangeZoom(val === 'fit' ? 'fit' : (Number(val) as CanvasZoom));
            }}
            className="bg-transparent outline-none text-xs font-mono cursor-pointer"
            style={{ color: textPrimary }}
          >
            <option value="fit">Ajustar (Fit)</option>
            <option value={1.0}>1.0x (100% 480×320)</option>
            <option value={1.5}>1.5x (150%)</option>
            <option value={2.0}>2.0x (200%)</option>
          </select>
        </div>

        {/* Snap Grid Toggle */}
        <div className="flex items-center rounded-xl px-2 py-1 border text-xs gap-1.5" style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}>
          <Magnet size={13} className={snapGrid > 0 ? 'text-blue-400' : 'text-gray-400'} />
          <select
            value={snapGrid}
            onChange={(e) => onChangeSnapGrid(Number(e.target.value) as SnapGridSize)}
            className="bg-transparent outline-none text-xs font-mono cursor-pointer"
            style={{ color: textPrimary }}
          >
            <option value={0}>Snap: Apagado</option>
            <option value={4}>Snap: 4px</option>
            <option value={8}>Snap: 8px (Token)</option>
          </select>
        </div>

        {/* Dark / Light Mode Toggle */}
        <button
          type="button"
          onClick={onToggleTheme}
          className="p-1.5 rounded-xl border text-gray-300 hover:text-white transition-all cursor-pointer"
          style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
          title={isDark ? 'Cambiar a Modo Claro' : 'Cambiar a Modo Oscuro'}
        >
          {isDark ? <Sun size={15} className="text-amber-400" /> : <Moon size={15} className="text-blue-500" />}
        </button>
      </div>

      {/* Right Primary Actions */}
      <div className="flex items-center gap-2">
        {/* Guardar Layout */}
        <button
          type="button"
          onClick={onSaveLayout}
          className="px-3 py-1.5 rounded-xl border flex items-center gap-1.5 text-xs font-semibold transition-all hover:border-blue-400 cursor-pointer"
          style={{ backgroundColor: bgSubtle, borderColor: borderSubtle, color: textPrimary }}
          title="Guardar layout en screens_layout.json"
        >
          <Save size={14} className="text-blue-400" />
          <span>Guardar Layout</span>
        </button>

        {/* Exportar a C */}
        <button
          type="button"
          onClick={onExportC}
          className="px-3 py-1.5 rounded-xl border flex items-center gap-1.5 text-xs font-semibold transition-all hover:border-emerald-400 cursor-pointer"
          style={{ backgroundColor: bgSubtle, borderColor: borderSubtle, color: textPrimary }}
          title="Generar código C para LVGL"
        >
          <FileCode size={14} className="text-emerald-400" />
          <span>Exportar a C</span>
        </button>

        {/* Simular en focal_sim */}
        <button
          type="button"
          onClick={onSimulate}
          className="px-3 py-1.5 rounded-xl bg-blue-500 hover:bg-blue-600 text-white flex items-center gap-1.5 text-xs font-semibold transition-all shadow-sm cursor-pointer"
          title="Previsualizar en simulador interactivo"
        >
          <PlayCircle size={14} />
          <span>Simular en focal_sim</span>
        </button>

        {/* Flashear ESP32 */}
        <button
          type="button"
          onClick={onFlashESP32}
          className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1.5 text-xs font-semibold transition-all shadow-sm cursor-pointer"
          title="Flashear a pantalla física ESP32-S3"
        >
          <Cpu size={14} />
          <span>Flashear ESP32</span>
        </button>
      </div>
    </header>
  );
}
