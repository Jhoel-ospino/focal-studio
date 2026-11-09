import { FocalElement } from '../types/designer';
import { FocalIcon } from './FocalIcon';

interface RenderElementProps {
  element: FocalElement;
  isSelected: boolean;
  isDark: boolean;
}

export function RenderElement({ element, isSelected, isDark }: RenderElementProps) {
  const {
    type,
    text,
    subtext,
    w,
    h,
    radius,
    fontSize,
    fontWeight = 'medium',
    textAlign = 'center',
    icon,
    iconColor,
    iconSize = 18,
    accentColor,
    textColor,
    textMode,
    value,
    minValue = 0,
    maxValue = 100,
    unit = '',
    customData,
  } = element;

  // Determine standard colors based on theme and tokens
  const bgCard = isDark ? '#1A1D24' : '#FFFFFF';
  const bgSubtle = isDark ? '#262A35' : '#F0F2F5';
  const borderSubtle = isDark ? '#2D333F' : '#E5E7EB';
  const textPrimary = textColor || (isDark ? '#F9FAFB' : '#111827');
  const textSecondary = isDark ? '#9CA3AF' : '#4B5563';
  const textInverse = isDark ? '#111827' : '#FFFFFF';

  // Radius calculation
  const borderRadius = radius >= 999 ? 9999 : radius;

  // Font weight class
  const fwClass =
    fontWeight === 'bold'
      ? 'font-bold'
      : fontWeight === 'semibold'
      ? 'font-semibold'
      : fontWeight === 'normal'
      ? 'font-normal'
      : 'font-medium';

  // Render by element type
  switch (type) {
    case 'card': {
      return (
        <div
          className="w-full h-full p-2.5 flex flex-col justify-between overflow-hidden transition-colors"
          style={{
            backgroundColor: bgCard,
            border: `1px solid ${borderSubtle}`,
            borderRadius,
            boxShadow: isDark
              ? '0 2px 8px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)'
              : '0 2px 6px rgba(0,0,0,0.06), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          <div className="flex items-center justify-between gap-1.5">
            {icon && (
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                style={{
                  backgroundColor: `${accentColor}18`,
                  color: iconColor || accentColor,
                }}
              >
                <FocalIcon name={icon} size={iconSize} color={iconColor || accentColor} />
              </div>
            )}
            <div className="flex-1 min-w-0 text-right">
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{ backgroundColor: accentColor }}
              />
            </div>
          </div>
          <div className="mt-auto">
            <div
              className={`text-left leading-tight ${fwClass} ${
                textMode === 'ellipsis' ? 'truncate' : ''
              }`}
              style={{ fontSize, color: textPrimary }}
            >
              {text}
            </div>
            {subtext && (
              <div
                className="text-left text-[10px] leading-tight mt-0.5 truncate"
                style={{ color: textSecondary }}
              >
                {subtext}
              </div>
            )}
          </div>
        </div>
      );
    }

    case 'button_primary':
    case 'button_mint':
    case 'button_amber':
    case 'button_danger': {
      let solidBg = accentColor;
      if (type === 'button_mint') solidBg = '#34D399';
      if (type === 'button_amber') solidBg = '#FBBF24';
      if (type === 'button_danger') solidBg = '#F87171';

      return (
        <div
          className={`w-full h-full px-2 py-1 flex items-center justify-center gap-1.5 overflow-hidden transition-all shadow-sm ${fwClass}`}
          style={{
            backgroundColor: solidBg,
            borderRadius,
            color: textInverse,
            fontSize,
          }}
        >
          {icon && <FocalIcon name={icon} size={iconSize} color={textInverse} />}
          <span className={`min-w-0 ${textMode === 'ellipsis' ? 'truncate' : ''}`}>{text}</span>
        </div>
      );
    }

    case 'button_secondary': {
      return (
        <div
          className={`w-full h-full px-2 py-1 flex items-center justify-center gap-1.5 overflow-hidden transition-all ${fwClass}`}
          style={{
            backgroundColor: bgSubtle,
            border: `1px solid ${borderSubtle}`,
            borderRadius,
            color: textPrimary,
            fontSize,
          }}
        >
          {icon && <FocalIcon name={icon} size={iconSize} color={iconColor || accentColor} />}
          <span className={`min-w-0 ${textMode === 'ellipsis' ? 'truncate' : ''}`}>{text}</span>
        </div>
      );
    }

    case 'status_pill': {
      return (
        <div
          className="w-full h-full px-2.5 flex items-center justify-center gap-2 overflow-hidden border transition-all"
          style={{
            backgroundColor: `${accentColor}18`,
            borderColor: `${accentColor}44`,
            borderRadius: 9999,
          }}
        >
          <span
            className="w-2 h-2 rounded-full shrink-0 animate-pulse"
            style={{ backgroundColor: accentColor }}
          />
          <span
            className="font-semibold tracking-wider uppercase truncate min-w-0"
            style={{ fontSize: fontSize || 10, color: accentColor }}
          >
            {text}
          </span>
        </div>
      );
    }

    case 'slider': {
      const numVal = typeof value === 'number' ? value : 50;
      const pct = Math.max(0, Math.min(100, ((numVal - minValue) / (maxValue - minValue)) * 100));

      return (
        <div
          className="w-full h-full p-2 flex flex-col justify-center overflow-hidden"
          style={{
            backgroundColor: bgCard,
            border: `1px solid ${borderSubtle}`,
            borderRadius,
          }}
        >
          <div className="flex justify-between items-center text-[10px] mb-1 font-medium">
            <span className="truncate" style={{ color: textSecondary }}>
              {text}
            </span>
            <span className="font-semibold tabular-nums" style={{ color: accentColor }}>
              {numVal} {unit}
            </span>
          </div>
          <div className="relative w-full h-2.5 bg-black/20 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${pct}%`,
                backgroundColor: accentColor,
              }}
            />
          </div>
        </div>
      );
    }

    case 'switch': {
      const isChecked = Boolean(value);

      return (
        <div
          className="w-full h-full px-2.5 py-1.5 flex items-center justify-between gap-2 overflow-hidden"
          style={{
            backgroundColor: bgCard,
            border: `1px solid ${borderSubtle}`,
            borderRadius,
          }}
        >
          <div className="flex-1 min-w-0">
            <div className="text-[11px] font-medium truncate" style={{ color: textPrimary }}>
              {text}
            </div>
            {subtext && (
              <div className="text-[9px] truncate" style={{ color: textSecondary }}>
                {subtext}
              </div>
            )}
          </div>
          {/* Apple-style pill switch */}
          <div
            className="w-10 h-6 rounded-full p-0.5 flex items-center transition-colors shrink-0"
            style={{
              backgroundColor: isChecked ? accentColor : isDark ? '#374151' : '#D1D5DB',
            }}
          >
            <div
              className={`w-5 h-5 rounded-full bg-white shadow-md transform transition-transform ${
                isChecked ? 'translate-x-4' : 'translate-x-0'
              }`}
            />
          </div>
        </div>
      );
    }

    case 'dro': {
      const xVal = customData?.xVal ?? '0.00';
      const yVal = customData?.yVal ?? '0.00';
      const zVal = customData?.zVal ?? '15.00';

      return (
        <div
          className="w-full h-full p-2.5 flex flex-col justify-between overflow-hidden"
          style={{
            backgroundColor: isDark ? '#14171E' : '#F9FAFB',
            border: `1px solid ${borderSubtle}`,
            borderRadius,
          }}
        >
          <div className="flex justify-between items-center border-b pb-1" style={{ borderColor: borderSubtle }}>
            <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: textSecondary }}>
              {text || 'DRO POSICIÓN (WCS)'}
            </span>
            <span className="text-[9px] px-1.5 py-0.5 rounded font-mono" style={{ backgroundColor: `${accentColor}20`, color: accentColor }}>
              G54 • MM
            </span>
          </div>
          <div className="space-y-1 font-mono my-auto">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-blue-400">X:</span>
              <span className="font-semibold text-sm tabular-nums" style={{ color: textPrimary }}>{xVal} mm</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-emerald-400">Y:</span>
              <span className="font-semibold text-sm tabular-nums" style={{ color: textPrimary }}>{yVal} mm</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-amber-400">Z:</span>
              <span className="font-semibold text-sm tabular-nums" style={{ color: textSecondary }}>{zVal} mm</span>
            </div>
          </div>
        </div>
      );
    }

    case 'bed': {
      const bedW = customData?.bedWidth ?? 160;
      const bedH = customData?.bedHeight ?? 200;

      return (
        <div
          className="w-full h-full p-2 flex flex-col justify-between overflow-hidden relative"
          style={{
            backgroundColor: isDark ? '#11141B' : '#F8FAFC',
            border: `1px solid ${borderSubtle}`,
            borderRadius,
          }}
        >
          {/* Bed header */}
          <div className="flex justify-between items-center text-[10px] z-10">
            <span className="font-semibold" style={{ color: textSecondary }}>
              ÁREA DE CORTE: {bedW}x{bedH} mm
            </span>
            <span className="text-[9px] font-mono text-emerald-400">ORIGEN (0,0)</span>
          </div>

          {/* Grid representation */}
          <div
            className="w-full flex-1 my-1 rounded border border-dashed relative flex items-center justify-center overflow-hidden"
            style={{
              borderColor: isDark ? '#2D333F' : '#CBD5E1',
              backgroundColor: isDark ? '#0A0C10' : '#FFFFFF',
            }}
          >
            {/* Grid markings */}
            <div className="absolute inset-0 grid grid-cols-4 grid-rows-5 opacity-20 pointer-events-none">
              {Array.from({ length: 20 }).map((_, i) => (
                <div key={i} className="border-r border-b border-gray-500" />
              ))}
            </div>

            {/* Simulated workpiece shape on bed */}
            <div
              className="relative rounded-lg border-2 border-dashed flex items-center justify-center animate-pulse"
              style={{
                width: '60%',
                height: '55%',
                borderColor: accentColor,
                backgroundColor: `${accentColor}15`,
              }}
            >
              <div className="w-6 h-6 rounded-full border border-current flex items-center justify-center" style={{ color: accentColor }}>
                <span className="text-[8px] font-bold">LÁSER</span>
              </div>
            </div>

            {/* Corner Origin Indicator */}
            <div className="absolute bottom-1 left-1 flex items-center gap-0.5 text-[8px] font-mono text-emerald-400 bg-black/60 px-1 py-0.5 rounded">
              <span>(0,0)</span>
            </div>
          </div>

          <div className="text-[9px] text-center" style={{ color: textSecondary }}>
            {text}
          </div>
        </div>
      );
    }

    case 'label': {
      return (
        <div
          className={`w-full h-full flex flex-col justify-center overflow-hidden ${fwClass}`}
          style={{
            textAlign,
            color: textPrimary,
            fontSize,
          }}
        >
          <div className={textMode === 'ellipsis' ? 'truncate' : 'whitespace-pre-line'}>
            {text}
          </div>
          {subtext && (
            <div className="text-[10px] opacity-70 truncate mt-0.5">
              {subtext}
            </div>
          )}
        </div>
      );
    }

    case 'icon': {
      const safeSize = Math.max(8, Math.min(Math.max(8, w), Math.max(8, h)) * 0.75);
      return (
        <div className="w-full h-full flex items-center justify-center overflow-hidden">
          <FocalIcon name={icon || 'shapes'} size={safeSize} color={iconColor || accentColor} />
        </div>
      );
    }

    default:
      return (
        <div
          className="w-full h-full p-2 flex items-center justify-center text-xs"
          style={{ backgroundColor: bgSubtle, borderRadius }}
        >
          {text}
        </div>
      );
  }
}
