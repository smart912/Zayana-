# ملخص مشروع فيديو العيد الوطني العُماني

هذا الملف ملخص لمحادثة سابقة. المطلوب منك (Claude Code مع متصفح Chrome) أن تفتح **Google Flow** وتولّد صور المشاهد ثم مقاطعها، حسب التفاصيل تحت.

## الهدف

فيديو قصير للعيد الوطني العُماني، طوله ٣٠–٤٠ ثانية، مكوّن من ١٢ مشهد، كل مشهد ٢–٤ ثواني.

الفكرة مأخوذة من فيديو لليوم الوطني السعودي بأسلوب كولاج الورق: يبدأ بخبر واحد صغير، ثم تكبر القصة حتى تصير الوطن كله، ويختم بعنوان العيد ورقمه. نريد نفس الفكرة والأسلوب، لكن بقصة ورموز عُمانية وبصياغة خاصة بنا، لا نسخة حرفية من الفيديو الأصلي.

## المواصفات

- المقاس: ١٦:٩ (1920×1080)، ونفس المقاس لكل المشاهد.
- نفس عدد الإطارات لكل المقاطع (30fps إن أمكن).
- بدون صوت من أداة التوليد. الموسيقى تُضاف لاحقاً في المونتاج.
- **لا تكتب أي نص عربي داخل الصورة أو المقطع.** أدوات التوليد تخربط الحروف العربية. اترك مساحة فارغة للعنوان، والنصوص تُركّب في المونتاج.

## طريقة العمل في Flow

1. افتح Google Flow في Chrome. صاحبة الحساب تسجّل الدخول بنفسها إن طُلب.
2. **الصور أولاً:** ولّد صورة ثابتة لكل مشهد من البرومتات تحت (البرومت الأساسي + برومت المشهد).
3. اعرض الصور على صاحبة المشروع وانتظر موافقتها. أعد توليد أي مشهد لا يعجبها.
4. **ثم المقاطع:** حوّل كل صورة معتمدة إلى مقطع (image-to-video) باستخدام برومت الحركة الخاص بالمشهد.
5. نزّل المقاطع وسمّها `01.mp4` إلى `12.mp4` بترتيب المشاهد.

**قبل أي توليد يصرف رصيداً، أخبر صاحبة المشروع بالتكلفة وانتظر موافقتها.**

## البرومت الأساسي (يُلصق في بداية كل مشهد)

```
Paper collage animation, handmade cut-paper style, vintage Omani newspaper and old manuscript textures, deep teal-green textured background, torn paper edges, layered paper cutouts with soft shadows, black-and-white photo cutouts of Omani forts and mountains, decorative ribbons with Omani embroidery patterns in red, white and green, warm cinematic lighting, 16:9, high detail, no text, no letters, no watermark
```

## المشاهد

لكل مشهد: النص العربي (يُضاف في المونتاج فقط)، برومت الصورة، وبرومت الحركة.

### 01 — «كانت رسالة واحدة…»
- الصورة: `A single old rolled Arabic manuscript lying on a deep teal paper background, wax seal, Omani embroidery ribbon beside it, empty space on the right for title`
- الحركة: `Slow push-in toward the manuscript, ribbon gently moving`

### 02 — «قامت دولة… باسم عُمان»
- الصورة: `The old manuscript unrolled, revealing a paper-cutout landscape behind it: Nizwa fort round tower, date palms, Hajar mountains, red and green paper ribbons, empty space at top for title`
- الحركة: `Manuscript unrolls, paper cutouts pop up in layers, camera rises`

### 03 — «والفرحة جاءت من كل الجهات»
- الصورة: `Many paper letters and small paper scrolls flying in from all directions over teal background, some carried by wisps of frankincense smoke, a paper dhow boat in the corner, empty center for title`
- الحركة: `Letters fly inward from all sides, smoke drifting, dhow sailing slowly`

### 04 — «وحدة»
- الصورة: `Large piece of torn white paper in the center, stitched together with red and green Omani embroidery thread, teal paper-texture background, empty center for one big word`
- الحركة: `Two torn halves slide together and get stitched, slight settle shake`

### 05 — «انتماء»
- الصورة: `Close-up of two hands in white Omani dishdasha sleeves passing a folded paper letter wrapped with a red-green embroidered ribbon, black-and-white photo cutout style, teal background, empty top space for title`
- الحركة: `One hand passes the letter to the other, slow motion, slight camera drift`

### 06 — «وطن»
- الصورة: `Paper collage of an old Omani mud-brick village, falaj water channel, palm trees, Jebel Akhdar terraces and mountains, small paper clouds, empty sky for one big title word`
- الحركة: `Parallax between paper layers, clouds drifting, camera slowly pulling back`

### 07 — «اسم واحد»
- الصورة: `A long horizontal blank paper banner across the frame, framed on both sides by Omani embroidery pattern panels in red, white and green, teal background`
- الحركة: `Banner unfolds from the center outward, pattern panels slide in`

### 08 — «رسائل أكثر من أن تتسع لها صفحة»
- الصورة: `A huge pile of paper letters and envelopes rising from the bottom of the frame, some with red and green ribbons, teal sky with paper clouds, empty top half for title`
- الحركة: `Letters keep falling and piling up, camera tilting up`

### 09 — «فاكتفت بالإشارة إليها»
- الصورة: `Extreme close-up of an old newspaper page tilted at an angle, one small article highlighted with a green marker, paper letters around it, shallow depth of field, illegible abstract print`
- الحركة: `Slow slide along the page, highlight glowing softly, letters falling past`

### 10 — «لأن فرحة وطن… لا تحتويها صفحة»
- الصورة: `Paper letters swirling in a circle around a paper-cutout Muttrah corniche with old houses and dhow boats, frankincense smoke, teal background, empty center for title`
- الحركة: `Letters orbit around the scene, camera slowly rotating`

### 11 — «ومنذ ذلك اليوم… تكبر الحكاية»
- الصورة: `Paper collage skyline mixing modern Muscat landmarks (Sultan Qaboos Grand Mosque minaret and dome, Royal Opera House) with old forts, mud houses and palm trees, red and green embroidered ribbons waving through the scene, empty sky for title`
- الحركة: `Camera tracks sideways across the skyline, ribbons waving, buildings rising in layers`

### 12 — الختام: «العيد الوطني العُماني» مع الرقم
- الصورة: `Wide final shot: full paper collage of Oman, mountains, forts, Grand Mosque, palms and sea, crossed swords and khanjar emblem as a subtle paper cutout, red white green ribbons, paper clouds, large empty center space for title and number`
- الحركة: `Slow pull-back revealing the whole collage, ribbons settling, soft light sweep`

## ملاحظات مهمة

- **الرقم والتاريخ:** المقترح «٥٦» و«٢٠ نوفمبر»، لكنهما غير مؤكدين. تأكد منهما مع صاحبة المشروع قبل اعتمادهما.
- **الأسلوب الموحّد:** حافظ على نفس الخلفية الخضراء الغامقة ونفس ملمس الورق في كل المشاهد حتى يبدو الفيديو قطعة واحدة.
- **الألوان:** أحمر وأبيض وأخضر (ألوان العلم العُماني) للأشرطة والنقوش.
- **النقوش:** تطريز الكمة ونقش المندوس، لا نقش السدو.

## بعد التوليد

المقاطع الـ١٢ تُجمع في فيديو واحد: ترتيب المشاهد، انتقالات ناعمة، تركيب النصوص العربية، وإضافة الموسيقى. يمكن إرجاعها للمحادثة الأصلية لتجميعها بـ ffmpeg، أو تجميعها محلياً.
