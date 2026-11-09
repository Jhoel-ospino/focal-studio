import { useState } from 'react';
import { ScreenLayout, FocalElement } from '../types/designer';
import { ICON_CATALOG, FocalIcon } from './FocalIcon';
import {
  Layers,
  Component,
  Smile,
  Plus,
  Trash2,
  Copy,
  Search,
  Check,
  FolderOpen,
} from 'lucide-react';

interface LeftSidebarProps {
  screens: ScreenLayout[];
  activeScreenId: string;
  onSelectScreen: (id: string) => void;
  onAddScreen: (name: string) => void;
  onDuplicateScreen: (id: string) => void;
  onDeleteScreen: (id: string) => void;
  onAddElement: (element: Partial<FocalElement>) => void;
  selectedElement: FocalElement | null;
  onUpdateSelectedIcon: (iconName: string) => void;
  isDark: boolean;
}

type TabType = 'screens' | 'elements' | 'icons';

export function LeftSidebar({
  screens,
  activeScreenId,
  onSelectScreen,
  onAddScreen,
  onDuplicateScreen,
  onDeleteScreen,
  onAddElement,
  selectedElement,
  onUpdateSelectedIcon,
  isDark,
}: LeftSidebarProps) {
  const [activeTab, setActiveTab] = useState<TabType>('screens');
  const [iconSearch, setIconSearch] = useState('');
  const [newScreenName, setNewScreenName] = useState('');
  const [showNewScreenModal, setShowNewScreenModal] = useState(false);

  const filteredIcons = ICON_CATALOG.filter(
    (item) =>
      item.name.toLowerCase().includes(iconSearch.toLowerCase()) ||
      item.id.toLowerCase().includes(iconSearch.toLowerCase()) ||
      item.category.toLowerCase().includes(iconSearch.toLowerCase())
  );

  const bgCard = isDark ? '#1A1D24' : '#FFFFFF';
  const bgSubtle = isDark ? '#262A35' : '#F0F2F5';
  const borderSubtle = isDark ? '#2D333F' : '#E5E7EB';
  const textPrimary = isDark ? '#F9FAFB' : '#111827';
  const textSecondary = isDark ? '#9CA3AF' : '#4B5563';

  return (
    <aside
      className="w-80 h-full flex flex-col shrink-0 border-r transition-colors select-none z-20"
      style={{
        backgroundColor: bgCard,
        borderColor: borderSubtle,
      }}
    >
      {/* Top Segmented Tab Navigation */}
      <div className="p-3 border-b" style={{ borderColor: borderSubtle }}>
        <div
          className="grid grid-cols-3 p-1 rounded-xl gap-1 text-xs font-medium"
          style={{ backgroundColor: bgSubtle }}
        >
          <button
            type="button"
            className={`py-1.5 px-2 rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'screens'
                ? 'bg-blue-500 text-white shadow-sm font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
            onClick={() => setActiveTab('screens')}
          >
            <Layers size={14} />
            <span>Pantallas</span>
          </button>

          <button
            type="button"
            className={`py-1.5 px-2 rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'elements'
                ? 'bg-blue-500 text-white shadow-sm font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
            onClick={() => setActiveTab('elements')}
          >
            <Component size={14} />
            <span>Elementos</span>
          </button>

          <button
            type="button"
            className={`py-1.5 px-2 rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'icons'
                ? 'bg-blue-500 text-white shadow-sm font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
            onClick={() => setActiveTab('icons')}
          >
            <Smile size={14} />
            <span>Iconos</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Screens */}
      {activeTab === 'screens' && (
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="p-3 flex items-center justify-between border-b" style={{ borderColor: borderSubtle }}>
            <span className="text-xs font-semibold tracking-wider uppercase" style={{ color: textSecondary }}>
              PANTALLAS ({screens.length})
            </span>
            <button
              type="button"
              className="text-xs px-2.5 py-1 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500 hover:text-white transition-all flex items-center gap-1 font-medium cursor-pointer"
              onClick={() => setShowNewScreenModal(true)}
            >
              <Plus size={13} />
              <span>Nueva</span>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {screens.map((scr) => {
              const isActive = scr.id === activeScreenId;
              return (
                <div
                  key={scr.id}
                  className={`p-3 rounded-xl border transition-all cursor-pointer group flex flex-col justify-between ${
                    isActive
                      ? 'border-blue-500 ring-1 ring-blue-500/50 shadow-sm'
                      : 'hover:border-gray-500'
                  }`}
                  style={{
                    backgroundColor: isActive ? (isDark ? '#222630' : '#EFF6FF') : bgSubtle,
                    borderColor: isActive ? '#3B82F6' : borderSubtle,
                  }}
                  onClick={() => onSelectScreen(scr.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
                        style={{
                          backgroundColor: isActive ? '#3B82F6' : `${borderSubtle}`,
                          color: isActive ? '#FFFFFF' : textSecondary,
                        }}
                      >
                        <FocalIcon name={scr.icon} size={15} />
                      </div>
                      <div>
                        <div className="text-xs font-semibold" style={{ color: textPrimary }}>
                          {scr.name}
                        </div>
                        <div className="text-[10px]" style={{ color: textSecondary }}>
                          {scr.elements.length} elementos
                        </div>
                      </div>
                    </div>

                    {/* Quick duplicate / delete actions on hover */}
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        type="button"
                        className="p-1 rounded text-gray-400 hover:text-white hover:bg-gray-700/50 cursor-pointer"
                        title="Duplicar Pantalla"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDuplicateScreen(scr.id);
                        }}
                      >
                        <Copy size={13} />
                      </button>
                      {screens.length > 1 && (
                        <button
                          type="button"
                          className="p-1 rounded text-gray-400 hover:text-red-400 hover:bg-red-500/10 cursor-pointer"
                          title="Eliminar Pantalla"
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteScreen(scr.id);
                          }}
                        >
                          <Trash2 size={13} />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="mt-2 text-[10px] line-clamp-1 italic" style={{ color: textSecondary }}>
                    {scr.description}
                  </div>
                </div>
              );
            })}
          </div>

          {/* New Screen Dialog Modal */}
          {showNewScreenModal && (
            <div className="p-3 border-t bg-black/20" style={{ borderColor: borderSubtle }}>
              <div className="text-xs font-medium mb-1.5" style={{ color: textPrimary }}>
                Nombre de la nueva pantalla:
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Ej: Diagnóstico Motores"
                  value={newScreenName}
                  onChange={(e) => setNewScreenName(e.target.value)}
                  className="flex-1 px-2.5 py-1.5 text-xs rounded-lg border outline-none bg-black/20 focus:border-blue-500"
                  style={{ borderColor: borderSubtle, color: textPrimary }}
                />
                <button
                  type="button"
                  className="px-3 py-1.5 rounded-lg bg-blue-500 text-white text-xs font-semibold cursor-pointer"
                  onClick={() => {
                    if (newScreenName.trim()) {
                      onAddScreen(newScreenName.trim());
                      setNewScreenName('');
                      setShowNewScreenModal(false);
                    }
                  }}
                >
                  Crear
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Elements (Canva-style component palette) */}
      {activeTab === 'elements' && (
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          <div className="text-[10px] font-semibold tracking-wider uppercase" style={{ color: textSecondary }}>
            COMPONENTES FOCAL DESIGN SYSTEM
          </div>

          {/* Squircle Card */}
          <button
            type="button"
            className="w-full p-2.5 rounded-xl border text-left transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-between"
            style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            onClick={() =>
              onAddElement({
                type: 'card',
                name: 'Tarjeta Squircle',
                w: 142,
                h: 120,
                radius: 14,
                text: 'Tarjeta Squircle',
                subtext: 'Subtítulo M 14px',
                fontSize: 13,
                icon: 'shapes',
                accentColor: '#60A5FA',
              })
            }
          >
            <div>
              <div className="text-xs font-semibold" style={{ color: textPrimary }}>
                Tarjeta Squircle (Focal Card)
              </div>
              <div className="text-[10px]" style={{ color: textSecondary }}>
                Radio M=14px, acento pastel y borde 1px
              </div>
            </div>
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
              <Component size={16} />
            </div>
          </button>

          {/* Primary Button */}
          <button
            type="button"
            className="w-full p-2.5 rounded-xl border text-left transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-between"
            style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            onClick={() =>
              onAddElement({
                type: 'button_primary',
                name: 'Botón Primario',
                w: 120,
                h: 44,
                radius: 10,
                text: 'Acción Primaria',
                fontSize: 12,
                accentColor: '#60A5FA',
                icon: 'check',
              })
            }
          >
            <div>
              <div className="text-xs font-semibold" style={{ color: textPrimary }}>
                Botón Primario (Pastel Blue)
              </div>
              <div className="text-[10px]" style={{ color: textSecondary }}>
                Énfasis alto, radio M 10px (#60A5FA)
              </div>
            </div>
            <div className="w-8 h-8 rounded-lg bg-blue-500 text-white flex items-center justify-center text-xs font-bold">
              PRI
            </div>
          </button>

          {/* Secondary Button */}
          <button
            type="button"
            className="w-full p-2.5 rounded-xl border text-left transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-between"
            style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            onClick={() =>
              onAddElement({
                type: 'button_secondary',
                name: 'Botón Secundario',
                w: 120,
                h: 44,
                radius: 10,
                text: 'Secundario',
                fontSize: 12,
                accentColor: '#60A5FA',
              })
            }
          >
            <div>
              <div className="text-xs font-semibold" style={{ color: textPrimary }}>
                Botón Secundario
              </div>
              <div className="text-[10px]" style={{ color: textSecondary }}>
                Fondo sutil y borde suave
              </div>
            </div>
            <div className="w-8 h-8 rounded-lg border border-gray-500 text-gray-300 flex items-center justify-center text-xs">
              SEC
            </div>
          </button>

          {/* Mint Action Button */}
          <button
            type="button"
            className="w-full p-2.5 rounded-xl border text-left transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-between"
            style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            onClick={() =>
              onAddElement({
                type: 'button_mint',
                name: 'Botón Iniciar Corte',
                w: 150,
                h: 50,
                radius: 12,
                text: 'INICIAR CORTE',
                fontSize: 12,
                fontWeight: 'bold',
                accentColor: '#34D399',
                icon: 'play',
              })
            }
          >
            <div>
              <div className="text-xs font-semibold text-emerald-400">
                Botón Acción Menta (#34D399)
              </div>
              <div className="text-[10px]" style={{ color: textSecondary }}>
                Iniciar corte / Conectar máquina
              </div>
            </div>
            <div className="w-8 h-8 rounded-lg bg-emerald-500 text-black flex items-center justify-center">
              <FocalIcon name="play" size={16} />
            </div>
          </button>

          {/* Amber Alert Button */}
          <button
            type="button"
            className="w-full p-2.5 rounded-xl border text-left transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-between"
            style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            onClick={() =>
              onAddElement({
                type: 'button_amber',
                name: 'Botón Pausa/Alerta',
                w: 140,
                h: 48,
                radius: 12,
                text: 'PAUSAR TRABAJO',
                fontSize: 12,
                fontWeight: 'bold',
                accentColor: '#FBBF24',
                icon: 'pause',
              })
            }
          >
            <div>
              <div className="text-xs font-semibold text-amber-400">
                Botón Alerta Ámbar (#FBBF24)
              </div>
              <div className="text-[10px]" style={{ color: textSecondary }}>
                Pausa / Puntero láser / Framing
              </div>
            </div>
            <div className="w-8 h-8 rounded-lg bg-amber-500 text-black flex items-center justify-center">
              <FocalIcon name="pause" size={16} />
            </div>
          </button>

          {/* Red Danger Button */}
          <button
            type="button"
            className="w-full p-2.5 rounded-xl border text-left transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-between"
            style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            onClick={() =>
              onAddElement({
                type: 'button_danger',
                name: 'E-STOP Emergencia',
                w: 160,
                h: 52,
                radius: 12,
                text: 'PARADA DE EMERGENCIA',
                fontSize: 11,
                fontWeight: 'bold',
                accentColor: '#F87171',
                icon: 'estop',
              })
            }
          >
            <div>
              <div className="text-xs font-semibold text-red-400">
                Botón Peligro Rojo (#F87171)
              </div>
              <div className="text-[10px]" style={{ color: textSecondary }}>
                E-STOP / Reset de fábrica
              </div>
            </div>
            <div className="w-8 h-8 rounded-lg bg-red-500 text-white flex items-center justify-center">
              <FocalIcon name="estop" size={16} />
            </div>
          </button>

          {/* Text Label */}
          <button
            type="button"
            className="w-full p-2.5 rounded-xl border text-left transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-between"
            style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            onClick={() =>
              onAddElement({
                type: 'label',
                name: 'Etiqueta Texto',
                w: 160,
                h: 30,
                radius: 0,
                text: 'Texto Montserrat / Inter',
                fontSize: 14,
                fontWeight: 'bold',
                accentColor: '#60A5FA',
              })
            }
          >
            <div>
              <div className="text-xs font-semibold" style={{ color: textPrimary }}>
                Etiqueta de Texto
              </div>
              <div className="text-[10px]" style={{ color: textSecondary }}>
                Títulos, subtítulos y telemetría
              </div>
            </div>
            <div className="w-8 h-8 rounded-lg bg-gray-700 text-white flex items-center justify-center font-serif text-sm">
              Aa
            </div>
          </button>

          {/* Tactile Slider */}
          <button
            type="button"
            className="w-full p-2.5 rounded-xl border text-left transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-between"
            style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            onClick={() =>
              onAddElement({
                type: 'slider',
                name: 'Slider Potencia/Velocidad',
                w: 200,
                h: 60,
                radius: 12,
                text: 'Potencia Láser (S)',
                fontSize: 11,
                value: 75,
                minValue: 0,
                maxValue: 100,
                unit: '%',
                accentColor: '#FBBF24',
              })
            }
          >
            <div>
              <div className="text-xs font-semibold" style={{ color: textPrimary }}>
                Slider Táctil de Precisión
              </div>
              <div className="text-[10px]" style={{ color: textSecondary }}>
                Canaleta píldora con thumb dinámico
              </div>
            </div>
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
              <FocalIcon name="gauge" size={16} />
            </div>
          </button>

          {/* Apple-style Switch */}
          <button
            type="button"
            className="w-full p-2.5 rounded-xl border text-left transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-between"
            style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            onClick={() =>
              onAddElement({
                type: 'switch',
                name: 'Switch Asistencia Aire',
                w: 200,
                h: 54,
                radius: 12,
                text: 'M8 Asistencia de Aire',
                subtext: 'Activar relé de compresor',
                fontSize: 11,
                value: true,
                accentColor: '#34D399',
              })
            }
          >
            <div>
              <div className="text-xs font-semibold" style={{ color: textPrimary }}>
                Switch Apple-Style
              </div>
              <div className="text-[10px]" style={{ color: textSecondary }}>
                Interruptor con halo y animación
              </div>
            </div>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <FocalIcon name="power" size={16} />
            </div>
          </button>

          {/* DRO Display */}
          <button
            type="button"
            className="w-full p-2.5 rounded-xl border text-left transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-between"
            style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            onClick={() =>
              onAddElement({
                type: 'dro',
                name: 'Lectura DRO Coordenadas',
                w: 190,
                h: 110,
                radius: 14,
                text: 'DRO COORDINATES',
                fontSize: 14,
                accentColor: '#60A5FA',
                customData: { xVal: '0.00', yVal: '0.00', zVal: '15.00' },
              })
            }
          >
            <div>
              <div className="text-xs font-semibold" style={{ color: textPrimary }}>
                DRO Display (Lectura X/Y/Z)
              </div>
              <div className="text-[10px]" style={{ color: textSecondary }}>
                Lectura digital de posición en mm
              </div>
            </div>
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center font-mono text-[10px] font-bold">
              X/Y
            </div>
          </button>

          {/* Interactive Laser Bed 160x200 */}
          <button
            type="button"
            className="w-full p-2.5 rounded-xl border text-left transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-between"
            style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            onClick={() =>
              onAddElement({
                type: 'bed',
                name: 'Cama Láser 160x200',
                w: 220,
                h: 240,
                radius: 14,
                text: 'Área Cama 160x200 mm',
                fontSize: 11,
                accentColor: '#60A5FA',
                customData: { bedWidth: 160, bedHeight: 200, shape: 'circle' },
              })
            }
          >
            <div>
              <div className="text-xs font-semibold" style={{ color: textPrimary }}>
                Cama de Corte 160x200 mm
              </div>
              <div className="text-[10px]" style={{ color: textSecondary }}>
                Grilla de área útil y ubicación
              </div>
            </div>
            <div className="w-8 h-8 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center">
              <FocalIcon name="shapes" size={16} />
            </div>
          </button>

          {/* Status Pill */}
          <button
            type="button"
            className="w-full p-2.5 rounded-xl border text-left transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-between"
            style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            onClick={() =>
              onAddElement({
                type: 'status_pill',
                name: 'Píldora de Estado',
                w: 110,
                h: 28,
                radius: 999,
                text: 'IDLE (LISTO)',
                fontSize: 10,
                accentColor: '#34D399',
              })
            }
          >
            <div>
              <div className="text-xs font-semibold" style={{ color: textPrimary }}>
                Píldora de Estado (Status Pill)
              </div>
              <div className="text-[10px]" style={{ color: textSecondary }}>
                Pip de estado y fondo atenuado
              </div>
            </div>
            <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs">
              •
            </div>
          </button>
        </div>
      )}

      {/* Tab 3: Vector Icons Catalog */}
      {activeTab === 'icons' && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Search Bar */}
          <div className="p-3 border-b" style={{ borderColor: borderSubtle }}>
            <div
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl border text-xs"
              style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
            >
              <Search size={14} className="text-gray-400 shrink-0" />
              <input
                type="text"
                placeholder="Buscar iconos..."
                value={iconSearch}
                onChange={(e) => setIconSearch(e.target.value)}
                className="w-full bg-transparent outline-none text-xs"
                style={{ color: textPrimary }}
              />
            </div>
          </div>

          {selectedElement && (
            <div className="px-3 py-2 bg-blue-500/10 border-b border-blue-500/30 flex items-center justify-between text-[11px] text-blue-400">
              <span>Elemento: {selectedElement.name}</span>
              <span className="text-[10px] opacity-75">Clic asigna icono</span>
            </div>
          )}

          {/* Icons Grid */}
          <div className="flex-1 overflow-y-auto p-3">
            <div className="grid grid-cols-3 gap-2">
              {filteredIcons.map((ic) => (
                <button
                  key={ic.id}
                  type="button"
                  className="p-2.5 rounded-xl border flex flex-col items-center justify-center gap-1.5 transition-all hover:scale-105 hover:border-blue-500 cursor-pointer group"
                  style={{ backgroundColor: bgSubtle, borderColor: borderSubtle }}
                  onClick={() => {
                    if (selectedElement) {
                      onUpdateSelectedIcon(ic.id);
                    } else {
                      // Add standalone icon
                      onAddElement({
                        type: 'icon',
                        name: `Icono ${ic.name}`,
                        w: 48,
                        h: 48,
                        radius: 12,
                        text: ic.name,
                        icon: ic.id,
                        accentColor: '#60A5FA',
                      });
                    }
                  }}
                  title={ic.name}
                >
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center text-blue-400 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                    <FocalIcon name={ic.id} size={20} />
                  </div>
                  <span className="text-[9px] text-center truncate w-full" style={{ color: textSecondary }}>
                    {ic.name}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
