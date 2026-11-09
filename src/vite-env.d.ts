/// <reference types="vite/client" />

interface Window {
  electronAPI?: {
    saveFileDialog: (defaultName: string, content: string) => Promise<{ canceled: boolean; filePath?: string }>;
    isElectron: boolean;
  };
}
