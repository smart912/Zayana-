/* Zayana Desktop: the Electron shell.
 *
 * Based on Khalfan by Ahmed Al Araimi — https://github.com/Ahmed-Al-Araimi/khalfan
 * (the transparent click-through window, the world feed and the tray follow his main.js).
 *
 * One transparent, click-through, always-on-top window over the main screen (1 px shorter than it, so Windows never
 * takes it for a full-screen app). It only takes the mouse while the cursor is on Zayana. She lives in app/pet.js;
 * this file feeds her the cursor, the windows she can stand on, the taskbar and the idle time, and owns the tray and
 * Ctrl+Alt+Z.
 */
'use strict';
const { app, BrowserWindow, screen, ipcMain, Tray, Menu, nativeImage, globalShortcut } = require('electron');
const path = require('path');
const fs = require('fs');

app.commandLine.appendSwitch('disable-features', 'CalculateNativeWinOcclusion');
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
if (!app.requestSingleInstanceLock()) app.quit();

// ---------------------------------------------------------------- log (userData\zayana.log)
const LOG_FILE = path.join(app.getPath('userData'), 'zayana.log');
function log(...a) {
  const line = `${new Date().toISOString()} ${a.map((x) => (typeof x === 'string' ? x : JSON.stringify(x))).join(' ')}\n`;
  try {
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
    if (fs.existsSync(LOG_FILE) && fs.statSync(LOG_FILE).size > 300000) fs.renameSync(LOG_FILE, LOG_FILE + '.old');
    fs.appendFileSync(LOG_FILE, line);
  } catch (e) { /* never let the log stop her */ }
}
process.on('uncaughtException', (e) => log('uncaught', (e && e.stack) || String(e)));
process.on('unhandledRejection', (e) => log('unhandled rejection', (e && e.stack) || String(e)));

let W32 = null;
try { W32 = require('./win32'); } catch (e) { log('win32 bindings failed:', e.message); }

// ---------------------------------------------------------------- settings
const SETTINGS_FILE = () => path.join(app.getPath('userData'), 'settings.json');
const settings = { size: 'medium', sound: true, voice: true, chatty: true, mischief: true, visible: true, name: '' };
function loadSettings() { try { Object.assign(settings, JSON.parse(fs.readFileSync(SETTINGS_FILE(), 'utf8'))); } catch (e) { /* first run */ } }
function saveSettings() { try { fs.mkdirSync(path.dirname(SETTINGS_FILE()), { recursive: true }); fs.writeFileSync(SETTINGS_FILE(), JSON.stringify(settings, null, 2)); } catch (e) { /* ignore */ } }

// ---------------------------------------------------------------- the window
let win = null, tray = null, myHwnd = 0, area = null;
let interactive = false, tracked = 0, hiding = false, busyHidden = false, pageDrag = false, hitBox = null;

function hwndOf(w) { const b = w.getNativeWindowHandle(); return b.length >= 8 ? Number(b.readBigUInt64LE(0)) : b.readUInt32LE(0); }

function placeWindow() {
  const d = screen.getPrimaryDisplay();
  area = { x: d.bounds.x, y: d.bounds.y, w: d.bounds.width, h: d.bounds.height - 1, work: d.workArea, scale: d.scaleFactor };
  if (win) { win.setBounds({ x: area.x, y: area.y, width: area.w, height: area.h }); coverScreen(); }
}
// over the whole main screen, the taskbar too, so she can stand on top of it without being cut off
function coverScreen() {
  if (!win || win.isDestroyed() || !W32 || !myHwnd) return;
  try {
    const d = screen.getPrimaryDisplay();
    const p = screen.dipToScreenRect(null, d.bounds);
    W32.placeOwn(myHwnd, p.x, p.y, Math.floor(d.bounds.width * d.scaleFactor), Math.floor(d.bounds.height * d.scaleFactor) - 1);
  } catch (e) { log('cover failed', e.message); }
}

