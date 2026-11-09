import {
  Compass,
  Folder,
  Activity,
  Zap,
  Target,
  Shapes,
  Settings,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Home,
  Trash2,
  Wifi,
  Check,
  Play,
  Pause,
  Square,
  RefreshCw,
  AlertOctagon,
  Circle,
  HelpCircle,
  Power,
  RotateCcw,
  Sparkles,
  Palette,
  Sun,
  Moon,
  Crosshair,
  Sliders,
  Maximize2,
  Gauge,
  Layers,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Flame,
  FileCode,
  FolderOpen,
  Cpu,
} from 'lucide-react';

export const ICON_CATALOG = [
  { id: 'control', name: 'Control / Jogging', category: 'Navegación', component: Compass },
  { id: 'files', name: 'Archivos SD', category: 'Navegación', component: Folder },
  { id: 'monitor', name: 'Monitor de Corte', category: 'Navegación', component: Activity },
  { id: 'calibration', name: 'Calibración Cama', category: 'Navegación', component: Target },
  { id: 'shapes', name: 'Figuras Rápidas', category: 'Navegación', component: Shapes },
  { id: 'settings', name: 'Ajustes de Máquina', category: 'Navegación', component: Settings },
  { id: 'laser', name: 'Cabezal Láser', category: 'Láser', component: Zap },
  { id: 'flame', name: 'Foco / Potencia', category: 'Láser', component: Flame },
  { id: 'home', name: 'Homing Máquina', category: 'Control', component: Home },
  { id: 'jog_up', name: 'Jog Arriba (Y+)', category: 'Control', component: ArrowUp },
  { id: 'jog_down', name: 'Jog Abajo (Y-)', category: 'Control', component: ArrowDown },
  { id: 'jog_left', name: 'Jog Izquierda (X-)', category: 'Control', component: ArrowLeft },
  { id: 'jog_right', name: 'Jog Derecha (X+)', category: 'Control', component: ArrowRight },
  { id: 'play', name: 'Iniciar / Continuar', category: 'Acción', component: Play },
  { id: 'pause', name: 'Pausar', category: 'Acción', component: Pause },
  { id: 'stop', name: 'Detener', category: 'Acción', component: Square },
  { id: 'refresh', name: 'Refrescar / Reload', category: 'Acción', component: RefreshCw },
  { id: 'trash', name: 'Eliminar Archivo', category: 'Acción', component: Trash2 },
  { id: 'check', name: 'Confirmar / Check', category: 'Acción', component: Check },
  { id: 'estop', name: 'Parada Emergencia', category: 'Seguridad', component: AlertOctagon },
  { id: 'wifi', name: 'Conexión Wi-Fi', category: 'Sistema', component: Wifi },
  { id: 'shape_circle', name: 'Círculo', category: 'Geometría', component: Circle },
  { id: 'shape_square', name: 'Cuadrado', category: 'Geometría', component: Square },
  { id: 'crosshair', name: 'Encuadrar / Framing', category: 'Láser', component: Crosshair },
  { id: 'gauge', name: 'Velocidad / Avance', category: 'Monitor', component: Gauge },
  { id: 'power', name: 'Encendido / M8', category: 'Sistema', component: Power },
];

export interface FocalIconProps {
  name?: string;
  size?: number;
  color?: string;
  className?: string;
}

export function FocalIcon({ name, size = 20, color, className }: FocalIconProps) {
  if (!name) return null;

  const found = ICON_CATALOG.find((icon) => icon.id.toLowerCase() === name.toLowerCase());
  const IconComponent = found ? found.component : HelpCircle;

  return (
    <IconComponent
      size={size}
      color={color}
      className={className}
      strokeWidth={2}
    />
  );
}
