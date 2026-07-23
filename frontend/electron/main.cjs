const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonDaemonProcess = null;

const isDev = process.env.NODE_ENV === 'development';

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        title: 'AutoJob AI Ecosystem',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    if (isDev) {
        mainWindow.loadURL('http://localhost:5173');
        mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
    }

    // Open external links in default browser
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });
}

function spawnPythonDaemon() {
    console.log('[Electron] Spawning Python SPrav MoE Daemon in the background...');
    const venvPath = path.join(__dirname, '../../.venv/Scripts/python.exe');
    const scriptPath = path.join(__dirname, '../../engine/daemon.py');

    // Spawn the daemon (which also starts the API if we integrated it, 
    // or we can spawn the API separately if needed).
    pythonDaemonProcess = spawn(venvPath, ['-m', 'engine.daemon'], {
        cwd: path.join(__dirname, '../../'),
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });

    pythonDaemonProcess.stdout.on('data', (data) => {
        console.log(`[Python Daemon] ${data.toString()}`);
    });

    pythonDaemonProcess.stderr.on('data', (data) => {
        console.error(`[Python Daemon Error] ${data.toString()}`);
    });

    pythonDaemonProcess.on('close', (code) => {
        console.log(`[Python Daemon] Exited with code ${code}`);
    });
}

function spawnFastAPI() {
    console.log('[Electron] Spawning FastAPI Backend...');
    const venvPath = path.join(__dirname, '../../.venv/Scripts/uvicorn.exe');
    
    const apiProcess = spawn(venvPath, ['api:app', '--host', '127.0.0.1', '--port', '8000'], {
        cwd: path.join(__dirname, '../../'),
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });

    apiProcess.stdout.on('data', (data) => {
        console.log(`[FastAPI] ${data.toString()}`);
    });

    // Cleanup processes on exit
    app.on('will-quit', () => {
        if (apiProcess) apiProcess.kill();
        if (pythonDaemonProcess) pythonDaemonProcess.kill();
        
        // Hard fallback for Windows orphaned processes
        spawn('taskkill', ['/F', '/IM', 'python.exe']);
    });
}

app.whenReady().then(() => {
    createWindow();
    
    // Boot up the native AI engine services!
    spawnFastAPI();
    spawnPythonDaemon();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    // In a real desktop app, we might just hide the window to tray.
    // For now, we close everything.
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('will-quit', () => {
    console.log('[Electron] Shutting down background processes...');
    if (pythonDaemonProcess) {
        pythonDaemonProcess.kill();
    }
});
