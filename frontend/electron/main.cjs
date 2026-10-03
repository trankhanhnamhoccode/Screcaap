const { app, BrowserWindow, Menu, dialog } = require('electron');
const path = require('node:path');

function createWindow() {
  const window = new BrowserWindow({
    title: 'Screcaap',
    width: 1180,
    height: 880,
    minWidth: 480,
    minHeight: 600,
    backgroundColor: '#f6f7f9',
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  });
  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  window.webContents.on('will-navigate', event => event.preventDefault());
  window.webContents.session.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  window.webContents.session.setPermissionCheckHandler(() => false);
  window.once('ready-to-show', () => window.show());
  window.loadFile(path.join(__dirname, '../dist/index.html')).catch(() => {
    dialog.showErrorBox('Unable to open Screcaap', 'The dashboard could not be loaded. Rebuild or download a fresh copy of the app.');
    app.quit();
  });
}

app.whenReady().then(() => {
  Menu.setApplicationMenu(null);
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
