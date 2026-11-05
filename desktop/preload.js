'use strict';
// Based on Khalfan by Ahmed Al Araimi — https://github.com/Ahmed-Al-Araimi/khalfan (preload.js)
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('desk', {
  onTick: (fn) => ipcRenderer.on('tick', (e, d) => fn(d)),
  onWorld: (fn) => ipcRenderer.on('world', (e, d) => fn(d)),
  onEvent: (fn) => ipcRenderer.on('event', (e, d) => fn(d)),
  onSettings: (fn) => ipcRenderer.on('settings', (e, d) => fn(d)),
  onVisible: (fn) => ipcRenderer.on('visible', (e, d) => fn(d)),
  settings: () => ipcRenderer.invoke('settings'),
  firstWorld: () => ipcRenderer.invoke('first-world'),
  interactive: (on, box, dragging) => ipcRenderer.send('interactive', on, box, dragging),
  track: (hwnd) => ipcRenderer.send('track', hwnd || 0),
  pace: (fast) => ipcRenderer.send('pace', !!fast),
  menu: () => ipcRenderer.send('menu'),
  gone: () => ipcRenderer.send('gone'),
  setName: (name) => ipcRenderer.send('set-name', name),
  log: (...a) => ipcRenderer.send('log', ...a),
});
