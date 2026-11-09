import { useState } from 'react';
import { ScreenLayout, FocalElement } from '../types/designer';
import { RenderElement } from './RenderElement';
import { X, Play, RotateCcw, Monitor, ExternalLink } from 'lucide-react';

interface SimulateModalProps {
  screen: ScreenLayout;
  onClose: () => void;
  isDark: boolean;
}

export function SimulateModal({ screen, onClose, isDark }: SimulateModalProps) {
  // Local state for interactive test simulation
  const [elementsState, setElementsState] = useState<FocalElement[]>(screen.elements);
  const [lastAction, setLastAction] = useState<string>('Simulador iniciado en 480x320 px');

  const handleInteract = (el: FocalElement) => {
    if (el.type === 'switch') {
      const newVal = !el.value;
      setElementsState((prev) =>
        prev.map((item) => (item.id === el.id ? { ...item, value: newVal } : item))
      );
      setLastAction(`Switch "${el.text}" alternado a ${newVal ? 'ON' : 'OFF'}`);
    } else if (el.type === 'slider') {
      const current = typeof el.value === 'number' ? el.value : 50;
      const min = el.minValue ?? 0;
      const max = el.maxValue ?? 100;
      const step = (max - min) / 10;
      let next = current + step;
      if (next > max) next = min;
      setElementsState((prev) =>
        prev.map((item) => (item.id === el.id ? { ...item, value: Math.round(next) } : item))
      );
      setLastAction(`Slider "${el.text}" ajustado a ${Math.round(next)} ${el.unit || ''}`);
    } else {
      setLastAction(`Botón pulsado: "${el.text}" [${el.type}]`);
    }
  };

  const bgCard = isDark ? '#1A1D24' : '#FFFFFF';
  const borderSubtle = isDark ? '#2D333F' : '#E5E7EB';

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-6 select-none">
      <div
        className="w-full max-w-4xl rounded-2xl border shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150"
        style={{ backgroundColor: bgCard, borderColor: borderSubtle }}
      >
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between" style={{ borderColor: borderSubtle }}>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
              <Monitor size={18} />
            </div>
            <div>
              <div className="text-sm font-bold text-white">
                Simulación Interactiva TFT 3.5&quot;
              </div>
              <div className="text-[11px] text-gray-400">
                Pantalla: <span className="text-blue-400 font-semibold">{screen.name}</span> • Interacción táctil en vivo
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setElementsState(screen.elements);
                setLastAction('Valores reiniciados a los predeterminados');
              }}
              className="px-2.5 py-1.5 rounded-lg border border-gray-600 text-gray-300 hover:text-white text-xs flex items-center gap-1 cursor-pointer"
            >
              <RotateCcw size={13} />
              <span>Reiniciar</span>
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

        {/* Simulator Body */}
        <div className="p-6 bg-[#0A0C10] flex flex-col items-center justify-center">
          {/* Simulated 480x320 TFT Frame */}
          <div
            className="relative rounded-lg overflow-hidden border-4 border-zinc-700 shadow-2xl transition-colors"
            style={{
              width: 480,
              height: 320,
              backgroundColor: isDark ? '#0F1115' : '#F5F6F8',
            }}
          >
            {elementsState
              .slice()
              .sort((a, b) => a.zIndex - b.zIndex)
              .map((el) => (
                <div
                  key={el.id}
                  className="absolute cursor-pointer active:scale-95 transition-transform"
                  style={{
                    left: el.x,
                    top: el.y,
                    width: el.w,
                    height: el.h,
                    zIndex: el.zIndex,
                  }}
                  onClick={() => handleInteract(el)}
                >
                  <RenderElement element={el} isSelected={false} isDark={isDark} />
                </div>
              ))}
          </div>

          {/* Action Console & Live Log */}
          <div className="w-[480px] mt-4 p-2.5 rounded-xl border border-zinc-800 bg-zinc-950/80 font-mono text-[11px] text-emerald-400 flex items-center justify-between">
            <div className="flex items-center gap-2 truncate">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="truncate">{lastAction}</span>
            </div>
            <span className="text-[10px] text-zinc-500 font-sans shrink-0">LVGL Touch Driver OK</span>
          </div>
        </div>

        {/* Footer with native command */}
        <div className="p-3 border-t bg-black/20 flex items-center justify-between text-xs text-gray-400" style={{ borderColor: borderSubtle }}>
          <div className="flex items-center gap-2">
            <span>Para simulación nativa SDL2 ejecute en terminal:</span>
            <code className="px-2 py-0.5 rounded bg-zinc-800 font-mono text-zinc-200 text-[11px]">
              ./run_simulator.sh
            </code>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-blue-500 hover:bg-blue-600 text-white font-semibold text-xs cursor-pointer"
          >
            Aceptar
          </button>
        </div>
      </div>
    </div>
  );
}
