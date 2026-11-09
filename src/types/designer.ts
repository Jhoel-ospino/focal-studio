export type ElementType =
  | 'card'
  | 'button_primary'
  | 'button_secondary'
  | 'button_mint'
  | 'button_amber'
  | 'button_danger'
  | 'label'
  | 'slider'
  | 'switch'
  | 'dro'
  | 'bed'
  | 'status_pill'
  | 'icon'
  | 'progress_bar';

export type TextMode = 'ellipsis' | 'multiline';

export interface FocalElement {
  id: string;
  type: ElementType;
  name: string;
  x: number;
  y: number;
  w: number;
  h: number;
  radius: number; // 0, 8, 10, 14, 20, 999 (pill)
  text: string;
  subtext?: string;
  textMode: TextMode;
  fontSize: number; // e.g. 10, 11, 12, 13, 14, 16, 20
  fontWeight?: 'normal' | 'medium' | 'semibold' | 'bold';
  textAlign?: 'left' | 'center' | 'right';
  icon?: string;
  iconColor?: string;
  iconSize?: number;
  accentColor: string; // Pastel blue (#60A5FA), mint (#34D399), amber (#FBBF24), purple (#A78BFA), red (#F87171)
  backgroundColor?: string;
  borderColor?: string;
  borderWidth?: number;
  textColor?: string;
  value?: number | boolean | string;
  minValue?: number;
  maxValue?: number;
  unit?: string;
  locked?: boolean;
  visible?: boolean;
  zIndex: number;
  customData?: Record<string, any>;
}

export interface ScreenLayout {
  id: string;
  name: string;
  description: string;
  icon: string;
  elements: FocalElement[];
}

export interface ProjectData {
  projectName: string;
  version: string;
  canvasWidth: number; // 480
  canvasHeight: number; // 320
  activeScreenId: string;
  screens: ScreenLayout[];
}

export type SnapGridSize = 0 | 4 | 8;
export type CanvasZoom = 1.0 | 1.5 | 2.0 | 'fit';

export interface Guideline {
  type: 'x' | 'y';
  position: number;
}
