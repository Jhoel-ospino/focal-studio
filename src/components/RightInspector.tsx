import { FocalElement, TextMode } from '../types/designer';
import { ACCENT_PALETTE, STANDARD_RADII } from '../data/tokens';
import { ICON_CATALOG, FocalIcon } from './FocalIcon';
import {
  AlertTriangle,
  Maximize2,
  Copy,
  Trash2,
  ArrowUpToLine,
  ArrowDownToLine,
  ChevronUp,
  ChevronDown,
  Type,
  Layout,
  Palette,
  Sparkles,
} from 'lucide-react';

interface RightInspectorProps {
  element: FocalElement | null;
  onUpdateElement: (id: string, updates: Partial<FocalElement>) => void;
  onDeleteElement: (id: string) => void;
  onDuplicateElement: (id: string) => void;
  onBringToFront: (id: string) => void;
  onSendToBack: (id: string) => void;
  onMoveUp: (id: string) => void;
  onMoveDown: (id: string) => void;
  isDark: boolean;
}

export function RightInspector({
  element,
  onUpdateElement,
  onDeleteElement,
  onDuplicateElement,
  onBringToFront,
  onSendToBack,
  onMoveUp,
  onMoveDown,
  isDark,
}: RightInspectorProps) {
  const bgCard = isDark ? '#1A1D24' : '#FFFFFF';
  const bgSubtle = isDark ? '#262A35' : '#F0F2F5';
  const borderSubtle = isDark ? '#2D333F' : '#E5E7EB';
  const textPrimary = isDark ? '#F9FAFB' : '#111827';
  const textSecondary = isDark ? '#9CA3AF' : '#4B5563';

  if (!element) {
    return (
      <aside
        className="w-72 h-full flex flex-col items-center justify-center p-6 text-center shrink-0 border-l transition-colors select-none z-20"
        style={{ backgroundColor: bgCard, borderColor: borderSubtle }}
      >
        <div className="w-12 h-12 rounded-2xl bg-blue-500/10 text-blue-400 flex items-center justify-center mb-3">
          <Layout size={24} />
        </div>
        <div className="text-xs font-semibold" style={{ color: textPrimary }}>
          Sin selección
        </div>
        <div className="text-[11px] mt-1 text-gray-400">
          Haz clic en cualquier componente del lienzo o agrega uno desde la biblioteca para inspeccionar y editar sus propiedades.
        </div>
      </aside>
    );
  }

  const isSmallHitbox = element.w < 44 || element.h < 44;

  const handleExpandHitbox = () => {
    const newW = Math.max(44, element.w);
    const newH = Math.max(44, element.h);
    // Keep within bounds
    const newX = Math.min(element.x, 480 - newW);
    const newY = Math.min(element.y, 320 - newH);
    onUpdateElement(element.id, {
      w: newW,
      h: newH,
      x: Math.max(0, newX),
      y: Math.max(0, newY),
    });
  };

  return (
    <aside
      className="w-72 h-full flex flex-col shrink-0 border-l overflow-y-auto transition-colors select-none z-20"
      style={{ backgroundColor: bgCard, borderColor: borderSubtle }}
    >
      {/* Header with Type & ID */}
      <div className="p-3 border-b flex items-center justify-between" style={{ borderColor: borderSubtle }}>
        <div>
          <div className="text-xs font-bold truncate" style={{ color: textPrimary }}>
            {element.name}
          </div>
          <div className="text-[10px] font-mono text-gray-400">
            ID: {element.id} • Tipo: {element.type}
          </div>
        </div>

        {/* Action icons */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            className="p-1 rounded text-gray-400 hover:text-white hover:bg-gray-700/50 cursor-pointer"
            title="Duplicar"
            onClick={() => onDuplicateElement(element.id)}
          >
            <Copy size={13} />
          </button>
          <button
            type="button"
            className="p-1 rounded text-gray-400 hover:text-red-400 hover:bg-red-500/10 cursor-pointer"
            title="Eliminar"
            onClick={() => onDeleteElement(element.id)}
          >
            <Trash2 size={13} />
          </button>
        </div>
      </div>

      <div className="p-3 space-y-4 text-xs">
        {/* ISO 9241-9 Touch Ergonomics Indicator Banner */}
        {isSmallHitbox && (
          <div className="p-2.5 rounded-xl border border-amber-500/40 bg-amber-500/10 text-amber-300 space-y-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-[11px]">
              <AlertTriangle size={14} className="text-amber-400 shrink-0" />
              <span>Incumple ISO 9241-9</span>
            </div>
            <p className="text-[10px] leading-tight text-amber-200/80">
              Área táctil menor a 44x44 px ({element.w}x{element.h}). Puede dificultar la pulsación con guantes o dedos en la máquina.
            </p>
            <button
              type="button"
              className="w-full mt-1 py-1.5 px-2 bg-amber-500 text-black font-semibold rounded-lg text-[10px] flex items-center justify-center gap-1 hover:bg-amber-400 cursor-pointer shadow-sm"
              onClick={handleExpandHitbox}
            >
              <Maximize2 size={12} />
              <span>Expandir Hitbox táctil (≥44px)</span>
            </button>
          </div>
        )}

        {/* Section 1: Dimensions & Position */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-[10px] font-semibold tracking-wider uppercase text-gray-400">
            <span>TRANSFORMACIÓN (PX)</span>
            <span className="font-mono text-gray-500">CANVAS 480x320</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-gray-400 block mb-0.5">X (Posición)</label>
              <input
                type="number"
                min={0}
                max={Math.max(0, 480 - element.w)}
                value={Math.round(element.x)}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  const safeVal = isNaN(val) ? 0 : val;
                  const clamped = Math.max(0, Math.min(Math.max(0, 480 - element.w), safeVal));
                  onUpdateElement(element.id, { x: clamped });
                }}
                className="w-full px-2 py-1 rounded-lg border bg-black/20 text-xs font-mono outline-none focus:border-blue-500"
                style={{ borderColor: borderSubtle, color: textPrimary }}
              />
            </div>

            <div>
              <label className="text-[10px] text-gray-400 block mb-0.5">Y (Posición)</label>
              <input
                type="number"
                min={0}
                max={Math.max(0, 320 - element.h)}
                value={Math.round(element.y)}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  const safeVal = isNaN(val) ? 0 : val;
                  const clamped = Math.max(0, Math.min(Math.max(0, 320 - element.h), safeVal));
                  onUpdateElement(element.id, { y: clamped });
                }}
                className="w-full px-2 py-1 rounded-lg border bg-black/20 text-xs font-mono outline-none focus:border-blue-500"
                style={{ borderColor: borderSubtle, color: textPrimary }}
              />
            </div>

            <div>
              <label className="text-[10px] text-gray-400 block mb-0.5">W (Ancho)</label>
              <input
                type="number"
                min={16}
                max={Math.max(16, 480 - element.x)}
                value={Math.round(element.w)}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  const safeVal = isNaN(val) ? 16 : val;
                  const maxAllowed = Math.max(16, 480 - element.x);
                  const clamped = Math.max(16, Math.min(maxAllowed, safeVal));
                  onUpdateElement(element.id, { w: clamped });
                }}
                className="w-full px-2 py-1 rounded-lg border bg-black/20 text-xs font-mono outline-none focus:border-blue-500"
                style={{ borderColor: borderSubtle, color: textPrimary }}
              />
            </div>

            <div>
              <label className="text-[10px] text-gray-400 block mb-0.5">H (Alto)</label>
              <input
                type="number"
                min={16}
                max={Math.max(16, 320 - element.y)}
                value={Math.round(element.h)}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  const safeVal = isNaN(val) ? 16 : val;
                  const maxAllowed = Math.max(16, 320 - element.y);
                  const clamped = Math.max(16, Math.min(maxAllowed, safeVal));
                  onUpdateElement(element.id, { h: clamped });
                }}
                className="w-full px-2 py-1 rounded-lg border bg-black/20 text-xs font-mono outline-none focus:border-blue-500"
                style={{ borderColor: borderSubtle, color: textPrimary }}
              />
            </div>
          </div>
        </div>

        {/* Section 2: Text & Typography */}
        <div className="space-y-2 pt-2 border-t" style={{ borderColor: borderSubtle }}>
          <div className="text-[10px] font-semibold tracking-wider uppercase text-gray-400">
            TEXTO Y TIPOGRAFÍA
          </div>

          <div>
            <label className="text-[10px] text-gray-400 block mb-0.5">Texto Principal</label>
            <input
              type="text"
              value={element.text}
              onChange={(e) => onUpdateElement(element.id, { text: e.target.value })}
              className="w-full px-2.5 py-1.5 rounded-lg border bg-black/20 text-xs outline-none focus:border-blue-500"
              style={{ borderColor: borderSubtle, color: textPrimary }}
            />
          </div>

          {element.subtext !== undefined && (
            <div>
              <label className="text-[10px] text-gray-400 block mb-0.5">Subtexto / Detalle</label>
              <input
                type="text"
                value={element.subtext}
                onChange={(e) => onUpdateElement(element.id, { subtext: e.target.value })}
                className="w-full px-2.5 py-1.5 rounded-lg border bg-black/20 text-xs outline-none focus:border-blue-500"
                style={{ borderColor: borderSubtle, color: textPrimary }}
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-gray-400 block mb-0.5">Modo de Texto</label>
              <select
                value={element.textMode}
                onChange={(e) =>
                  onUpdateElement(element.id, { textMode: e.target.value as TextMode })
                }
                className="w-full px-2 py-1 rounded-lg border bg-black/20 text-xs outline-none"
                style={{ borderColor: borderSubtle, color: textPrimary }}
              >
                <option value="ellipsis">Ellipsis (&apos;...&apos; Fijo)</option>
                <option value="multiline">Multilínea</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-gray-400 block mb-0.5">Tamaño Fuente</label>
              <select
                value={element.fontSize}
                onChange={(e) =>
                  onUpdateElement(element.id, { fontSize: Number(e.target.value) })
                }
                className="w-full px-2 py-1 rounded-lg border bg-black/20 text-xs outline-none"
                style={{ borderColor: borderSubtle, color: textPrimary }}
              >
                {[10, 11, 12, 13, 14, 16, 18, 20, 24].map((size) => (
                  <option key={size} value={size}>
                    {size} px
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Section 3: Curvature & Squircle Radius */}
        <div className="space-y-2 pt-2 border-t" style={{ borderColor: borderSubtle }}>
          <div className="flex items-center justify-between text-[10px] font-semibold tracking-wider uppercase text-gray-400">
            <span>RADIO DE ESQUINAS (SQUIRCLE)</span>
            <span className="font-mono text-blue-400">{element.radius >= 999 ? 'Píldora' : `${element.radius}px`}</span>
          </div>

          <div className="grid grid-cols-4 gap-1">
            {STANDARD_RADII.slice(0, 4).map((r) => (
              <button
                key={r.value}
                type="button"
                className={`py-1 text-[10px] rounded-lg border cursor-pointer ${
                  element.radius === r.value ? 'bg-blue-500 text-white font-semibold' : 'hover:border-gray-500'
                }`}
                style={{
                  backgroundColor: element.radius === r.value ? '#3B82F6' : bgSubtle,
                  borderColor: element.radius === r.value ? '#3B82F6' : borderSubtle,
                  color: element.radius === r.value ? '#FFFFFF' : textPrimary,
                }}
                onClick={() => onUpdateElement(element.id, { radius: r.value })}
              >
                {r.value}px
              </button>
            ))}
          </div>

          <div className="grid grid-cols-3 gap-1">
            {STANDARD_RADII.slice(4).map((r) => (
              <button
                key={r.value}
                type="button"
                className={`py-1 text-[10px] rounded-lg border cursor-pointer ${
                  element.radius === r.value ? 'bg-blue-500 text-white font-semibold' : 'hover:border-gray-500'
                }`}
                style={{
                  backgroundColor: element.radius === r.value ? '#3B82F6' : bgSubtle,
                  borderColor: element.radius === r.value ? '#3B82F6' : borderSubtle,
                  color: element.radius === r.value ? '#FFFFFF' : textPrimary,
                }}
                onClick={() => onUpdateElement(element.id, { radius: r.value })}
              >
                {r.value === 999 ? 'Pill (999)' : `${r.value}px`}
              </button>
            ))}
          </div>
        </div>

        {/* Section 4: Accent Color Tokens */}
        <div className="space-y-2 pt-2 border-t" style={{ borderColor: borderSubtle }}>
          <div className="text-[10px] font-semibold tracking-wider uppercase text-gray-400">
            COLOR DE ÉNFASIS (TOKENS FOCAL)
          </div>

          <div className="grid grid-cols-5 gap-1.5">
            {ACCENT_PALETTE.map((acc) => {
              const isSelected = element.accentColor.toLowerCase() === acc.hex.toLowerCase();
              return (
                <button
                  key={acc.hex}
                  type="button"
                  className={`h-7 rounded-lg border transition-all cursor-pointer flex items-center justify-center ${
                    isSelected ? 'ring-2 ring-white scale-105' : 'hover:scale-105'
                  }`}
                  style={{
                    backgroundColor: acc.hex,
                    borderColor: isSelected ? '#FFFFFF' : 'transparent',
                  }}
                  onClick={() => onUpdateElement(element.id, { accentColor: acc.hex })}
                  title={`${acc.name} (${acc.hex}) - ${acc.desc}`}
                >
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-black" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Section 5: Icon selection */}
        <div className="space-y-2 pt-2 border-t" style={{ borderColor: borderSubtle }}>
          <div className="flex items-center justify-between text-[10px] font-semibold tracking-wider uppercase text-gray-400">
            <span>ICONO VECTORIAL</span>
            {element.icon && (
              <button
                type="button"
                className="text-red-400 hover:underline cursor-pointer"
                onClick={() => onUpdateElement(element.id, { icon: undefined })}
              >
                Quitar
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div
              className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
              style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            >
              <FocalIcon name={element.icon} size={20} color={element.accentColor} />
            </div>

            <select
              value={element.icon || ''}
              onChange={(e) => onUpdateElement(element.id, { icon: e.target.value || undefined })}
              className="flex-1 px-2.5 py-1.5 rounded-lg border bg-black/20 text-xs outline-none"
              style={{ borderColor: borderSubtle, color: textPrimary }}
            >
              <option value="">(Sin icono)</option>
              {ICON_CATALOG.map((ic) => (
                <option key={ic.id} value={ic.id}>
                  {ic.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Section 6: Layer / Z-Index management */}
        <div className="space-y-2 pt-2 border-t" style={{ borderColor: borderSubtle }}>
          <div className="flex items-center justify-between text-[10px] font-semibold tracking-wider uppercase text-gray-400">
            <span>CAPAS Y JERARQUÍA</span>
            <span className="font-mono text-gray-500">Z: {element.zIndex}</span>
          </div>

          <div className="grid grid-cols-4 gap-1">
            <button
              type="button"
              className="p-1.5 rounded-lg border text-gray-300 hover:text-white flex flex-col items-center gap-1 cursor-pointer"
              style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
              title="Traer al frente"
              onClick={() => onBringToFront(element.id)}
            >
              <ArrowUpToLine size={13} />
              <span className="text-[9px]">Frente</span>
            </button>

            <button
              type="button"
              className="p-1.5 rounded-lg border text-gray-300 hover:text-white flex flex-col items-center gap-1 cursor-pointer"
              style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
              title="Subir una capa"
              onClick={() => onMoveUp(element.id)}
            >
              <ChevronUp size={13} />
              <span className="text-[9px]">Subir</span>
            </button>

            <button
              type="button"
              className="p-1.5 rounded-lg border text-gray-300 hover:text-white flex flex-col items-center gap-1 cursor-pointer"
              style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
              title="Bajar una capa"
              onClick={() => onMoveDown(element.id)}
            >
              <ChevronDown size={13} />
              <span className="text-[9px]">Bajar</span>
            </button>

            <button
              type="button"
              className="p-1.5 rounded-lg border text-gray-300 hover:text-white flex flex-col items-center gap-1 cursor-pointer"
              style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
              title="Enviar al fondo"
              onClick={() => onSendToBack(element.id)}
            >
              <ArrowDownToLine size={13} />
              <span className="text-[9px]">Fondo</span>
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