function createWindow() {
  placeWindow();
  win = new BrowserWindow({
    x: area.x, y: area.y, width: area.w, height: area.h,
    transparent: true, backgroundColor: '#00000000', frame: false, hasShadow: false, thickFrame: false,
    resizable: false, movable: false, minimizable: false, maximizable: false, fullscreenable: false,
    skipTaskbar: true, focusable: false, alwaysOnTop: true, show: false, title: 'Zayana', enableLargerThanScreen: true,
    webPreferences: { preload: path.join(__dirname, 'preload.js'), backgroundThrottling: false, contextIsolation: true, nodeIntegration: false },
  });
  win.setAlwaysOnTop(true, 'screen-saver');
  win.setIgnoreMouseEvents(true, { forward: true });
  win.loadFile(path.join(__dirname, 'app', 'index.html'));
  win.once('ready-to-show', () => {
    const fs0 = fullScreenApp();
    log('ready', { visible: settings.visible, fullScreenApp: fs0 });
    if (settings.visible && !fs0) showWin(); else { busyHidden = !!settings.visible && fs0; win.webContents.send('visible', false); }
  });
  myHwnd = hwndOf(win);
  win.on('closed', () => { win = null; });
  win.on('unresponsive', () => { log('page unresponsive'); setInteractive(false); });
  win.webContents.on('render-process-gone', (e, d) => { log('page crashed', d); setInteractive(false); setTimeout(() => win && !win.isDestroyed() && win.reload(), 1500); });
  win.webContents.on('will-navigate', (e) => e.preventDefault());
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
}

// a full-screen app in front (a game, a video, a presentation): she steps aside
const SHELL = new Set(['Progman', 'WorkerW', 'Shell_TrayWnd', 'Shell_SecondaryTrayWnd', 'Windows.UI.Core.CoreWindow', 'XamlExplorerHostIslandWindow',
  'XamlExplorerHostIslandWindow_WASDK', 'MultitaskingViewFrame', 'ForegroundStaging', 'TopLevelWindowForOverflowXamlIsland', 'NotifyIconOverflowWindow']);
let showAnywayFor = 0;
function fullScreenApp() {
  if (!W32) return false;
  try {
    if (W32.busy()) return true;
    const fg = W32.foreground();
    if (!fg || !fg.rect || fg.iconic || fg.hwnd === myHwnd || SHELL.has(fg.cls) || fg.caption) return false;
    if (fg.hwnd === showAnywayFor) return false;
    const r = toDip(fg.rect);
    return r.x <= 1 && r.y <= 1 && r.x + r.w >= area.w - 1 && r.y + r.h >= area.h;
  } catch (e) { return false; }
}

function setInteractive(on) {
  if (!win || on === interactive) return;
  interactive = on;
  win.setIgnoreMouseEvents(!on, { forward: true });
}
// the safety net: if the page stalls with the mouse taken, give it back as soon as the cursor is away from her
function guardClicks(pt) {
  if (!interactive) return;
  if (W32 && (W32.leftDown() || W32.rightDown())) return;
  const b = hitBox, m = 40, x = pt.x - area.x, y = pt.y - area.y;
  if (!b || x < b.x - m || x > b.x + b.w + m || y < b.y - m || y > b.y + b.h + m) setInteractive(false);
}

// ---------------------------------------------------------------- what she can see
function toDip(r) {
  const d = screen.screenToDipRect(null, { x: r.left, y: r.top, width: r.right - r.left, height: r.bottom - r.top });
  return { x: d.x - area.x, y: d.y - area.y, w: d.width, h: d.height };
}
function subtract(segs, a, b) {
  const out = [];
  for (const [x0, x1] of segs) {
    if (b <= x0 || a >= x1) { out.push([x0, x1]); continue; }
    if (a > x0) out.push([x0, a]);
    if (b < x1) out.push([b, x1]);
  }
  return out;
}
// the visible top edges she can stand on, and the taskbar's top as her floor
function world() {
  const W = area.w, H = area.h, work = area.work;
  const floorY = Math.min(H, work.y + work.height - area.y);
  const ledges = [];
  let fg = null;
  if (W32) {
    let ws = [];
    try { ws = W32.listWindows(new Set([myHwnd])); } catch (e) { ws = []; }
    const occ = [];
    for (const w of ws) {
      const r = toDip(w.rect);
      if (r.x >= W || r.x + r.w <= 0 || r.y >= H || r.y + r.h <= 0) continue;
      if (w.ledge && r.y > 70 && r.y < floorY - 60) {
        let segs = [[Math.max(0, r.x), Math.min(W, r.x + r.w)]];
        for (const o of occ) if (o.y < r.y + 1 && o.y + o.h > r.y - 1) segs = subtract(segs, o.x, o.x + o.w);
        for (const [x0, x1] of segs) if (x1 - x0 >= 70) ledges.push({ hwnd: w.hwnd, x0, x1, y: r.y });
      }
      occ.push(r);
    }
    try { fg = W32.foreground(); } catch (e) { fg = null; }
    if (fg) fg = { hwnd: fg.hwnd, proc: fg.proc, title: (fg.title || '').slice(0, 60) };
  }
  return { W, H, floorY, ledges, fg, idle: W32 ? W32.idleMs() : 0, hour: new Date().getHours() };
}

