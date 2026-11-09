import { useState, useEffect } from 'react';
import defaultProjectData from './data/screens_layout.json';
import {
  ProjectData,
  ScreenLayout,
  FocalElement,
  CanvasZoom,
  SnapGridSize,
} from './types/designer';
import { TopBar } from './components/TopBar';
import { LeftSidebar } from './components/LeftSidebar';
import { CanvasViewport } from './components/CanvasViewport';
import { RightInspector } from './components/RightInspector';
import { ExportCModal } from './components/ExportCModal';
import { SimulateModal } from './components/SimulateModal';
import { FlashModal } from './components/FlashModal';

const STORAGE_KEY = 'focal_designer_layout_v1';

export default function App() {
  // Theme state
  const [isDark, setIsDark] = useState<boolean>(true);

  // Load project data
  const [project, setProject] = useState<ProjectData>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return JSON.parse(saved) as ProjectData;
      }
    } catch (e) {
      console.warn('Could not load saved layout, using default', e);
    }
    return defaultProjectData as unknown as ProjectData;
  });

  // Active screen and selection
  const [activeScreenId, setActiveScreenId] = useState<string>(
    project.activeScreenId || project.screens[0]?.id || 'launcher'
  );
  const [selectedElementId, setSelectedElementId] = useState<string | null>(null);

  // Undo / Redo history
  const [history, setHistory] = useState<ProjectData[]>([]);
  const [future, setFuture] = useState<ProjectData[]>([]);

  // Canvas settings
  const [zoom, setZoom] = useState<CanvasZoom>('fit');
  const [snapGrid, setSnapGrid] = useState<SnapGridSize>(8);

  // Modals
  const [showExportModal, setShowExportModal] = useState<boolean>(false);
  const [showSimulateModal, setShowSimulateModal] = useState<boolean>(false);
  const [showFlashModal, setShowFlashModal] = useState<boolean>(false);
  const [saveToast, setSaveToast] = useState<string | null>(null);

  // Sync theme class to html
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  // Push history snapshot before mutating
  const pushHistory = (currentProject: ProjectData) => {
    setHistory((prev) => [...prev.slice(-30), JSON.parse(JSON.stringify(currentProject))]);
    setFuture([]);
  };

  const currentScreen =
    project.screens.find((s) => s.id === activeScreenId) || project.screens[0];

  const selectedElement =
    currentScreen?.elements.find((el) => el.id === selectedElementId) || null;

  // Undo
  const handleUndo = () => {
    if (history.length === 0) return;
    const previous = history[history.length - 1];
    setFuture((prev) => [JSON.parse(JSON.stringify(project)), ...prev]);
    setHistory((prev) => prev.slice(0, prev.length - 1));
    setProject(previous);
    if (!previous.screens.some((s) => s.id === activeScreenId)) {
      setActiveScreenId(previous.screens[0]?.id || 'launcher');
      setSelectedElementId(null);
    }
  };

  // Redo
  const handleRedo = () => {
    if (future.length === 0) return;
    const next = future[0];
    setHistory((prev) => [...prev, JSON.parse(JSON.stringify(project))]);
    setFuture((prev) => prev.slice(1));
    setProject(next);
    if (!next.screens.some((s) => s.id === activeScreenId)) {
      setActiveScreenId(next.screens[0]?.id || 'launcher');
      setSelectedElementId(null);
    }
  };

  // Update element properties
  const handleUpdateElement = (id: string, updates: Partial<FocalElement>) => {
    setProject((prev) => {
      const nextScreens = prev.screens.map((scr) => {
        if (scr.id !== activeScreenId) return scr;
        const nextElements = scr.elements.map((el) =>
          el.id === id ? { ...el, ...updates } : el
        );
        return { ...scr, elements: nextElements };
      });
      return { ...prev, screens: nextScreens };
    });
  };

  // Delete element
  const handleDeleteElement = (id: string) => {
    pushHistory(project);
    setProject((prev) => {
      const nextScreens = prev.screens.map((scr) => {
        if (scr.id !== activeScreenId) return scr;
        return {
          ...scr,
          elements: scr.elements.filter((el) => el.id !== id),
        };
      });
      return { ...prev, screens: nextScreens };
    });
    if (selectedElementId === id) {
      setSelectedElementId(null);
    }
  };

  // Duplicate element
  const handleDuplicateElement = (id: string) => {
    const el = currentScreen.elements.find((item) => item.id === id);
    if (!el) return;

    pushHistory(project);
    const randSuffix = Math.random().toString(36).substring(2, 6);
    const newId = `${el.id}_copy_${Date.now().toString().slice(-4)}_${randSuffix}`;
    const newElement: FocalElement = {
      ...el,
      id: newId,
      name: `${el.name} (Copia)`,
      x: Math.min(480 - el.w, el.x + 12),
      y: Math.min(320 - el.h, el.y + 12),
      zIndex: el.zIndex + 1,
    };

    setProject((prev) => {
      const nextScreens = prev.screens.map((scr) => {
        if (scr.id !== activeScreenId) return scr;
        return { ...scr, elements: [...scr.elements, newElement] };
      });
      return { ...prev, screens: nextScreens };
    });
    setSelectedElementId(newId);
  };

  // Add new element from sidebar
  const handleAddElement = (template: Partial<FocalElement>) => {
    pushHistory(project);
    const newId = `elem_${Date.now().toString().slice(-6)}`;
    const newElement: FocalElement = {
      id: newId,
      type: template.type || 'card',
      name: template.name || 'Nuevo Elemento',
      x: 30,
      y: 50,
      w: template.w || 140,
      h: template.h || 60,
      radius: template.radius ?? 14,
      text: template.text || 'Elemento',
      subtext: template.subtext,
      textMode: template.textMode || 'ellipsis',
      fontSize: template.fontSize || 13,
      fontWeight: template.fontWeight || 'semibold',
      accentColor: template.accentColor || '#60A5FA',
      icon: template.icon,
      value: template.value,
      minValue: template.minValue,
      maxValue: template.maxValue,
      unit: template.unit,
      customData: template.customData,
      zIndex: currentScreen.elements.length + 1,
    };

    setProject((prev) => {
      const nextScreens = prev.screens.map((scr) => {
        if (scr.id !== activeScreenId) return scr;
        return { ...scr, elements: [...scr.elements, newElement] };
      });
      return { ...prev, screens: nextScreens };
    });
    setSelectedElementId(newId);
  };

  // Layer order actions
  const handleBringToFront = (id: string) => {
    pushHistory(project);
    setProject((prev) => {
      const scr = prev.screens.find((s) => s.id === activeScreenId);
      if (!scr) return prev;
      const maxZ = Math.max(...scr.elements.map((e) => e.zIndex), 0);
      return {
        ...prev,
        screens: prev.screens.map((s) =>
          s.id === activeScreenId
            ? {
                ...s,
                elements: s.elements.map((e) =>
                  e.id === id ? { ...e, zIndex: maxZ + 1 } : e
                ),
              }
            : s
        ),
      };
    });
  };

  const handleSendToBack = (id: string) => {
    pushHistory(project);
    setProject((prev) => {
      const scr = prev.screens.find((s) => s.id === activeScreenId);
      if (!scr) return prev;
      const minZ = Math.min(...scr.elements.map((e) => e.zIndex), 1);
      return {
        ...prev,
        screens: prev.screens.map((s) =>
          s.id === activeScreenId
            ? {
                ...s,
                elements: s.elements.map((e) =>
                  e.id === id ? { ...e, zIndex: Math.max(0, minZ - 1) } : e
                ),
              }
            : s
        ),
      };
    });
  };

  const handleMoveUp = (id: string) => {
    pushHistory(project);
    setProject((prev) => {
      return {
        ...prev,
        screens: prev.screens.map((s) =>
          s.id === activeScreenId
            ? {
                ...s,
                elements: s.elements.map((e) =>
                  e.id === id ? { ...e, zIndex: e.zIndex + 1 } : e
                ),
              }
            : s
        ),
      };
    });
  };

  const handleMoveDown = (id: string) => {
    pushHistory(project);
    setProject((prev) => {
      return {
        ...prev,
        screens: prev.screens.map((s) =>
          s.id === activeScreenId
            ? {
                ...s,
                elements: s.elements.map((e) =>
                  e.id === id ? { ...e, zIndex: Math.max(0, e.zIndex - 1) } : e
                ),
              }
            : s
        ),
      };
    });
  };

  // Screen management
  const handleAddScreen = (name: string) => {
    pushHistory(project);
    const newId = `screen_${Date.now().toString().slice(-4)}`;
    const newScreen: ScreenLayout = {
      id: newId,
      name,
      description: 'Pantalla personalizada',
      icon: 'shapes',
      elements: [],
    };
    setProject((prev) => ({
      ...prev,
      screens: [...prev.screens, newScreen],
      activeScreenId: newId,
    }));
    setActiveScreenId(newId);
    setSelectedElementId(null);
  };

  const handleDuplicateScreen = (id: string) => {
    const scr = project.screens.find((s) => s.id === id);
    if (!scr) return;

    pushHistory(project);
    const newId = `${scr.id}_copy_${Date.now().toString().slice(-4)}`;
    const duplicated: ScreenLayout = {
      ...JSON.parse(JSON.stringify(scr)),
      id: newId,
      name: `${scr.name} (Copia)`,
    };

    setProject((prev) => ({
      ...prev,
      screens: [...prev.screens, duplicated],
      activeScreenId: newId,
    }));
    setActiveScreenId(newId);
  };

  const handleDeleteScreen = (id: string) => {
    if (project.screens.length <= 1) return;
    pushHistory(project);
    setProject((prev) => {
      const filtered = prev.screens.filter((s) => s.id !== id);
      return {
        ...prev,
        screens: filtered,
        activeScreenId: filtered[0].id,
      };
    });
    setActiveScreenId(project.screens.filter((s) => s.id !== id)[0].id);
    setSelectedElementId(null);
  };

  // Save Layout action
  const handleSaveLayout = async () => {
    const jsonStr = JSON.stringify(project, null, 2);
    localStorage.setItem(STORAGE_KEY, jsonStr);

    // If running in Electron, invoke native save dialog
    if (window.electronAPI?.saveFileDialog) {
      await window.electronAPI.saveFileDialog('screens_layout.json', jsonStr);
    } else {
      // Browser download fallback
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'screens_layout.json';
      a.click();
      URL.revokeObjectURL(url);
    }

    setSaveToast('¡Layout guardado con éxito en screens_layout.json!');
    setTimeout(() => setSaveToast(null), 3000);
  };

  return (
    <div
      className="w-screen h-screen flex flex-col overflow-hidden select-none"
      style={{
        backgroundColor: isDark ? '#0F1115' : '#F5F6F8',
        color: isDark ? '#F9FAFB' : '#111827',
      }}
    >
      {/* Top Action Bar */}
      <TopBar
        screenName={currentScreen?.name || 'Pantalla'}
        isDark={isDark}
        onToggleTheme={() => setIsDark((prev) => !prev)}
        zoom={zoom}
        onChangeZoom={setZoom}
        snapGrid={snapGrid}
        onChangeSnapGrid={setSnapGrid}
        canUndo={history.length > 0}
        canRedo={future.length > 0}
        onUndo={handleUndo}
        onRedo={handleRedo}
        onSaveLayout={handleSaveLayout}
        onExportC={() => setShowExportModal(true)}
        onSimulate={() => setShowSimulateModal(true)}
        onFlashESP32={() => setShowFlashModal(true)}
      />

      {/* Main Workspace (Left Sidebar + Canvas 3:2 + Right Inspector) */}
      <div className="flex-1 flex overflow-hidden relative">
        <LeftSidebar
          screens={project.screens}
          activeScreenId={activeScreenId}
          onSelectScreen={(id) => {
            setActiveScreenId(id);
            setSelectedElementId(null);
          }}
          onAddScreen={handleAddScreen}
          onDuplicateScreen={handleDuplicateScreen}
          onDeleteScreen={handleDeleteScreen}
          onAddElement={handleAddElement}
          selectedElement={selectedElement}
          onUpdateSelectedIcon={(iconName) => {
            if (selectedElementId) {
              handleUpdateElement(selectedElementId, { icon: iconName });
            }
          }}
          isDark={isDark}
        />

        <CanvasViewport
          elements={currentScreen?.elements || []}
          selectedId={selectedElementId}
          onSelectElement={setSelectedElementId}
          onUpdateElement={handleUpdateElement}
          onDeleteElement={handleDeleteElement}
          onDuplicateElement={handleDuplicateElement}
          isDark={isDark}
          zoom={zoom}
          snapGrid={snapGrid}
          onUndo={handleUndo}
          onRedo={handleRedo}
          onDragStart={() => pushHistory(project)}
        />

        <RightInspector
          element={selectedElement}
          onUpdateElement={handleUpdateElement}
          onDeleteElement={handleDeleteElement}
          onDuplicateElement={handleDuplicateElement}
          onBringToFront={handleBringToFront}
          onSendToBack={handleSendToBack}
          onMoveUp={handleMoveUp}
          onMoveDown={handleMoveDown}
          isDark={isDark}
        />
      </div>

      {/* Floating Save Notification Toast */}
      {saveToast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-semibold shadow-2xl z-50 flex items-center gap-2 animate-in fade-in slide-in-from-bottom-4 duration-200">
          <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
          <span>{saveToast}</span>
        </div>
      )}

      {/* Modals */}
      {showExportModal && currentScreen && (
        <ExportCModal
          screen={currentScreen}
          onClose={() => setShowExportModal(false)}
          isDark={isDark}
        />
      )}

      {showSimulateModal && currentScreen && (
        <SimulateModal
          screen={currentScreen}
          onClose={() => setShowSimulateModal(false)}
          isDark={isDark}
        />
      )}

      {showFlashModal && (
        <FlashModal
          onClose={() => setShowFlashModal(false)}
          isDark={isDark}
        />
      )}
    </div>
  );
}
