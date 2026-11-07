"""Builds album.html: inlines the shared helpers (text, flag, Zayana) from reel.html."""
s = open('reel.html').read()
a = s.index('// ---------- helpers ----------'); b = s.index('// ---------- particles (analytic) ----------')
shared = s[a:b]
ta = shared.index('// ---------- timeline ----------'); tb = shared.index('// ---------- text ----------')
shared = shared[:ta] + shared[tb:]
src = open('album.src.html').read()
open('album.html', 'w').write(src.replace('/*SHARED*/', shared))
print('album.html built')