let paceFast = true, lastSent = '';
function tick() {
  if (!win || win.isDestroyed() || !win.isVisible()) return;
  const pt = screen.getCursorScreenPoint();
  guardClicks(pt);
  let tr = null;
  if (tracked && W32) {
    const r = W32.windowRect(tracked);
    tr = r ? Object.assign({ hwnd: tracked }, toDip(r)) : { hwnd: tracked, gone: true };
  }
  const d = { mx: pt.x - area.x, my: pt.y - area.y, ld: W32 ? W32.leftDown() : false, tr };
  if (interactive && d.ld && !pageDrag) { const b = hitBox; if (!b || d.mx < b.x || d.mx > b.x + b.w || d.my < b.y || d.my > b.y + b.h) setInteractive(false); }
  const key = tr ? '' : `${d.mx},${d.my},${d.ld}`;
  if (key && key === lastSent) return;
  lastSent = key;
  win.webContents.send('tick', d);
}
function tickLoop() { tick(); setTimeout(tickLoop, paceFast || tracked || interactive ? 16 : 33); }
function worldTick() {
  if (!win || win.isDestroyed()) return;
  const busy = fullScreenApp();
  if (busy && !busyHidden && win.isVisible()) { busyHidden = true; hideWin(); }
  else if (!busy && busyHidden) { busyHidden = false; showAnywayFor = 0; if (settings.visible) { showWin(); win.webContents.send('event', { type: 'hello' }); } }
  if (!win.isVisible()) return;
  win.moveTop();
  coverScreen();
  win.webContents.send('world', world());
}
function hideWin() { if (!win) return; win.hide(); setInteractive(false); win.webContents.send('visible', false); }
function showWin() { if (!win) return; win.webContents.send('world', world()); win.webContents.send('visible', true); win.showInactive(); coverScreen(); }

function toggle(force, why = 'toggle') {
  if (!win) return;
  const show = force != null ? force : !(settings.visible && win.isVisible());
  log(show ? 'show' : 'hide', why);
  if (show) {
    settings.visible = true; hiding = false; saveSettings();
    if (busyHidden) { try { showAnywayFor = W32.foreground().hwnd; } catch (e) { showAnywayFor = 0; } busyHidden = false; }
    showWin(); win.webContents.send('event', { type: 'hello' });
  } else if (!hiding) {
    settings.visible = false; saveSettings(); hiding = true;
    win.webContents.send('event', { type: 'bye' });
    setTimeout(() => { if (hiding && win) { hideWin(); hiding = false; } }, 2200);
  }
  buildMenu();
}

