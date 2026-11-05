/* Zayana Desktop: Zayana herself.
 *
 * She walks along the top of your taskbar, jumps onto your windows and rides them as they move, can be picked up
 * and thrown, waves, dances, naps when you are away, and chats in little Arabic bubbles (and out loud, if Windows
 * has an Arabic voice). Positions are in DIP over the main screen; (x, y) is the point between her feet.
 *
 * The window feed and the click-through pattern follow Khalfan by Ahmed Al Araimi —
 * https://github.com/Ahmed-Al-Araimi/khalfan
 */
'use strict';
(() => {
  const desk = window.desk;
  const $ = (id) => document.getElementById(id);
  const el = $('z'), inner = $('inner'), flip = $('flip'), bubbleEl = $('bubble'), zzz = $('zzz');
  flip.innerHTML = window.ZAYANA_SVG;

  const G = 2200;                        // gravity, px/s²
  const SIZES = { small: 120, medium: 160, large: 210 };
  const ASPECT = 250 / 515;

  let S = { size: 'medium', sound: true, voice: true, chatty: true, mischief: true, name: '' };
  let W = { W: innerWidth, H: innerHeight, floorY: innerHeight - 48, ledges: [], fg: null, idle: 0, hour: 12 };
  let mouse = { x: -999, y: -999, ld: false };
  let visible = false;

  const z = {
    x: 200, y: -200, vx: 0, vy: 0, h: 160, w: 78,
    state: 'fall',                     // fall | idle | walk | drag | sleep | dance
    surface: null,                     // { kind: 'floor' } | { kind: 'ledge', hwnd, x0, x1 }
    face: 1, target: 0, until: 0, next: 0,
  };

  // ---------------------------------------------------------------- words
  const nm = () => (S.name ? ' يا ' + S.name : '');
  const pick = (a) => a[Math.floor(Math.random() * a.length)];
  function greeting() {
    const h = new Date().getHours();
    if (h >= 4 && h < 12) return 'صباح الخير' + nm() + '! ☀️';
    if (h >= 12 && h < 16) return 'مرحبا' + nm() + '! الجو حار، اشرب ماي 💧';
    if (h >= 16 && h < 20) return 'مساء الخير' + nm() + '! 🌇';
    if (h >= 20) return 'مساء النور' + nm() + '! 🌙';
    return 'الوقت متأخر' + nm() + '، لا تسهر وايد 😴';
  }
  const CHAT = [
    () => 'تبي قهوة عُمانية؟ ☕', () => 'لا تنسى تشرب ماي 💧', () => 'قوم تمشّى شوي 🚶',
    () => 'ما شاء الله عليك، شغلك زين!', () => 'يلا كمّل' + nm() + '، باقي شوي! 💪', () => 'تبي تمر؟ 🌴',
    () => 'ريّح عيونك دقيقة 👀', () => 'اللبان العُماني من ظفار 🌿', () => 'قلعة نزوى أكبر قلعة في عُمان 🏰',
    () => 'الجبل الأخضر حلو في الشتا ❄️', () => 'سوق مطرح فيه كل شي 🛍️', () => 'عاشت إيدك' + nm() + '!',
    () => 'أنا زيانه، وأنت؟ 🧕', () => 'خلنا نرقص؟ 💃',
  ];
  const CLICK = ['هههه تدغدغني! 😆', 'هلا والله!', 'وش تبي؟ 😄', 'يلا نلعب!', 'حياك الله' + '!'];
  const THROWN = ['وييي! 🎢', 'بشويش علي! 😵', 'آآآي!'];
  const APPS = [
    [/^(chrome|msedge|firefox|brave|opera)\.exe$/, 'تتصفح؟ لا تطوّل 🌐'],
    [/^code\.exe$/, 'يلا نبرمج! 💻'], [/^winword\.exe$/, 'تكتب شي حلو؟ ✍️'], [/^excel\.exe$/, 'أرقام وجداول 📊'],
    [/^powerpnt\.exe$/, 'عرض تقديمي؟ بالتوفيق! 🎤'], [/^claude\.exe$/, 'سلّم لي على Claude 🧕'],
    [/whatsapp/, 'سلّم على الأهل 📱'], [/^spotify\.exe$/, 'شغّل شي حلو 🎵'], [/^explorer\.exe$/, 'تدوّر على ملف؟ 📁'],
  ];

  // ---------------------------------------------------------------- voice and little sounds
  let voice = null;
  function pickVoice() {
    const vs = (window.speechSynthesis ? speechSynthesis.getVoices() : []).filter((v) => /^ar/i.test(v.lang));
    voice = vs.find((v) => /ar-om/i.test(v.lang)) || vs.find((v) => /hoda|laila|salma|zariyah|fatima|aysha|female/i.test(v.name)) || vs[0] || null;
  }
  if (window.speechSynthesis) { pickVoice(); speechSynthesis.onvoiceschanged = pickVoice; }
  let mouthTimer = 0;
  function speak(text) {
    if (!S.voice || !voice) return;
    try {
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text.replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}]/gu, ''));
      u.voice = voice; u.lang = voice.lang; u.rate = 1; u.pitch = 1.3;
      u.onstart = () => { clearInterval(mouthTimer); mouthTimer = setInterval(() => el.classList.toggle('mouth'), 140); };
      u.onend = u.onerror = () => { clearInterval(mouthTimer); el.classList.remove('mouth'); };
      speechSynthesis.speak(u);
    } catch (e) { /* no voice, just the bubble */ }
  }
  let ac = null;
  function boop(freqs, dur = 0.09) {
    if (!S.sound) return;
    try {
      ac = ac || new AudioContext();
      freqs.forEach((f, i) => {
        const o = ac.createOscillator(), g = ac.createGain(), t = ac.currentTime + i * dur;
        o.type = 'sine'; o.frequency.value = f;
        g.gain.setValueAtTime(0.08, t); g.gain.exponentialRampToValueAtTime(0.001, t + dur * 1.8);
        o.connect(g).connect(ac.destination); o.start(t); o.stop(t + dur * 2);
      });
    } catch (e) { /* silent */ }
  }

  let bubbleUntil = 0;
  function say(text, ms = 3500, aloud = true) {
    bubbleEl.textContent = text;
    bubbleEl.hidden = false;
    bubbleUntil = performance.now() + ms;
    if (aloud) speak(text);
  }

  // ---------------------------------------------------------------- body
  function setSize() {
    z.h = SIZES[S.size] || 160; z.w = Math.round(z.h * ASPECT);
    el.style.width = z.w + 'px'; el.style.height = z.h + 'px';
  }
  function setState(s) {
    z.state = s;
    el.classList.toggle('walk', s === 'walk');
    el.classList.toggle('idle', s === 'idle');
    el.classList.toggle('air', s === 'fall');
    el.classList.toggle('drag', s === 'drag');
    el.classList.toggle('sleep', s === 'sleep');
    el.classList.toggle('dance', s === 'dance');
    zzz.hidden = s !== 'sleep';
    desk.pace(s !== 'idle' && s !== 'sleep');
  }
  function flash(cls, ms) { el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); setTimeout(() => el.classList.remove(cls), ms); }
  function setFace(d) { if (d) { z.face = d > 0 ? 1 : -1; flip.classList.toggle('left', z.face < 0); } }

  function leaveSurface() { z.surface = null; desk.track(0); }
  function landOn(surface, y) {
    const hard = z.vy > 1100;
    z.y = y; z.vy = 0; z.vx = 0; z.surface = surface;
    desk.track(surface.kind === 'ledge' ? surface.hwnd : 0);
    flash('land', 360);
    boop(hard ? [180, 120] : [260]);
    if (hard) say(pick(['آي! 😵', 'آخ!', 'وصلت بالسلامة 😅']), 2000);
    setState('idle'); z.next = now() + 700 + Math.random() * 1200;
  }

  function jumpTo(tx, ty) {
    const T = 0.75 + Math.min(0.5, Math.abs(tx - z.x) / 1400);
    z.vx = (tx - z.x) / T;
    z.vy = (ty - z.y - 0.5 * G * T * T) / T;
    setFace(z.vx);
    leaveSurface(); setState('fall'); boop([420, 620]);
  }

  // ---------------------------------------------------------------- the brain
  const now = () => performance.now();
  function surfaceRange() {
    if (z.surface && z.surface.kind === 'ledge') return [z.surface.x0 + z.w / 2, z.surface.x1 - z.w / 2];
    return [z.w / 2 + 4, W.W - z.w / 2 - 4];
  }
  function decide() {
    const t = now(), [a, b] = surfaceRange();
    const onLedge = z.surface && z.surface.kind === 'ledge';
    const r = Math.random();
    if (S.mischief && r < 0.12 && !onLedge && mouse.y > W.floorY - 260 && mouse.x > 0) {
      z.target = Math.max(a, Math.min(b, mouse.x)); setState('walk'); say(pick(['بلحقك! 😄', 'وين رايح؟ 🏃‍♀️']), 2000); return;
    }
    if (r < 0.5) { z.target = a + Math.random() * (b - a); setState('walk'); return; }
    if (r < 0.62 && W.ledges.length) {
      const options = W.ledges.filter((l) => Math.abs((l.x0 + l.x1) / 2 - z.x) < 700 && z.y - l.y < 520 && z.y - l.y > -400 && !(onLedge && l.hwnd === z.surface.hwnd));
      if (options.length) {
        const l = pick(options);
        const tx = Math.max(l.x0 + z.w / 2 + 6, Math.min(l.x1 - z.w / 2 - 6, l.x0 + Math.random() * (l.x1 - l.x0)));
        jumpTo(tx, l.y); return;
      }
    }
    if (r < 0.7 && onLedge) { jumpTo(Math.max(a, Math.min(b, z.x + (Math.random() - 0.5) * 300)), W.floorY); return; }
    if (r < 0.8 && S.chatty) { say(pick(CHAT)()); flash('wave', 2200); z.next = t + 3500; return; }
    if (r < 0.85) { dance(); return; }
    setState('idle'); z.next = t + 1500 + Math.random() * 3500;
  }
  function dance() { setState('dance'); say(pick(['💃 يلا نرقص!', 'لالالا 🎶', 'رقصة عُمانية! 🥁']), 2600); z.until = now() + 3200; }

  // ---------------------------------------------------------------- the mouse: hover, pick up, throw, click
  let drag = null, interactiveOn = false, lastBoxSent = 0;
  function box() { return { x: z.x - z.w / 2 - 6, y: z.y - z.h - 6, w: z.w + 12, h: z.h + 12 }; }
  function overHer(mx, my) { const b = box(); return mx >= b.x && mx <= b.x + b.w && my >= b.y && my <= b.y + b.h; }
  function updateInteractive() {
    const on = !!drag || overHer(mouse.x, mouse.y);
    const t = now();
    if (on !== interactiveOn || (on && t - lastBoxSent > 100)) {
      interactiveOn = on; lastBoxSent = t;
      desk.interactive(on, box(), !!drag);
    }
  }
  el.addEventListener('pointerdown', (e) => {
    if (e.button === 2) return;
    e.preventDefault();
    drag = { t0: now(), sx: mouse.x, sy: mouse.y, ox: z.x - mouse.x, oy: z.y - mouse.y, moved: false, hist: [] };
    if (z.state === 'sleep') say('صح النوم! 😴', 1800);
  });
  window.addEventListener('pointerup', () => { if (drag) { mouse.ld = false; release(); } });
  el.addEventListener('contextmenu', (e) => { e.preventDefault(); desk.menu(); });

  function onMouse(d) {
    mouse.x = d.mx; mouse.y = d.my;
    const wasDown = mouse.ld; mouse.ld = d.ld;
    if (drag) {
      const dist = Math.hypot(mouse.x - drag.sx, mouse.y - drag.sy);
      if (!drag.moved && dist > 6) { drag.moved = true; leaveSurface(); setState('drag'); el.classList.add('oh'); say(pick(['وين ماخذني؟ 😮', 'نزّلني! 😆', 'أطير! 🕊️']), 1800); }
      if (drag.moved) {
        z.x = mouse.x + drag.ox; z.y = mouse.y + drag.oy;
        drag.hist.push({ t: now(), x: z.x, y: z.y }); if (drag.hist.length > 6) drag.hist.shift();
      }
      if (wasDown && !mouse.ld || (!mouse.ld && now() - drag.t0 > 80)) release();
    }
    // riding the window under her feet
    if (z.surface && z.surface.kind === 'ledge' && d.tr && d.tr.hwnd === z.surface.hwnd) {
      if (d.tr.gone || d.tr.x > z.x || d.tr.x + d.tr.w < z.x) { leaveSurface(); setState('fall'); say(pick(['وين راحت النافذة؟! 😱', 'طييييح!']), 1800); }
      else { const dx = d.tr.x - z.surface.x0; z.x += dx; z.surface.x0 += dx; z.surface.x1 += dx; z.y = d.tr.y; }
    }
  }
  function release() {
    const dr = drag; drag = null; el.classList.remove('oh');
    if (!dr.moved) { // a click
      flash('wave', 2200); boop([520, 780]);
      say(pick(CLICK)); if (z.state === 'sleep') setState('idle');
      z.next = now() + 2500; return;
    }
    const h = dr.hist, a = h[0], b = h[h.length - 1];
    const dt = b && a && b.t > a.t ? (b.t - a.t) / 1000 : 0;
    z.vx = dt ? Math.max(-2600, Math.min(2600, (b.x - a.x) / dt)) : 0;
    z.vy = dt ? Math.max(-2600, Math.min(2600, (b.y - a.y) / dt)) : 0;
    setState('fall');
    if (Math.hypot(z.vx, z.vy) > 900) say(pick(THROWN), 1800);
  }

  // ---------------------------------------------------------------- the loop
  let last = 0, lastFg = '', lastAppTalk = 0, lastBlink = 0;
  function frame(t) {
    if (!visible) { last = 0; return; }
    const dt = Math.min(0.05, last ? (t - last) / 1000 : 0.016); last = t;
    const [a, b] = surfaceRange();

    if (z.state === 'fall') {
      const py = z.y;
      z.vy += G * dt; z.x += z.vx * dt; z.y += z.vy * dt;
      if (z.x < z.w / 2) { z.x = z.w / 2; z.vx = -z.vx * 0.5; }
      if (z.x > W.W - z.w / 2) { z.x = W.W - z.w / 2; z.vx = -z.vx * 0.5; }
      if (z.y < z.h * 0.6 && z.vy < 0) { z.vy *= 0.5; }                       // the top of the screen
      setFace(z.vx);
      if (z.vy > 0) {
        let best = null;
        for (const l of W.ledges) if (py <= l.y + 1 && z.y >= l.y && z.x > l.x0 + 10 && z.x < l.x1 - 10 && (!best || l.y < best.y)) best = l;
        if (best) landOn({ kind: 'ledge', hwnd: best.hwnd, x0: best.x0, x1: best.x1 }, best.y);
        else if (z.y >= W.floorY) landOn({ kind: 'floor' }, W.floorY);
      }
    } else if (z.state === 'walk') {
      const d = z.target - z.x, step = 70 * dt * (z.h / 160);
      setFace(d);
      if (Math.abs(d) <= step) { z.x = z.target; setState('idle'); z.next = t + 800 + Math.random() * 2500; }
      else z.x += Math.sign(d) * step;
      if (z.surface && z.surface.kind === 'floor') z.y = W.floorY;
    } else if (z.state === 'dance') {
      if (t > z.until) { setState('idle'); z.next = t + 1200; }
    } else if (z.state === 'idle') {
      if (z.surface && z.surface.kind === 'floor') z.y = W.floorY;
      z.x = Math.max(a, Math.min(b, z.x));
      if (W.idle > 180000) { setState('sleep'); say('بنام شوي... 😴', 2500, false); }
      else if (t > z.next) decide();
    } else if (z.state === 'sleep') {
      if (z.surface && z.surface.kind === 'floor') z.y = W.floorY;
      if (W.idle < 3000) { setState('idle'); say('هلا' + nm() + '! رجعت؟ 🧕'); flash('wave', 2200); z.next = t + 3000; }
    }

    // blink now and then
    if (z.state !== 'sleep' && t - lastBlink > 3200 + Math.random() * 2000) { lastBlink = t; el.classList.add('blink'); setTimeout(() => el.classList.remove('blink'), 140); }
    if (!bubbleEl.hidden && t > bubbleUntil) bubbleEl.hidden = true;

    el.style.transform = `translate(${Math.round(z.x - z.w / 2)}px, ${Math.round(z.y - z.h)}px)`;
    updateInteractive();
    requestAnimationFrame(frame);
  }

  // she notices the app you switch to (now and then)
  function noticeApp() {
    const p = W.fg && W.fg.proc;
    if (!p || p === lastFg) return;
    lastFg = p;
    if (!S.chatty || z.state === 'sleep' || now() - lastAppTalk < 90000 || Math.random() < 0.5) return;
    const hit = APPS.find(([re]) => re.test(p));
    if (hit) { lastAppTalk = now(); say(hit[1]); }
  }

  // ---------------------------------------------------------------- wiring
  desk.onTick(onMouse);
  desk.onWorld((w) => { W = w; noticeApp(); if (z.surface && z.surface.kind === 'floor' && z.state !== 'fall') z.y = W.floorY; });
  desk.onSettings((s) => { S = Object.assign(S, s); setSize(); });
  desk.onVisible((v) => {
    const was = visible; visible = !!v; el.hidden = !visible;
    if (visible && !was) requestAnimationFrame(frame);
    if (!visible) { desk.interactive(false, null, false); interactiveOn = false; }
  });
  desk.onEvent((ev) => {
    if (ev.type === 'hello') { say(greeting()); flash('wave', 2200); }
    if (ev.type === 'bye') { say('مع السلامة' + nm() + '! 👋'); flash('wave', 2200); setTimeout(() => desk.gone(), 1600); }
    if (ev.type === 'call') { z.target = Math.max(z.w, Math.min(W.W - z.w, mouse.x)); if (z.surface) { setState('walk'); say('جايتك! 🏃‍♀️', 2000); } }
    if (ev.type === 'talk') { if (z.state === 'sleep') setState('idle'); say(pick(CHAT)()); flash('wave', 2200); }
    if (ev.type === 'dance') { if (z.surface) dance(); }
    if (ev.type === 'named') { say('تشرفنا' + nm() + '! 🧕💚'); flash('wave', 2200); }
  });

  (async () => {
    try { S = Object.assign(S, await desk.settings()); } catch (e) { /* defaults */ }
    try { W = await desk.firstWorld(); } catch (e) { /* defaults */ }
    setSize();
    z.x = W.W * (0.25 + Math.random() * 0.5); z.y = -z.h; setState('fall');
    setTimeout(() => say(S.name ? greeting() : 'هلا والله! أنا زيانه 🧕 اضغط علي يمين وقولي اسمك'), 900);
  })();
})();
