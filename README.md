# زيانه · Zayana

<p align="center"><img src="zayana.svg" width="280" alt="Zayana"></p>

زيانه شخصية كرتونية عمانية تعيش داخل Claude Code، لابسة الزي العماني التقليدي:
لحاف أخضر مورّد بحواف ذهبية وشراريب ملونة، دشداشة حمراء منقوشة بالذهبي والأخضر
مع صدرية مطرزة وذيل أزرق، سروال أخضر بأطراف مطرزة، تيكا وقلادة ذهب، وحذاء فضي.

## وين تلقاها في Claude Code؟
| المكان | الملف |
|---|---|
| ترحيب عند بداية كل جلسة (SessionStart hook) | `scripts/zayana.sh` |
| شريط الحالة تحت | `scripts/zayana-statusline.sh` |
| أسلوب الرد (Claude يتكلم بشخصية زيانه) | `.claude/output-styles/zayana.md` |
| الرسمة | `zayana.svg` / `zayana.png` |

كل شي مفعّل من `.claude/settings.json`. افتح Claude Code داخل هذا المجلد وبتطلع لك زيانه.
تقدر تغيّر الأسلوب أو توقفه بأمر `/config` → Output style.

جرّبها في الطرفية: `bash scripts/zayana.sh`

## أنيميشن وملصقات
- `animation/zayana-wave.gif` / `.mp4` / `.svg` — زيانه تلوّح بيدها، ترمش، والشراريب تتمايل، مع فقاعة "هلا والله!".
- `stickers/` — ٤ ملصقات بحجم 512×512 وخلفية شفافة (مناسبة لواتساب): هلا والله، تسلم يا الغالي، صباح الخير، عيدكم مبارك.

## زيانه تتنطط داخل Claude Code (Mod)
في `mod/zayana/` إضافة تخلي زيانه تتنطط فوق مربع الكتابة، وفقاعتها تتغير حسب شغل Claude
(تدوّر في الملفات 🔍، تشغّل أوامر 💻، تكتب كود ✍️، وتقول "خلصت!" لما يخلص).
- `/zayana` ترجعها · `/zayana hide` تخفيها · `/zayana pane` نافذة كبيرة
- للتجربة محلياً: `claude --plugin-dir mod/zayana`

### تثبيت زيانه في أي جلسة Claude Code
الإعداد في `.claude/settings.json` يفعّلها تلقائياً لما تفتح هذا المشروع. ولو ما طلعت، اكتب:

```
/plugin install zayana --marketplace smart912/Zayana-
```
