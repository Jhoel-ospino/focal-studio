import { useState, useRef, useEffect, useCallback } from 'react';
import { FocalElement, Guideline, SnapGridSize, CanvasZoom } from '../types/designer';
import { RenderElement } from './RenderElement';
import { calculateMagneticSnap } from '../utils/snapping';

interface CanvasViewportProps {
  elements: FocalElement[];
  selectedId: string | null;
  onSelectElement: (id: string | null) => void;
  onUpdateElement: (id: string, updates: Partial<FocalElement>) => void;
  onDeleteElement: (id: string) => void;
  onDuplicateElement: (id: string) => void;
  isDark: boolean;
  zoom: CanvasZoom;
  snapGrid: SnapGridSize;
  onUndo: () => void;
  onRedo: () => void;
  onDragStart?: () => void;
}

type ResizeDirection = 'nw' | 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w';

interface DragState {
  type: 'move' | 'resize';
  elementId: string;
  startX: number;
  startY: number;
  initialX: number;
  initialY: number;
  initialW: number;
  initialH: number;
  direction?: ResizeDirection;
}

export function CanvasViewport({
  elements,
  selectedId,
  onSelectElement,
  onUpdateElement,
  onDeleteElement,
  onDuplicateElement,
  isDark,
  zoom,
  snapGrid,
  onUndo,
  onRedo,
  onDragStart,
}: CanvasViewportProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLDivElement>(null);

  const [guidelines, setGuidelines] = useState<Guideline[]>([]);
  const [dragState, setDragState] = useState<DragState | null>(null);
  const [liveInfo, setLiveInfo] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
  const [fitScale, setFitScale] = useState<number>(1.0);

  // Compute scale factor
  const computeFitScale = useCallback(() => {
    if (!containerRef.current) return;
    const { clientWidth, clientHeight } = containerRef.current;
    const padding = 60;
    const availW = Math.max(200, clientWidth - padding);
    const availH = Math.max(150, clientHeight - padding);
    const scaleW = availW / 480;
    const scaleH = availH / 320;
    setFitScale(Math.min(scaleW, scaleH));
  }, []);

  useEffect(() => {
    computeFitScale();
    window.addEventListener('resize', computeFitScale);
    return () => window.removeEventListener('resize', computeFitScale);
  }, [computeFitScale]);

  const currentScale = zoom === 'fit' ? fitScale : zoom;

  const selectedElement = elements.find((el) => el.id === selectedId);

  // Keyboard navigation & actions
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in an input or textarea
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) {
        return;
      }

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const cmdKey = isMac ? e.metaKey : e.ctrlKey;

      if (cmdKey && e.key.toLowerCase() === 'z') {
        e.preventDefault();
        if (e.shiftKey) {
          onRedo();
        } else {
          onUndo();
        }
        return;
      }

      if (cmdKey && e.key.toLowerCase() === 'y') {
        e.preventDefault();
        onRedo();
        return;
      }

      if (cmdKey && e.key.toLowerCase() === 'd' && selectedId) {
        e.preventDefault();
        onDuplicateElement(selectedId);
        return;
      }

      if ((e.key === 'Delete' || e.key === 'Backspace') && selectedId) {
        e.preventDefault();
        onDeleteElement(selectedId);
        return;
      }

      if (e.key === 'Escape') {
        onSelectElement(null);
        return;
      }

      // Arrow keys nudging
      if (selectedElement && ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        e.preventDefault();
        const step = e.shiftKey ? 8 : snapGrid > 0 ? snapGrid : 1;
        let dx = 0;
        let dy = 0;
        if (e.key === 'ArrowUp') dy = -step;
        if (e.key === 'ArrowDown') dy = step;
        if (e.key === 'ArrowLeft') dx = -step;
        if (e.key === 'ArrowRight') dx = step;

        const newX = Math.max(0, Math.min(480 - selectedElement.w, selectedElement.x + dx));
        const newY = Math.max(0, Math.min(320 - selectedElement.h, selectedElement.y + dy));
        onUpdateElement(selectedElement.id, { x: newX, y: newY });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedElement, selectedId, snapGrid, onUndo, onRedo, onDeleteElement, onDuplicateElement, onSelectElement, onUpdateElement]);

  // Handle pointer down on an element to start moving
  const handleElementPointerDown = (e: React.PointerEvent, el: FocalElement) => {
    e.stopPropagation();
    onSelectElement(el.id);
    onDragStart?.();

    setDragState({
      type: 'move',
      elementId: el.id,
      startX: e.clientX,
      startY: e.clientY,
      initialX: el.x,
      initialY: el.y,
      initialW: el.w,
      initialH: el.h,
    });

    setLiveInfo({ x: el.x, y: el.y, w: el.w, h: el.h });
  };

  // Handle pointer down on a resize handle
  const handleHandlePointerDown = (e: React.PointerEvent, direction: ResizeDirection) => {
    e.stopPropagation();
    if (!selectedElement) return;
    onDragStart?.();

    setDragState({
      type: 'resize',
      elementId: selectedElement.id,
      startX: e.clientX,
      startY: e.clientY,
      initialX: selectedElement.x,
      initialY: selectedElement.y,
      initialW: selectedElement.w,
      initialH: selectedElement.h,
      direction,
    });

    setLiveInfo({
      x: selectedElement.x,
      y: selectedElement.y,
      w: selectedElement.w,
      h: selectedElement.h,
    });
  };

  // Pointer move handler (global during dragging)
  const handlePointerMove = (e: React.PointerEvent) => {
    if (!dragState) return;

    const deltaX = (e.clientX - dragState.startX) / currentScale;
    const deltaY = (e.clientY - dragState.startY) / currentScale;

    const el = elements.find((item) => item.id === dragState.elementId);
    if (!el) return;

    if (dragState.type === 'move') {
      const rawX = dragState.initialX + deltaX;
      const rawY = dragState.initialY + deltaY;

      const otherElements = elements.filter((item) => item.id !== el.id);
      const snapResult = calculateMagneticSnap(
        rawX,
        rawY,
        el.w,
        el.h,
        otherElements,
        snapGrid,
        480,
        320
      );

      setGuidelines(snapResult.guidelines);
      setLiveInfo({ x: Math.round(snapResult.x), y: Math.round(snapResult.y), w: el.w, h: el.h });
      onUpdateElement(el.id, { x: Math.round(snapResult.x), y: Math.round(snapResult.y) });
    } else if (dragState.type === 'resize' && dragState.direction) {
      const dir = dragState.direction;
      let newX = dragState.initialX;
      let newY = dragState.initialY;
      let newW = dragState.initialW;
      let newH = dragState.initialH;

      const minSize = 16;

      if (dir.includes('e')) {
        newW = Math.max(minSize, dragState.initialW + deltaX);
      }
      if (dir.includes('s')) {
        newH = Math.max(minSize, dragState.initialH + deltaY);
      }
      if (dir.includes('w')) {
        const potentialW = dragState.initialW - deltaX;
        if (potentialW >= minSize) {
          newW = potentialW;
          newX = dragState.initialX + deltaX;
        }
      }
      if (dir.includes('n')) {
        const potentialH = dragState.initialH - deltaY;
        if (potentialH >= minSize) {
          newH = potentialH;
          newY = dragState.initialY + deltaY;
        }
      }

      // Apply grid snap to resizing
      if (snapGrid > 0) {
        newX = Math.round(newX / snapGrid) * snapGrid;
        newY = Math.round(newY / snapGrid) * snapGrid;
        newW = Math.round(newW / snapGrid) * snapGrid;
        newH = Math.round(newH / snapGrid) * snapGrid;
      }

      // Keep inside 480x320 canvas while strictly preserving minSize >= 16
      newX = Math.max(0, Math.min(480 - minSize, newX));
      newY = Math.max(0, Math.min(320 - minSize, newY));
      newW = Math.max(minSize, Math.min(480 - newX, newW));
      newH = Math.max(minSize, Math.min(320 - newY, newH));

      setLiveInfo({ x: Math.round(newX), y: Math.round(newY), w: Math.round(newW), h: Math.round(newH) });
      onUpdateElement(el.id, {
        x: Math.round(newX),
        y: Math.round(newY),
        w: Math.round(newW),
        h: Math.round(newH),
      });
    }
  };

  const handlePointerUp = () => {
    setDragState(null);
    setGuidelines([]);
    setLiveInfo(null);
  };

  return (
    <div
      ref={containerRef}
      className="flex-1 h-full flex flex-col items-center justify-center relative overflow-hidden canvas-grid-pattern p-6"
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerDown={() => onSelectElement(null)}
    >
      {/* Canvas Frame / Bezel 3.5" (3:2 Aspect Ratio: 480x320 px) */}
      <div
        className="relative transition-transform duration-75 select-none"
        style={{
          transform: `scale(${currentScale})`,
          transformOrigin: 'center center',
          width: 480,
          height: 320,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Physical TFT Bezel & Silkscreen Header */}
        <div
          className="absolute -top-7 left-0 right-0 flex items-center justify-between px-1 text-[10px] font-mono tracking-wider pointer-events-none"
          style={{ color: isDark ? '#6B7280' : '#9CA3AF' }}
        >
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>TFT 3.5&quot; ILI9488 • 480×320 (3:2)</span>
          </div>
          <span>ZOOM: {(currentScale * 100).toFixed(0)}%</span>
        </div>

        {/* TFT Screen Glass / Viewport */}
        <div
          ref={canvasRef}
          className="w-full h-full relative overflow-hidden rounded-md shadow-2xl transition-colors duration-150"
          style={{
            backgroundColor: isDark ? '#0F1115' : '#F5F6F8',
            border: isDark ? '2px solid #2D333F' : '2px solid #CBD5E1',
            boxShadow: isDark
              ? '0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 20px rgba(96, 165, 250, 0.1)'
              : '0 20px 35px -10px rgba(0, 0, 0, 0.15)',
          }}
          onPointerDown={(e) => {
            if (e.target === canvasRef.current) {
              onSelectElement(null);
            }
          }}
        >
          {/* Subtle 8px / 4px background grid on canvas */}
          {snapGrid > 0 && (
            <div
              className="absolute inset-0 pointer-events-none opacity-25"
              style={{
                backgroundImage: isDark
                  ? `radial-gradient(circle, #4B5563 0.75px, transparent 0.75px)`
                  : `radial-gradient(circle, #94A3B8 0.75px, transparent 0.75px)`,
                backgroundSize: `${snapGrid * 2}px ${snapGrid * 2}px`,
              }}
            />
          )}

          {/* Render Elements */}
          {elements
            .slice()
            .sort((a, b) => a.zIndex - b.zIndex)
            .map((el) => {
              const isSelected = el.id === selectedId;
              const isSmallHitbox = el.w < 44 || el.h < 44;

              return (
                <div
                  key={el.id}
                  className={`absolute group cursor-move select-none ${
                    isSelected ? 'z-50' : ''
                  }`}
                  style={{
                    left: el.x,
                    top: el.y,
                    width: el.w,
                    height: el.h,
                    zIndex: isSelected ? 9999 : el.zIndex,
                  }}
                  onPointerDown={(e) => handleElementPointerDown(e, el)}
                >
                  {/* Element Contents */}
                  <RenderElement
                    element={el}
                    isSelected={isSelected}
                    isDark={isDark}
                  />

                  {/* ISO 9241-9 Touch Accessibility Alert indicator if < 44x44 */}
                  {isSmallHitbox && (
                    <div
                      className="absolute -top-1.5 -right-1.5 w-3.5 h-3.5 rounded-full bg-amber-500 text-black text-[8px] font-bold flex items-center justify-center shadow-md pointer-events-none"
                      title="Área táctil menor a 44x44 px (ISO 9241-9)"
                    >
                      !
                    </div>
                  )}

                  {/* Selection Bounding Box & 8 Resize Handles */}
                  {isSelected && (
                    <div className="absolute inset-0 border-2 border-blue-500 pointer-events-none rounded-[inherit]">
                      {/* NW handle */}
                      <div
                        className="absolute -top-1.5 -left-1.5 w-3 h-3 bg-white border-2 border-blue-500 rounded-sm cursor-nwse-resize pointer-events-auto shadow"
                        onPointerDown={(e) => handleHandlePointerDown(e, 'nw')}
                      />
                      {/* N handle */}
                      <div
                        className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-2 border-blue-500 rounded-sm cursor-ns-resize pointer-events-auto shadow"
                        onPointerDown={(e) => handleHandlePointerDown(e, 'n')}
                      />
                      {/* NE handle */}
                      <div
                        className="absolute -top-1.5 -right-1.5 w-3 h-3 bg-white border-2 border-blue-500 rounded-sm cursor-nesw-resize pointer-events-auto shadow"
                        onPointerDown={(e) => handleHandlePointerDown(e, 'ne')}
                      />
                      {/* E handle */}
                      <div
                        className="absolute top-1/2 -right-1.5 -translate-y-1/2 w-3 h-3 bg-white border-2 border-blue-500 rounded-sm cursor-ew-resize pointer-events-auto shadow"
                        onPointerDown={(e) => handleHandlePointerDown(e, 'e')}
                      />
                      {/* SE handle */}
                      <div
                        className="absolute -bottom-1.5 -right-1.5 w-3 h-3 bg-white border-2 border-blue-500 rounded-sm cursor-nwse-resize pointer-events-auto shadow"
                        onPointerDown={(e) => handleHandlePointerDown(e, 'se')}
                      />
                      {/* S handle */}
                      <div
                        className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-2 border-blue-500 rounded-sm cursor-ns-resize pointer-events-auto shadow"
                        onPointerDown={(e) => handleHandlePointerDown(e, 's')}
                      />
                      {/* SW handle */}
                      <div
                        className="absolute -bottom-1.5 -left-1.5 w-3 h-3 bg-white border-2 border-blue-500 rounded-sm cursor-nesw-resize pointer-events-auto shadow"
                        onPointerDown={(e) => handleHandlePointerDown(e, 'sw')}
                      />
                      {/* W handle */}
                      <div
                        className="absolute top-1/2 -left-1.5 -translate-y-1/2 w-3 h-3 bg-white border-2 border-blue-500 rounded-sm cursor-ew-resize pointer-events-auto shadow"
                        onPointerDown={(e) => handleHandlePointerDown(e, 'w')}
                      />
                    </div>
                  )}
                </div>
              );
            })}

          {/* Magnetic Alignment Guidelines */}
          {guidelines.map((guide, idx) => {
            if (guide.type === 'x') {
              return (
                <div
                  key={`guide-x-${idx}`}
                  className="absolute top-0 bottom-0 w-[1px] bg-pink-500 z-50 pointer-events-none"
                  style={{ left: guide.position }}
                />
              );
            }
            return (
              <div
                key={`guide-y-${idx}`}
                className="absolute left-0 right-0 h-[1px] bg-pink-500 z-50 pointer-events-none"
                style={{ top: guide.position }}
              />
            );
          })}
        </div>

        {/* Live floating coordinate tooltip during drag / resize */}
        {liveInfo && (
          <div
            className="absolute -bottom-9 left-1/2 -translate-x-1/2 bg-blue-600 text-white font-mono text-[10px] px-2.5 py-1 rounded-full shadow-lg pointer-events-none flex items-center gap-2 whitespace-nowrap z-50"
          >
            <span>X: {liveInfo.x} px</span>
            <span>Y: {liveInfo.y} px</span>
            <span className="opacity-60">|</span>
            <span>W: {liveInfo.w} px</span>
            <span>H: {liveInfo.h} px</span>
          </div>
        )}
      </div>
    </div>
  );
}