// ---------------------------------------------------------------- tray (Arabic)
const sendEv = (ev) => { if (win && settings.visible) win.webContents.send('event', ev); };
function buildMenu() {
  const size = (s, label) => ({ label, type: 'radio', checked: settings.size === s, click: () => { settings.size = s; saveSettings(); push(); } });
  const check = (key, label) => ({ label, type: 'checkbox', checked: !!settings[key], click: (i) => { settings[key] = i.checked; saveSettings(); push(); } });
  const loginOn = app.getLoginItemSettings({ args: app.isPackaged ? [] : [app.getAppPath()] }).openAtLogin;
  const menu = Menu.buildFromTemplate([
    { label: settings.visible ? 'أخفي زيانه' : 'أظهر زيانه', accelerator: 'Ctrl+Alt+Z', click: () => toggle() },
    { label: 'نادي زيانه', enabled: settings.visible, click: () => sendEv({ type: 'call' }) },
    { label: 'خليها تسولف', enabled: settings.visible, click: () => sendEv({ type: 'talk' }) },
    { label: 'خليها ترقص', enabled: settings.visible, click: () => sendEv({ type: 'dance' }) },
    { label: 'اسمك…', click: () => askName() },
    { type: 'separator' },
    size('small', 'صغيرة'), size('medium', 'وسط'), size('large', 'كبيرة'),
    { type: 'separator' },
    check('voice', 'تتكلم بالصوت'),
    check('sound', 'أصوات الحركة'),
    check('chatty', 'تسولف من نفسها'),
    check('mischief', 'تلحق الماوس'),
    { label: 'تشتغل مع الويندوز', type: 'checkbox', checked: loginOn, click: (i) => {
      app.setLoginItemSettings({ openAtLogin: i.checked, path: process.execPath, args: app.isPackaged ? [] : [app.getAppPath()] });
      buildMenu();
    } },
    { type: 'separator' },
    { label: 'Based on Khalfan by Ahmed Al Araimi', enabled: false },
    { label: 'خروج', click: () => { app.isQuitting = true; app.quit(); } },
  ]);
  if (tray) tray.setContextMenu(menu);
  return menu;
}
function push() { if (win) win.webContents.send('settings', settings); buildMenu(); }

// a small window to type your name in (her own window never takes the keyboard)
let nameWin = null;
function askName() {
  if (nameWin && !nameWin.isDestroyed()) { nameWin.focus(); return; }
  nameWin = new BrowserWindow({
    width: 380, height: 250, resizable: false, minimizable: false, maximizable: false, alwaysOnTop: true, title: 'زيانه',
    icon: path.join(__dirname, 'zayana.ico'), autoHideMenuBar: true, backgroundColor: '#fffaf0',
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false },
  });
  nameWin.setMenu(null);
  nameWin.loadFile(path.join(__dirname, 'app', 'name.html'));
  nameWin.on('closed', () => { nameWin = null; });
}

// ---------------------------------------------------------------- IPC
ipcMain.on('interactive', (e, on, box, dragging) => { hitBox = box || null; pageDrag = !!dragging; setInteractive(!!on); });
ipcMain.on('track', (e, hwnd) => { tracked = Number(hwnd) || 0; });
ipcMain.on('pace', (e, fast) => { paceFast = !!fast; });
ipcMain.on('menu', () => { const m = buildMenu(); if (win) m.popup({ window: win }); });
ipcMain.on('gone', () => { if (hiding && win) { hideWin(); hiding = false; } });
ipcMain.on('set-name', (e, name) => {
  settings.name = String(name || '').trim().slice(0, 24); saveSettings(); push();
  sendEv({ type: 'named' });
  if (nameWin && !nameWin.isDestroyed()) nameWin.close();
});
ipcMain.handle('settings', () => settings);
ipcMain.handle('first-world', () => world());
ipcMain.on('log', (e, ...a) => log('[pet]', ...a));

// ---------------------------------------------------------------- start
app.whenReady().then(() => {
  loadSettings();
  log('start', { electron: process.versions.electron, display: screen.getPrimaryDisplay().bounds, settings });
  createWindow();
  tray = new Tray(nativeImage.createFromPath(path.join(__dirname, 'zayana.ico')));
  tray.setToolTip('زيانه');
  tray.on('click', () => toggle(undefined, 'tray click'));
  buildMenu();
  if (!globalShortcut.register('Control+Alt+Z', () => toggle(undefined, 'Ctrl+Alt+Z'))) log('Ctrl+Alt+Z is taken by another app');
  tickLoop();
  setInterval(worldTick, 250);
  if (!settings.name && !settings.askedName) { settings.askedName = true; saveSettings(); setTimeout(askName, 4000); }
  screen.on('display-metrics-changed', placeWindow);
  screen.on('display-added', placeWindow);
  screen.on('display-removed', placeWindow);
});
app.on('second-instance', () => toggle(true, 'started again'));
app.on('window-all-closed', () => app.quit());
app.on('will-quit', () => globalShortcut.unregisterAll());
