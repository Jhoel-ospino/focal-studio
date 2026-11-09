import { useState } from 'react';
import { X, Cpu, Copy, Check, Terminal, AlertCircle } from 'lucide-react';

interface FlashModalProps {
  onClose: () => void;
  isDark: boolean;
}

export function FlashModal({ onClose, isDark }: FlashModalProps) {
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

  const copyToClipboard = (cmd: string) => {
    navigator.clipboard.writeText(cmd);
    setCopiedCmd(cmd);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const bgCard = isDark ? '#1A1D24' : '#FFFFFF';
  const borderSubtle = isDark ? '#2D333F' : '#E5E7EB';

  const commands = [
    {
      title: 'Compilar y Flashear con ESP-IDF (Recomendado)',
      cmd: 'idf.py build flash monitor',
    },
    {
      title: 'Flasheo rápido especificando puerto serie macOS',
      cmd: 'idf.py -p /dev/cu.usbserial-0001 flash',
    },
    {
      title: 'Flasheo con PlatformIO',
      cmd: 'pio run -t upload',
    },
  ];

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-6 select-none">
      <div
        className="w-full max-w-2xl rounded-2xl border shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150"
        style={{ backgroundColor: bgCard, borderColor: borderSubtle }}
      >
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between" style={{ borderColor: borderSubtle }}>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <Cpu size={18} />
            </div>
            <div>
              <div className="text-sm font-bold text-white">
                Flashear a ESP32-S3 (Pantalla TFT 3.5&quot; ILI9488)
              </div>
              <div className="text-[11px] text-gray-400">
                Instrucciones de compilación y carga directa al microcontrolador
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700/50 cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 text-xs">
          {/* Hardware Pinout Note */}
          <div className="p-3 rounded-xl border border-blue-500/30 bg-blue-500/10 text-blue-200 flex items-start gap-2.5">
            <AlertCircle size={16} className="text-blue-400 shrink-0 mt-0.5" />
            <div className="text-[11px] leading-relaxed">
              <strong className="text-white block mb-0.5">Hardware detectado: ESP32-S3 + ILI9488 (SPI 40MHz)</strong>
              Asegúrate de conectar el cable USB-C de la placa al puerto USB nativo / UART del computador con el display alimentado a 5V.
            </div>
          </div>

          {/* Flash Commands */}
          <div className="space-y-3">
            <div className="text-[10px] font-semibold tracking-wider uppercase text-gray-400">
              COMANDOS DE FLASHEO DIRECTO
            </div>

            {commands.map((item, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl border bg-black/40 space-y-1.5"
                style={{ borderColor: borderSubtle }}
              >
                <div className="text-[11px] font-medium text-gray-300">
                  {item.title}
                </div>
                <div className="flex items-center justify-between gap-2 bg-[#0A0C10] p-2 rounded-lg border border-zinc-800 font-mono text-[11px] text-emerald-400">
                  <div className="flex items-center gap-2 truncate">
                    <Terminal size={14} className="text-gray-500 shrink-0" />
                    <span className="truncate">{item.cmd}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(item.cmd)}
                    className="p-1 px-2 rounded bg-zinc-800 hover:bg-zinc-700 text-gray-300 hover:text-white text-[10px] flex items-center gap-1 cursor-pointer shrink-0 transition-colors"
                  >
                    {copiedCmd === item.cmd ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                    <span>{copiedCmd === item.cmd ? 'Copiado' : 'Copiar'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t bg-black/20 flex items-center justify-end" style={{ borderColor: borderSubtle }}>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs cursor-pointer"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
}
