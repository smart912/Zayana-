// Renders reel.html frame-by-frame into an MP4 (needs Playwright + ffmpeg).
// usage: node render.js [out.mp4] [--frames 0,60,120 (stills only)]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const args = process.argv.slice(2);
  const stillsIdx = args.indexOf('--stills');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  await page.goto('file://' + path.join(__dirname, 'reel.html'));
  await page.evaluate(() => window.ready);
  const { DURATION, FPS } = await page.evaluate(() => window.META);
  const grab = async t => Buffer.from(await page.evaluate(t => { render(t); return document.getElementById('c').toDataURL('image/jpeg', .95).split(',')[1]; }, t), 'base64');
  if (stillsIdx >= 0) {
    const fs = require('fs'); const dir = args[stillsIdx + 2] || '.';
    for (const t of args[stillsIdx + 1].split(',').map(Number)) fs.writeFileSync(path.join(dir, `still-${t.toFixed(2)}.jpg`), await grab(t));
    await browser.close(); return;
  }
  const out = args[0] || 'zayana-national-day.mp4';
  const audio = path.join(__dirname, 'audio.wav');
  const ff = spawn('ffmpeg', ['-y', '-framerate', String(FPS), '-f', 'image2pipe', '-c:v', 'mjpeg', '-i', '-', '-i', audio,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-r', String(FPS),
    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.round(DURATION * FPS);
  for (let i = 0; i < N; i++) {
    const buf = await grab(i / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) console.log(`frame ${i}/${N}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})();
