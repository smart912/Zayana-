"""Builds album.html and wilayat.html: inlines the shared helpers (text, flag, Zayana) from reel.html."""
s = open('reel.html').read()
a = s.index('// ---------- helpers ----------'); b = s.index('// ---------- particles (analytic) ----------')
shared = s[a:b]
ta = shared.index('// ---------- timeline ----------'); tb = shared.index('// ---------- text ----------')
shared = shared[:ta] + shared[tb:]
for name in ('album', 'wilayat'):
    src = open(name + '.src.html').read()
    open(name + '.html', 'w').write(src.replace('/*SHARED*/', shared))
    print(name + '.html built')
