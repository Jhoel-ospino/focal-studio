const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  saveFileDialog: (defaultName, content) => ipcRenderer.invoke('save-file-dialog', { defaultName, content }),
  isElectron: true,
});
