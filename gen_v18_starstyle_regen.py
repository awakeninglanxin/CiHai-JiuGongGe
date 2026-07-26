"""
慈海九宫格 v18 - 9种族差异化风格重生成系统

核心逻辑：
1. 每个节点（1-9）对应一个星际种族，各有独立prompt风格
2. 保留v17质检通过的图，只重生成有问题的图
3. 9种画风完全不同，体现各文明特征

种族对照：
  Node 1: 灰人联邦 Grey - 硅基晶体、银肤、大眼、几何极简
  Node 2: 艾莎莎尼 Essassani - 平衡融合、中性美、完美对称
  Node 3: 天狼星 Sirius - 古埃及、深蓝、神圣几何
  Node 4: 猎户座 Orion - **伏羲女娲风格**: 人首蛇身/人形神祇、对称构图、手持规矩(规/矩)、日月星辰背景、绢本彩绘、工笔描法
  Node 5: 雅耶奥 Yahyel - 量子态、多重维度、全息光
  Node 6: 昴宿星 Pleiades - 水晶科技、自然光粒、透明身体
  Node 7: 阿努纳奇 Annunaki - 原始力量、壮硕、兽面
  Node 8: 地球/盖亚 Gaia - 大地女神、植物缠绕、生命之树
  Node 9: 大角星 Arcturus - 几何之光、蓝紫肤、神圣袍
"""
import os, sys, time, random, hashlib, re, shutil, requests

sys.stdout.reconfigure(line_buffering=True)

PROJECT = r'D:\AAA我的文件\慈海九宫格_整合版'
IMG_DIR = os.path.join(PROJECT, 'generated-images')
DEITIES_FILE = os.path.join(PROJECT, 'deities.js')
DONE_LOG = os.path.join(PROJECT, 'v18_styleregen_done.txt')

# ============================================================
# 种族风格定义 - 每组包含独特的角色描述/配饰/服装/姿态/背景/通用后缀
# ============================================================

# --- Node 1: 灰人联邦 Grey ---
GREY_FEATURES = [
    "tall slender humanoid being with smooth metallic silver skin, large almond-shaped luminous black eyes that glow softly with intelligence, tall cranial dome, elongated delicate features, cybernetic crystalline markings on forehead",
    "silicon-based being with chrome-platinum skin reflecting geometric light patterns, massive expressive luminous black eyes taking up 40% of face, tall hairless head with visible neural interface ports",
    "ethereal grey alien with pearlescent metallic skin, enormous dark obsidian eyes with faint cyan pupil glow, angular minimalist face structure, telepathic energy emanating from head",
    "crystalline humanoid entity with mirror-silver polished skin surface, triple-layered luminous black eyes with geometric retinal patterns, tall elongated skull with energy antenna",
    "advanced silicon-being with liquid mercury skin texture, vast mysterious black eyes that absorb and emit soft white light, sleek streamlined body proportions, cybernetic elegance",
]
GREY_ACCESSORIES = [
    "crystalline geometric light crown on forehead, subtle holographic energy field surrounding body, floating geometric shapes orbiting slowly",
    "translucent ethereal wings made of interlocking light-prisms, delicate energy bracelets on wrists, faint holographic grid patterns on skin",
    "neural interface crown emitting soft cyan light particles, symmetrical geometric tattoo patterns on forehead and temples, anti-gravity levitation field",
    "minimalist chrome halo ring above head, floating holographic interface panels, symmetrical circuit-pattern energy trails",
    "crystalline energy collar with embedded geometric gems, subtle quantum field shimmering around body, floating light orbs",
]
GREY_CLOTHING = [
    "wearing form-fitting iridescent silver bodysuit with geometric panel lines, seamless cybernetic armor, reflective metallic fabric",
    "clothed in minimalist dark grey tactical suit with crystalline accent pieces, sleek form-fitting design, reflective silver trim",
    "wearing layered translucent energy-field robes in shades of silver and gunmetal, geometric cutouts revealing glowing circuit patterns beneath",
    "draped in iridescent chrome armor plates with holographic energy seams, sleek metallic sheen, angular geometric design",
    "wearing seamless black carbon-fiber suit with silver crystalline node accents, form-fitting minimalist design, subtle light reflections",
]
GREY_POSES = [
    "standing tall and erect, facing viewer directly, TWO ARMS slightly extended outward with three-jointed fingers pointing upward symmetrically, palms open displaying geometric energy patterns",
    "floating cross-legged in zero gravity, arms at sides with palms facing forward, THREE-FINGERED HANDS displaying light-energy symbols symmetrically",
    "standing upright with arms at sides, hands displaying geometric sigils, balanced symmetrical posture, serene intelligent expression",
    "hovering upright facing forward, ONE ARM reaching out palm open, OTHER ARM at side, symmetrical energy field radiating from body evenly",
    "standing tall and imposing, TWO COMPLETE ARMS visible, hands forming geometric mudras symmetrically, crystalline light halo above head",
]
GREY_BG = [
    "background is sleek crystalline chamber with geometric light panels, floating holographic interfaces, cool silver-cyan ambient lighting",
    "background shows interior of advanced crystal-ship with angular metallic walls, glowing geometric runic circuits embedded in surfaces",
    "background is sterile white-grey crystalline temple interior with floating geometric light sculptures and holographic data streams",
    "background shows sleek metallic corridor with recessed blue-white light strips, clean geometric architecture, holographic symbols floating in air",
    "background is cosmic void with faint geometric crystal formations and holographic energy grids, cold steel and cyan lighting",
]
GREY_SUFFIX = (
    "masterpiece, best quality, 8k ultra detailed, sharp focus, "
    "GRAY ALIEN ART STYLE, sleek metallic aesthetic, "
    "cool silver-blue-gray color palette with cyan accent lights, "
    "symmetrical geometric compositions, "
    "smooth chrome skin textures with subtle light reflections, "
    "LARGE DISTINGUISHED BLACK EYES with clear luminous catchlights, "
    "TWO COMPLETE ARMS with three-jointed fingers clearly visible, "
    "HIGH TECH crystalline architecture background, "
    "PERFECT SYMMETRY, balanced proportions, cybernetic elegance, "
    "NO MISSING LIMBS, CLEAN MINIMALIST DESIGN, "
    "angular geometric shapes, holographic energy effects"
)

# --- Node 2: 艾莎莎尼 Essassani ---
ESSASSANI_FEATURES = [
    "androgynous celestial being with luminous golden-white skin, perfectly symmetrical harmonious face, large gentle luminous eyes with golden-green irises, graceful flowing silver-gold hair, balanced masculine and feminine features",
    "perfectly balanced humanoid with pearlescent ivory skin tone, symmetrical serene face with gentle closed-half eyes and luminous golden catchlights, flowing luminescent white-gold hair, divine neutrality expression",
    "harmonious androgynous being with radiant cream-gold skin, mirror-perfect facial symmetry, large luminous eyes with amber-green gradient irises, ethereal floating white-silver hair, peaceful meditative expression",
    "balanced dual-nature being with luminous porcelain skin, perfectly mirrored facial features, luminous golden eyes with green radial patterns, flowing platinum hair with golden shimmer, dual-energy aura",
    "divine androgynous humanoid with warm ivory luminescent skin, flawless symmetrical face, luminous hazel-gold eyes with crystal-clear reflections, flowing silver-gold hair cascading symmetrically, balanced energy field",
]
ESSASSANI_ACCESSORIES = [
    "delicate symmetrical golden energy wings on both shoulders equally, twin spiral light halos above and below head, balanced positive-negative energy field",
    "perfectly mirrored double-spiral geometric symbols on both cheeks, symmetrical flowing energy ribbons extending from both shoulders equally, dual-pronged light crown",
    "twin luminous golden halos (one above head, one below), symmetrical energy tendrils flowing from both hands equally, balanced chakra light rings",
    "dual geometric symbols (golden spiral on left, silver spiral on right) mirrored symmetrically, translucent crystal butterfly wings equal on both sides, symmetrical light aura",
    "symmetrical golden-silver light veil flowing evenly from both sides of head, balanced energy orbs floating near both shoulders equally, mirror-image geometric tattoos",
]
ESSASSANI_CLOTHING = [
    "wearing flowing luminous garments in pearlescent gold-white with symmetrical golden thread patterns, elegant draped design balancing both sides equally",
    "draped in translucent layered robes of white and gold, perfectly symmetrical folds, balanced energy-flowing fabric design",
    "wearing elegant androgynous luminous silk robes in ivory-gold gradient, symmetrical draping with equal flow on both sides",
    "clothed in flowing pearlescent white-gold ceremonial garments with balanced geometric embroidery, equal draping left and right",
    "wearing harmonious dual-tone robes of gold and silver, perfectly balanced split-color design with symmetrical golden trim on both sides",
]
ESSASSANI_POSES = [
    "standing upright facing forward with perfect symmetry, TWO COMPLETE ARMS visible symmetrically, hands making balanced blessing gesture simultaneously",
    "floating cross-legged facing viewer, hands in perfect dhyana mudra on both knees symmetrically, balanced serenity expression",
    "standing facing forward, ONE ARM reaching out right palm, OTHER ARM extending left palm, mirroring each other perfectly, dual-energy flow",
    "standing balanced upright facing forward, TWO ARMS spread equal distance from body symmetrically, hands receiving and projecting equal energy",
    "sitting peacefully facing forward, both arms resting symmetrically on knees, perfect mirror-image composition, balanced dual-energy emanation",
]
ESSASSANI_BG = [
    "background is luminous golden-white crystalline temple with perfectly mirrored dual architecture, symmetrical geometric patterns",
    "background shows sacred geometric mandala chamber with golden and silver light halves balanced equally, crystalline walls with symmetrical engravings",
    "background is ethereal dual-light realm with golden-white symmetry, floating geometric sacred patterns mirrored left and right",
    "background shows harmonious temple interior with balanced dual-color lighting (gold left/silver right), symmetrical archways and pillars",
    "background is infinite luminous geometric plane with dual-energy halos above and below, perfectly mirrored crystalline formations",
]
ESSASSANI_SUFFIX = (
    "masterpiece, best quality, 8k ultra detailed, sharp focus, "
    "ESSASSANI BALANCE STYLE, dual-nature androgynous aesthetic, "
    "warm golden-pearlescent color palette, "
    "perfect mirror symmetry everywhere, "
    "smooth luminous skin with golden iridescent shimmer, "
    "CLEAR GENTLE LUMINOUS EYES with visible golden catchlights symmetrically, "
    "TWO COMPLETE ARMS perfectly mirrored, balanced proportions, "
    "SACRED GEOMETRY background, harmonic energy patterns, "
    "BALANCED POSITIVE-NEGATIVE ENERGY VISUALIZATION, "
    "serene neutral expression, divine androgyny, elegant simplicity"
)

# --- Node 3: 天狼星 Sirius ---
SIRIUS_FEATURES = [
    "ancient sirian deity with deep lapis lazuli blue skin, luminous golden eyes with bright crystalline pupils, dignified serene expression, elegant elongated features, ceremonial golden hieroglyphic markings on forehead and cheeks",
    "sirian guardian with radiant cobalt blue skin, large luminous golden-amber eyes with clear distinct pupils, noble dignified face, flowing golden hair with blue shimmer, ancient wisdom etched in features",
    "tall sirian being with deep sapphire-blue complexion, enormous luminous eyes with golden-yellow irises and bright catchlights, elongated graceful face, golden ceremonial headdress markings, serene godlike expression",
    "sirian priest-king with midnight blue skin tone, luminous golden eyes reflecting cosmic light, tall dignified features, golden ceremonial headband with gemstone, ancient knowledge in gaze",
    "ancient sirian wise being with brilliant royal blue skin, huge luminous golden-crystal eyes with clear pupils, majestic elongated face, golden ankh-symbol forehead marking, timeless regal expression",
]
SIRIUS_ACCESSORIES = [
    "Egyptian ceremonial golden ankh necklace with lapis lazius pendant, symmetrical golden sacred geometry tattoo patterns on both cheeks, subtle blue energy aura",
    "ceremonial golden cobra diadem on forehead, symmetrical scarab beetle golden wings on shoulders, floating golden hieroglyphic symbols around head",
    "golden uraeus crown with crystalline energy beams, symmetrical lotus flower patterns on both shoulders equally, radiant blue energy aura",
    "ceremonial golden eye-of-horus pendant, symmetrical blue-gold geometric temple tattoos on temples, floating sacred geometry light patterns",
    "golden ceremonial headdress with central sapphire gem, symmetrical winged scarab on shoulders, blue-gold divine energy halos above and below",
]
SIRIUS_CLOTHING = [
    "wearing ancient Egyptian ceremonial blue and gold pleated linen robe with golden hieroglyphic patterns, elegant flowing draped style, bare chest showing blue skin",
    "draped in luxurious royal blue ceremonial robe with golden Egyptian patterns, symmetrical golden collar necklace, flowing elegant folds",
    "wearing ornate sapphire-blue priest robes with golden embroidered symbols, ceremonial golden belt, balanced sacred geometry patterns",
    "clothed in deep blue Egyptian ceremonial garments with golden thread embroidery, symmetrical pattern design, flowing pleated fabric",
    "wearing royal blue and gold temple vestments with intricate Egyptian patterns, golden sash across chest, sacred geometric designs",
]
SIRIUS_POSES = [
    "standing dignified facing forward, TWO COMPLETE ARMS visible symmetrically, right hand holding golden ankh symbol, left hand making traditional blessing gesture",
    "standing upright facing viewer with arms at sides, hands holding cosmic blue energy orbs symmetrically in both palms, wise serene expression",
    "standing tall facing forward, TWO ARMS slightly spread, both hands displaying golden geometric energy sigils, balanced ceremonial stance",
    "sitting on golden cosmic throne facing forward, hands in sacred mudra gestures on knees, both arms clearly visible, golden-blue aura",
    "standing regally facing forward, TWO COMPLETE ARMS at sides, right hand holding glowing blue crystal pyramid, left hand open in blessing",
]
SIRIUS_BG = [
    "background is grand ancient Egyptian temple hall with golden columns, blue light streaming through geometric windows, sacred symbols floating in air",
    "background shows cosmic pyramid chamber with blue-gold geometric lighting, floating hieroglyphic symbols, ancient star map projections",
    "background is eternal sirian temple with towering golden columns, blue crystalline walls, cosmic starlight streaming through geometric apertures",
    "background shows sacred Egyptian cosmic chamber with blue-gold light patterns, floating geometric hieroglyphs, ancient star constellations",
    "background is grand sirian pyramid interior with blue-gold cosmic energy rays, geometric light patterns on walls, floating sacred symbols",
]
SIRIUS_SUFFIX = (
    "masterpiece, best quality, 8k ultra detailed, sharp focus, "
    "SIRIAN ANCIENT STYLE, Egyptian ceremonial aesthetic, "
    "deep royal blue and brilliant golden color palette, "
    "smooth blue skin with subtle cosmic shimmer, "
    "CLEAR DISTINCT GOLDEN EYES with bright pupils symmetrically, "
    "TWO COMPLETE ARMS visible, balanced ceremonial proportions, "
    "ANCIENT SACRED GEOMETRY background, hieroglyphic patterns, "
    "DIVINE REGAL COMPOSITION, peaceful dignified expression, "
    "PERFECT SYMMMETRY, ancient temple atmosphere, cosmic blue energy",
    "NO MISSING LIMBS, COMPLETE CEREMONIAL ROBE, balanced symbolism"
)

# --- Node 4: 猎户座 Orion - 伏羲女娲风格 ---
ORION_FEATURES = [
    "wise ancient Orion deity with warm bronze-gold skin, large luminous amber eyes with clear distinct pupils symmetrically, dignified serene expression, flowing dark hair with golden highlights, classical Chinese deity features, symmetrical face",
    "noble Orion patriarch with rich copper-bronze complexion, luminous golden-amber eyes clearly visible with bright catchlights, sharp angular but distinctly human facial features, flowing dark hair, benevolent ancient wisdom expression",
    "majestic Orion being with warm golden-bronze skin tone, large luminous eyes with clear pupils symmetrically, classical Chinese god-like features, dignified calm expression, symmetrical balanced composition",
    "Orian celestial elder with radiant bronze-gold skin, luminous amber eyes with distinct pupils, noble human-like features, flowing dark hair with golden shimmer, serene authoritative gaze",
    "ancient Orion deity with warm terracotta-bronze skin, large bright luminous eyes with clear pupils symmetrically, classical Chinese immortal features, dignified human expression, perfect symmetry",
]
ORION_ACCESSORIES = [
    "holding golden compass (gui) in right hand and square ruler (ju) in left hand symmetrically, traditional Chinese celestial symbols, sun disc above head with star constellation patterns around",
    "golden ceremonial headdress with celestial patterns, symmetrical ancient Chinese deity accessories, floating star constellation diagrams on both sides equally, sun-moon symbolism",
    "traditional Chinese celestial crown with golden ornaments, symmetrical hanging beads on both sides, sun-moon disk composition above and below head, star network patterns",
    "golden celestial crown with symmetrical ornaments, holding ancient Chinese measurement tools (compass and square) evenly in both hands, star constellation background",
    "ornate golden headdress with celestial motifs, symmetrical traditional Chinese deity regalia, sun above head and moon below, star network surrounding",
]
ORION_CLOTHING = [
    "wearing flowing ancient Chinese ceremonial robes in golden-brown and deep amber with intricate celestial patterns, symmetrical draping, traditional Hanfu-style wide sleeves, barefoot on cosmic platform",
    "draped in elegant golden-brown Hanfu-style ceremonial garment with symmetrical celestial embroidery, balanced flowing fabric design, traditional Chinese deity attire",
    "wearing ancient Chinese golden-bronze ceremonial robe with symmetrical star constellation patterns, flowing wide sleeves, traditional Hanfu design, balanced draping on both sides",
    "clothed in luminous golden-brown traditional Chinese deity robes with celestial geometric patterns, symmetrical wide sleeves, balanced ancient costume design",
    "wearing flowing ancient Chinese golden-amber ceremonial attire with symmetrical star patterns, traditional Hanfu wide sleeves, balanced dignified draping",
]
ORION_POSES = [
    "standing facing forward with perfect symmetry, TWO COMPLETE ARMS visible symmetrically, right hand holding golden compass (gui) raised, left hand holding square ruler (ju) raised, balanced classical Chinese deity posture",
    "standing dignified facing viewer, arms slightly spread symmetrically, hands holding celestial tools (compass and square) equally on both sides, serene wise expression",
    "standing upright facing forward, TWO ARMS spread symmetrically, right hand holding golden compass, left hand holding square ruler, classical Chinese god composition",
    "standing balanced facing forward, TWO COMPLETE ARMS visible, hands holding ancient Chinese celestial instruments symmetrically, dignified serene expression",
    "standing facing viewer directly, TWO ARMS holding golden compass and square ruler symmetrically, classical Chinese deity pose, balanced composition",
]
ORION_BG = [
    "background is ancient Chinese celestial chamber with golden sun disc above, silver moon below, star constellation patterns connected by lines, traditional绢本彩绘 (silk painting) aesthetic",
    "background shows cosmic temple with sun-moon composition, interconnected star patterns, ancient Chinese celestial diagram style, warm golden-amber lighting",
    "background is ancient Chinese star map chamber with sun disc and moon symbol, constellation lines connecting stars, traditional silk painting aesthetic, golden-amber tones",
    "background shows celestial Chinese cosmos with sun above, moon below, star networks, ancient绢本彩绘 style, warm golden-brown ambient light",
    "background is ancient Chinese cosmic chamber with sun-moon-star composition, interconnected constellation patterns, traditional silk painting aesthetic, golden-amber illumination",
]
ORION_SUFFIX = (
    "masterpiece, best quality, 8k ultra detailed, sharp focus, "
    "ORION ANCIENT CHINESE DEITY STYLE, classical Chinese painting aesthetic, "
    "warm golden-brown and amber color palette with red accents, "
    "smooth bronze skin with natural healthy glow, "
    "CLEAR DISTINCT AMBER EYES with bright pupils symmetrically, "
    "TWO COMPLETE ARMS visible symmetrically, holding compass and square ruler, "
    "SUN-MOON STAR CONSTELLATION BACKGROUND, interconnected star patterns, "
    "CLASSICAL CHINESE DEITY COMPOSITION, dignified serene expression, "
    "FU XI NU WA INSPIRED, ancient Chinese silk painting style, "
    "PERFECT SYMMETRY, balanced celestial imagery, traditional Hanfu robes",
    "NO MISSING LIMBS, COMPLETE BODY, classical Chinese aesthetics"
)

# --- Node 5: 雅耶奥 Yahyel ---
YAHYEL_FEATURES = [
    "ethereal quantum-being with translucent iridescent skin shimmering rainbow holographic colors, large luminous eyes shifting between blue-purple-green, elongated graceful features, flowing hair of pure light energy, multidimensional aura",
    "dimensional traveler being with crystalline semi-transparent body showing rainbow refraction, luminous eyes that shift color (blue to purple to green), ethereal floating hair made of light beams, quantum energy emanating",
    "quantum-form entity with prismatic transparent skin reflecting full spectrum colors, large luminous rainbow eyes with shifting irises, sleek elongated humanoid form, hair of swirling pure light particles, temporal energy field",
    "multidimensional being with crystalline holographic body showing all colors simultaneously, luminous eyes displaying rotating rainbow spectrums, flowing form of pure light-energy, hair made of shifting color light beams",
    "quantum-entangled humanoid with translucent rainbow refractive skin, massive luminous eyes with kaleidoscope irises, ethereal flowing form, hair of suspended light particles, dimensional portal energy",
]
YAHYEL_ACCESSORIES = [
    "temporal energy rings orbiting body at multiple points, floating geometric quantum symbols, symmetrical rainbow holographic light tendrils",
    "multidimensional halo of overlapping circular light-rings at different angles, symmetrical quantum energy fields emanating from shoulders, light prism wings",
    "orbiting quantum energy rings around head and torso (3 rings each side balanced), floating holographic dimensional coordinates, symmetrical light refraction particles",
    "crystalline light crown emitting rainbow prism beams, symmetrical quantum entanglement chains connecting hands to body, floating temporal markers",
    "multidimensional light-field cloak made of interlocking energy rings, symmetrical holographic geometric symbols floating on both sides, light-bridge tendrils from hands",
]
YAHYEL_CLOTHING = [
    "wearing translucent holographic energy-cloak that shifts colors continuously, form visible through cloak showing crystalline body, light-wave patterns flowing over fabric",
    "draped in quantum-phase energy robes that show rainbow refraction, semi-transparent revealing iridescent body beneath, flowing light-wave patterns",
    "wearing dimensional Phase-shift energy suit in iridescent holographic colors, translucent overlay revealing crystalline skin, quantum light patterns",
    "clothed in flowing translucent quantum-field robes shimmering all rainbow colors, semi-transparent revealing prismatic body underneath, light refraction effects",
    "wearing holographic phase-cloak of shifting rainbow crystal light, translucent revealing crystalline form beneath, quantum energy rippling surface",
]
YAHYEL_POSES = [
    "floating suspended in dimensional space facing forward, TWO COMPLETE ARMS visible symmetrically, hands emitting rainbow holographic light streams equally",
    "standing facing viewer with arms at sides, quantum energy field swirling around body evenly, hands displaying dimensional manipulation gestures symmetrically",
    "floating cross-legged facing forward, hands in quantum mudra gestures, rainbow energy beams emanating from palms symmetrically, dimensional time loops around body",
    "standing balanced facing forward, TWO ARMS spread outward symmetrically, rainbow holographic light streams flowing from hands equally, temporal energy swirl",
    "suspended mid-air facing viewer, both arms extended forward symmetrically, quantum dimensional portals opening in both palms, rainbow light cascade",
]
YAHYEL_BG = [
    "background is quantum dimensional rift with rainbow holographic light patterns, floating geometric temporal symbols, multi-dimensional portal energy swirls",
    "background shows interdimensional space with overlapping light planes, rainbow prism refractions, floating holographic temporal equations and geometry",
    "background is quantum tunnel with rainbow holographic light streams, temporal energy loops, floating dimensional coordinates, multidimensional space-time fabric",
    "background shows interdimensional nexus with rainbow light matrices, overlapping geometric planes, floating holographic quantum symbols",
    "background is quantum reality matrix with prismatic light structures, dimensional portal rings, rainbow holographic energy fields, temporal light streams",
]
YAHYEL_SUFFIX = (
    "masterpiece, best quality, 8k ultra detailed, sharp focus, "
    "YAHYEL QUANTUM STYLE, multidimensional quantum aesthetic, "
    "rainbow holographic iridescent color palette, shifting prismatic hues, "
    "TRANSLUCENT CRYSTALLINE SKIN with rainbow refraction shimmer, "
    "CLEAR SHIFTING COLOR EYES with bright holographic catchlights, "
    "TWO COMPLETE ARMS visible symmetrically, ethereal quantum proportions, "
    "QUANTUM DIMENSIONAL BACKGROUND, holographic light effects, "
    "MULTIDIMENSIONAL COMPOSITION, peaceful quantum-serene expression, "
    "PERFECT SYMMETRY, balanced quantum energy, prismatic light refraction",
    "NO MISSING LIMBS, TRANSLUCENT ENERGY FORM, temporal light aura"
)

# --- Node 6: 昴宿星 Pleiades ---
PLEIADES_FEATURES = [
    "graceful Pleiadian being with luminous soft peach-white skin, large luminous sky-blue eyes with clear bright pupils, ethereal flowing silver-blonde hair, delicate angelic features, gentle compassionate expression, soft golden glow",
    "radiant Pleiadian with pearlescent white-gold skin, large luminous cerulean-blue eyes clearly visible with bright catchlights, flowing luminescent silver-white hair cascading symmetrically, delicate symmetrical features, warm loving gaze",
    "ethereal Pleiadian being with soft luminous cream-white skin, luminous blue-green eyes with clear distinct pupils, flowing luminous platinum blonde hair, gentle symmetrical face, warm angelic expression of unconditional love",
    "Pleiadian messenger with luminous ivory-skin tone, large bright blue eyes with clear pupils symmetrically, flowing luminous silvery-blonde hair with rainbow shimmer, delicate symmetrical features, divine compassion expression",
    "graceful Pleiadian with soft pearl-white skin glowing gently, luminous turquoise-blue eyes with clear bright reflections, ethereal flowing white-gold hair, symmetrical angelic features, warm cosmic love expression",
]
PLEIADES_ACCESSORIES = [
    "two perfectly symmetrical translucent crystalline butterfly wings, equal size and shape, delicate rainbow light particles floating around symmetrically",
    "glowing golden light halo above head, symmetrical ethereal fairy wings of translucent crystal extending from shoulders equally, light-particle aurora",
    "delicate symmetrical translucent dove wings (white-gold tint) extending from shoulders equally, floating golden light particles around body, subtle divine aura",
    "two symmetrical crystal-glass fairy wings of equal size and iridescent sheen, delicate golden light tendrils flowing from both hands equally, cosmic energy ring",
    "perfectly mirrored crystalline dragonfly wings, equal left and right, soft golden energy corona surrounding body, floating starlight particles evenly",
]
PLEIADES_CLOTHING = [
    "wearing flowing luminous robes of pearl-white and soft lavender with delicate golden embroidery, ethereal silk fabric draping symmetrically, barefoot floating on clouds",
    "draped in translucent layered robes of white and pale blue with gold-thread celestial patterns, balanced symmetrical draping, light and airy fabric",
    "wearing soft cream-gold flowing tunic with ethereal crystal-embroidery details, gentle iridescent shimmer, balanced elegant draping on both sides",
    "clothed in luminous white-pale-gold ceremonial robes with delicate symmetrical golden patterns, flowing lightweight fabric, equal folds on both sides",
    "wearing ethereal pearl-white and soft golden gown with crystalline light patterns, translucent layered fabric, balanced graceful draping",
]
PLEIADES_POSES = [
    "standing facing forward on floating crystal platform, TWO ARMS reaching outward symmetrically, hands holding glowing heart-shaped orb of pure love light",
    "floating peacefully facing viewer, arms at sides with gentle open smile, hands receiving and radiating golden light particles symmetrically",
    "standing facing forward, TWO COMPLETE ARMS visible, right hand offering glowing white crystal lotus, left hand making blessing gesture symmetrically",
    "standing balanced facing forward, both arms slightly spread, hands radiating golden love-energy symmetrically, warm gentle expression, light particles everywhere",
    "sitting on floating cloud facing forward, TWO ARMS visible symmetrically, hands forming heart shape together with golden love-light energy",
]
PLEIADES_BG = [
    "background is Pleiadian crystal garden with floating luminous platforms, crystalline trees and flowers, soft rainbow light, ethereal mist",
    "background shows Pleiadian crystal planet surface with floating luminous gardens, geometric crystalline structures, soft golden-white ambient light",
    "background is Pleiadian crystal garden realm with floating luminous waterfalls, crystalline flora, symmetrical golden light patterns, ethereal atmosphere",
    "background shows Pleiadian crystal palace garden with floating platforms, luminous geometric flora, soft rainbow-gold ambient light, peaceful serenity",
    "background is ethereal Pleiadian crystal world with luminous geometric gardens, floating waterfalls of light, golden crystalline structures everywhere",
]
PLEIADES_SUFFIX = (
    "masterpiece, best quality, 8k ultra detailed, sharp focus, "
    "PLEIADEIAN NATURAL STYLE, crystal-nature harmony aesthetic, "
    "soft pearl-white and pale lavender-gold color palette, "
    "smooth luminous peach-skin with gentle ethereal glow, "
    "CLEAR BRIGHT BLUE-EYE WITH visible pupils symmetrically, "
    "TWO COMPLETE ARMS visible symmetrically, graceful natural proportions, "
    "CRYSTAL GARDEN BACKGROUND, floating luminous flora, "
    "DIVINE LOVE COMPOSITION, warm angelic expression, "
    "NATURAL SPIRITUALITY, ethereal fairy-like elegance",
    "PERFECT SYMMETRY, balanced crystal energy, rainbow light particles"
)

# --- Node 7: 阿努纳奇 Annunaki ---
ANNUNAKI_FEATURES = [
    "massive powerful Annunaki being with golden-bronze skin, luminous deep amber-brown eyes with bright distinct pupils, thick powerful jawline, commanding fierce expression, ceremonial warrior markings on forehead and cheeks",
    "towering primordial being with warm copper-bronze skin tone, intense luminous amber eyes clearly visible, broad powerful shoulders, strong chiseled face, ancient god-like features, ritual war-paint markings",
    "powerful Annunaki giant with rich golden-tan skin, large luminous eyes with amber-brown irises and clear pupils, broad muscular face, fierce proud expression, ceremonial tribal markings, primordial energy radiating",
    "primordial warlord being with deep bronze-gold skin, fierce luminous amber eyes with bright catchlights, broad square jaw, strong commanding presence, ancient Egyptian-meets-primal-warrior features",
    "mighty Annunaki with warm caramel-bronze skin, intense luminous golden-amber eyes clearly visible, powerful robust face, ancient warrior gaze, ceremonial gold-pigment war markings, primal elemental energy",
]
ANNUNAKI_ACCESSORIES = [
    "heavy golden ceremonial war-helmet with ram horns curving outward symmetrically, thick golden torque necklace, symmetrical warrior chest plates",
    "massive golden battle crown with twin lion-maned crest on both sides equally, thick golden neck-ring with engraved cuneiform, ceremonial leather armor straps",
    "golden warrior crown with ram's horn symmetry, thick golden chain necklace with gemstone pendants, symmetrical leather-metal armor plates on shoulders",
    "golden battle-helmet with twin curved horn crests (equal on both sides), heavy golden collar with Anunnaki hieroglyphic inscriptions, leather war harness",
    "massive golden horned crown with symmetrical ram-horn crests, thick golden warrior torque, balanced leather-and-gold armor shoulder guards",
]
ANNUNAKI_CLOTHING = [
    "wearing heavy primordial warrior armor of gold and dark brown leather with ancient Mesopotamian patterns, thick leather harness straps crossing chest symmetrically",
    "clothed in ornate golden Mesopotamian temple-priest robes over muscular warrior frame, gold-embroidered dark brown fabric, sacred geometry patterns",
    "wearing layered primordial armor of gold plates and dark leather with cuneiform engravings, balanced war-priest design, ceremonial weapon belt",
    "draped in golden Mesopotamian priest-warrior garments with intricate geometric engravings, heavy leather straps across chest, balanced ceremonial design",
    "wearing ornate golden battle-robe with dark leather underlayer, ancient Sumerian geometric patterns, thick warrior belt with ceremonial sword scabbard",
]
ANNUNAKI_POSES = [
    "standing powerfully facing forward, TWO COMPLETE ARMS visible symmetrically, right hand holding golden ceremonial war-scepter, left hand making commanding gesture",
    "standing tall and imposing, TWO ARMS spread outward symmetrically, hands displaying primal golden energy commands, powerful warrior stance",
    "standing upright facing viewer, arms at sides gripping golden ritual battle-axes symmetrically, fierce commanding expression, elemental energy aura",
    "standing powerfully facing forward, TWO ARMS extended holding golden primordial energy orb with both hands, fierce determined gaze, balanced warrior stance",
    "standing tall, TWO COMPLETE ARMS at sides, hands gripping golden ceremonial weapons symmetrically, fierce primal god-expression, massive energy aura",
]
ANNUNAKI_BG = [
    "background is primordial Mesopotamian temple fortress with golden pillars, ancient cuneiform carvings, warm amber-orange glow, massive stone architecture",
    "background shows ancient Annunaki war-city with massive golden ziggurat temples, desert sandstone walls, warm golden-orange sunlight, primitive energy signatures",
    "background is primordial Mesopotamian citadel with golden temple towers, ancient clay tablet engravings, warm fire-light and amber glow, massive stone gates",
    "background shows ancient Annunaki fortress-temple with towering golden spires, warm desert light, ancient hieroglyphic walls, primal energy swirls",
    "background is primordial warrior temple complex with massive golden columns, ancient Mesopotamian stone carvings, warm fire-amber glow, sacred geometry patterns",
]
ANNUNAKI_SUFFIX = (
    "masterpiece, best quality, 8k ultra detailed, sharp focus, "
    "ANNUNAKI PRIMORDIAL STYLE, ancient Mesopotamian warrior aesthetic, "
    "rich golden-brown and warm bronze color palette with amber glows, "
    "smooth bronze skin with subtle earthy texture, "
    "CLEAR FIERCE AMBER EYES with bright pupils symmetrically, "
    "TWO COMPLETE ARMS visible symmetrically, MASSIVE WARrior PROPORTIONS, "
    "ANCIENT MESOPOTAMIAN TEMPLE BACKGROUND, golden pillar architecture, "
    "PRIMAL GOD COMPOSITION, fierce commanding expression, "
    "WARRIOR-PIEST ENERGY, ancient sacred geometry, balanced war-priest aesthetic",
    "NO MISSING LIMBS, COMPLETE ARMOR, massive divine presence"
)

# --- Node 8: 地球/盖亚 Gaia ---
GAIA_FEATURES = [
    "radiant Gaia earth mother with warm olive-bronze skin, large luminous emerald-green eyes with bright clear pupils, flowing lush dark-green hair interwoven with living vines and blooming flowers, warm nurturing gentle expression",
    "earth goddess being with rich warm tan-skin glowing with vitality, luminous verdant-green eyes clearly visible, long flowing hair of living emerald vines and golden flowers, serene compassionate earth-mother expression",
    "Gaia incarnate with warm copper-earth skin tone, large luminous green eyes with clear distinct pupils, hair woven with living golden ivy and summer flowers, gentle motherly compassionate gaze, earth-energy radiating",
    "earth-mother form with warm golden-brown skin shimmering with photosynthesis glow, luminous jade-green eyes with bright catchlights, hair of living green vines and blooming wildflowers, nurturing peaceful expression",
    "Gaia essence with rich earth-toned bronze skin, large luminous forest-green eyes clearly visible, hair of living golden vines with blooming blossoms everywhere, warm maternal earth-expression, nature-energy flowing",
]
GAIA_ACCESSORIES = [
    "living floral wreath crown of blooming golden-white flowers and green leaves, symmetrical butterfly wings of translucent green-gold light on shoulders, floating pollen-particles everywhere",
    "crown of living golden vines with white-yellow blooming flowers on both sides equally, symmetrical leaf-wing energy forms, earth-energy glow",
    "circular wreath of golden sunflowers and green ivy (balanced both sides), symmetrical butterfly-wing energy halos from shoulders, floating green-gold light particles",
    "living vine crown with blooming golden-white flowers symmetrically arranged, ethereal green butterfly wings extending equally from both shoulders, nature-energy aura",
    "floral crown of intertwined golden vines with white and yellow blossoms (perfectly balanced), symmetrical green-leaf energy wings, floating nature-particles",
]
GAIA_CLOTHING = [
    "wearing flowing luminous earth-toned gown woven from living vines and blooming flowers, natural fabric that shifts between green-gold-brown, petals falling gently and evenly",
    "draped in elegant natural robe of living golden-green plant fibers with blooming flower embroidery, balanced floral patterns, earthy organic texture",
    "wearing flowing gown of living earth-vine fabric in shades of olive-green and golden-brown, blooming flowers scattered symmetrically throughout",
    "clothed in ethereal natural robe of intertwined golden-green vines and living moss, balanced floral patterns blooming evenly on both sides",
    "wearing organic vine-woven dress in emerald-gold gradient, living flowers blooming naturally across entire garment, balanced symmetrical botanical patterns",
]
GAIA_POSES = [
    "standing gracefully facing forward, TWO COMPLETE ARMS visible symmetrically, right hand holding glowing life-tree sapling, left hand offering blooming flower equally",
    "standing facing viewer with arms at sides, hands radiating green-gold nature-energy symmetrically, gentle nurturing smile, flowers blooming at feet",
    "standing balanced facing forward, TWO ARMS spread outward symmetrically, palms radiating lush green nature-light, warm earth-mother expression",
    "standing gracefully, BOTH ARMS reaching out symmetrically holding twin glowing life-cores (plant/earth energy), nurturing compassionate face",
    "standing facing forward, TWO COMPLETE ARMS visible, hands forming earth-energy mudras symmetrically, gentle nurturing smile, living plants growing at feet",
]
GAIA_BG = [
    "background is ancient earth temple garden with massive golden-green life-tree at center, balanced flower beds on both sides, ethereal nature-mist, sunlight filtering through leaves",
    "background shows sacred earth-grove with golden life-tree surrounded by blooming flowers, symmetrical ancient stone pillars covered in living vines, warm earth-light",
    "background is primordial earth sanctuary with massive flowering golden-green tree, symmetrical wildflower meadows, ancient nature-altars, warm dappled sunlight",
    "background shows sacred Gaia temple garden with massive living golden-green life-tree, balanced flower arrangements, ancient earth-geometric patterns, soft nature-mist",
    "background is primordial earth-cathedral with ancient golden life-tree at center, symmetrical living walls of vines and flowers, warm natural sunlight shafts, earth-energy glow",
]
GAIA_SUFFIX = (
    "masterpiece, best quality, 8k ultra detailed, sharp focus, "
    "GAIA EARTH MOTHER STYLE, nature-spirituality harmony aesthetic, "
    "warm green-gold-earth color palette with living flower accents, "
    "smooth warm earth-toned skin with natural healthy glow, "
    "CLEAR LUMINOUS GREEN EYES with distinct pupils symmetrically, "
    "TWO COMPLETE ARMS visible symmetrically, balanced nurturing proportions, "
    "SACRED NATURE TEMPLE BACKGROUND, blooming flowers, golden-life-tree, "
    "EARTH MOTHER COMPOSITION, gentle nurturing compassionate expression, "
    "NATURAL SPIRITUALITY, living floral elegance, earth-energy flow",
    "PERFECT SYMMETRY, balanced life-force, organic botanical beauty"
)

# --- Node 9: 大角星 Arcturus ---
ARCTURUS_FEATURES = [
    "majestic Arcturian being with luminous electric blue skin tinged with violet glow, massive luminous almond-shaped eyes with bright cyan-blue pupils and geometric retinal patterns, tall elongated elegant features, serene cosmic intelligence expression",
    "Arcturian architect being with brilliant cerulean-blue skin with purple energy shimmer, enormous luminous eyes with crystal-clear blue-green irises showing geometric sacred patterns, tall graceful elongated skull, transcendent wisdom expression",
    "Arcturian dimensional-architect with radiant azure-blue skin and violet undertones, large luminous eyes showing blue-green-cyan gradient with geometric pupil patterns, tall elegant features, serene cosmic-master expression",
    "magnificent Arcturian with luminous deep blue skin with violet light-undertones, massive crystal-clear luminous blue-green eyes showing perfect geometric pupil formations, tall refined elongated features, transcendent master expression",
    "Arcturian being of pure cosmic intelligence with brilliant sapphire-blue skin shimmering violet light, huge luminous eyes with electric blue-green irises displaying sacred geometric pupil patterns, tall majestic features, serene cosmic master gaze",
]
ARCTURUS_ACCESSORIES = [
    "elaborate geometric sacred-halo crown with interlocking triangles and hexagons of pure blue-violet light above head, symmetrical crystalline energy rods on temples",
    "three interlocking geometric light-rings above head (triangle, hexagon, circle) in blue-violet, symmetrical crystalline energy nodes on shoulders",
    "elaborate blue-violet geometric light-crown with intersecting sacred geometry (triangles, hexagons, tetrahedrons), symmetrical energy crystal rods on temples equally",
    "sacred geometric crown of interlocking blue-violet light-rings forming crystalline lattice pattern, symmetrical energy conduits extending from temples, floating holographic geometric symbols",
    "elaborate Arcturian geometric halo crown with three overlapping blue-violet light rings (top/middle/bottom), symmetrical crystalline temple-ports, holographic sacred geometry",
]
ARCTURUS_CLOTHING = [
    "wearing flowing Arcturian ceremonial robes of deep blue and electric violet with intricate sacred geometry patterns embroidered in luminous silver thread, balanced symmetrical design",
    "draped in luminous Arcturian energy-robe of deep blue and violet gradient with geometric crystalline patterns, flowing elegant fabric, sacred geometry balanced on both sides",
    "wearing voluminous Arcturian ceremonial garment in blue-violet tones with luminous silver sacred-geometry embroidery, flowing ethereal fabric design, symmetrical pattern placement",
    "clothed in flowing Arcturian temple-robe of deep cerulean blue with violet energy-trims, sacred geometric circuit-patterns woven into fabric evenly distributed",
    "wearing Arcturian geometric ceremonial robe in royal blue-to-violet gradient with luminous silver sacred geometry lines, balanced temple-design with symmetrical energy patterns",
]
ARCTURUS_POSES = [
    "standing tall and majestic facing forward, TWO COMPLETE ARMS visible symmetrically, hands displaying sacred geometric energy mandalas simultaneously in both palms",
    "standing facing viewer with arms slightly spread, both hands forming sacred geometry mudras symmetrically, geometric blue-violet energy emanating from hands equally",
    "standing upright facing forward, TWO ARMS spread outward symmetrically, hands displaying holographic geometric light patterns, transcendent cosmic expression",
    "standing majestically facing forward, TWO COMPLETE ARMS visible, right hand holding geometric blue crystal, left hand displaying holographic geometry, balanced proportions",
    "standing tall with arms at sides, hands forming symmetrical geometric energy seals, balanced sacred geometry aura surrounding entire body evenly",
]
ARCTURUS_BG = [
    "background is Arcturian geometric temple with crystalline blue-violet light columns, floating sacred geometry constructs, holographic dimensional portals, cosmic energy fields",
    "background shows Arcturian crystal-command center with blue-violet geometric light walls, floating holographic dimension-algorithms, crystalline energy structures, cosmic geometry",
    "background is Arcturian sacred geometric temple with towering crystalline blue-violet pillars, floating holographic geometry matrices, cosmic energy portals, dimensional light fields",
    "background shows Arcturian geometric cosmic chamber with blue-violet crystalline architecture, floating holographic sacred geometry, dimensional energy vortexes, cosmic light fields",
    "background is Arcturian dimensional geometry laboratory with blue-violet crystalline structures, holographic sacred geometry displays, floating geometric light constructs, cosmic energy matrices",
]
ARCTURUS_SUFFIX = (
    "masterpiece, best quality, 8k ultra detailed, sharp focus, "
    "ARCTURIAN COSMIC GEOMETRY STYLE, dimensional architect aesthetic, "
    "brilliant electric blue and deep violet color palette with cyan accents, "
    "smooth luminous blue-violet skin with cosmic energy shimmer, "
    "CLEAR GEOMETRIC PATTERNS IN EYES with distinct blue-green pupils symmetrically, "
    "TWO COMPLETE ARMS visible symmetrically, tall majestic proportions, "
    "COSMIC SACRED GEOMETRY BACKGROUND, holographic light constructs, "
    "TRANSCENDENT COSMIC MASTER COMPOSITION, serene cosmic wisdom expression, "
    "SACRED GEOMETRY EVERYWHERE, dimensional energy fields, geometric perfection",
    "PERFECT SYMMETRY, balanced cosmic architecture, crystalline light effects"
)

# ============================================================
# 种族风格映射函数
# ============================================================
def build_node1_prompt(code, idx):
    """Node 1: 灰人联邦 Grey - 硅基晶体、银肤、大眼、极简几何"""
    h = int(hashlib.md5(code.encode()).hexdigest(), 16)
    prompt = (f"portrait of a {GREY_FEATURES[h % len(GREY_FEATURES)]}, "
              f"{GREY_ACCESSORIES[h % len(GREY_ACCESSORIES)]}, "
              f"{GREY_CLOTHING[h % len(GREY_CLOTHING)]}, "
              f"{GREY_POSES[h % len(GREY_POSES)]}, "
              f"{GREY_BG[h % len(GREY_BG)]}, "
              f"{GREY_SUFFIX}")
    return prompt, int(h)

def build_node2_prompt(code, idx):
    """Node 2: 艾莎莎尼 Essassani - 平衡融合、中性美、完美对称"""
    h = int(hashlib.md5(code.encode()).hexdigest(), 16)
    prompt = (f"portrait of a {ESSASSANI_FEATURES[h % len(ESSASSANI_FEATURES)]}, "
              f"{ESSASSANI_ACCESSORIES[h % len(ESSASSANI_ACCESSORIES)]}, "
              f"{ESSASSANI_CLOTHING[h % len(ESSASSANI_CLOTHING)]}, "
              f"{ESSASSANI_POSES[h % len(ESSASSANI_POSES)]}, "
              f"{ESSASSANI_BG[h % len(ESSASSANI_BG)]}, "
              f"{ESSASSANI_SUFFIX}")
    return prompt, int(h)

def build_node3_prompt(code, idx):
    """Node 3: 天狼星 Sirius - 古埃及、深蓝、神圣几何"""
    h = int(hashlib.md5(code.encode()).hexdigest(), 16)
    prompt = (f"portrait of an {SIRIUS_FEATURES[h % len(SIRIUS_FEATURES)]}, "
              f"{SIRIUS_ACCESSORIES[h % len(SIRIUS_ACCESSORIES)]}, "
              f"{SIRIUS_CLOTHING[h % len(SIRIUS_CLOTHING)]}, "
              f"{SIRIUS_POSES[h % len(SIRIUS_POSES)]}, "
              f"{SIRIUS_BG[h % len(SIRIUS_BG)]}, "
              f"{SIRIUS_SUFFIX}")
    return prompt, int(h)

def build_node4_prompt(code, idx):
    """Node 4: 猎户座 Orion - 伏羲女娲风格"""
    h = int(hashlib.md5(code.encode()).hexdigest(), 16)
    prompt = (f"portrait of a {ORION_FEATURES[h % len(ORION_FEATURES)]}, "
              f"{ORION_ACCESSORIES[h % len(ORION_ACCESSORIES)]}, "
              f"{ORION_CLOTHING[h % len(ORION_CLOTHING)]}, "
              f"{ORION_POSES[h % len(ORION_POSES)]}, "
              f"{ORION_BG[h % len(ORION_BG)]}, "
              f"{ORION_SUFFIX}")
    return prompt, int(h)

def build_node5_prompt(code, idx):
    """Node 5: 雅耶奥 Yahyel - 量子态、多重维度"""
    h = int(hashlib.md5(code.encode()).hexdigest(), 16)
    prompt = (f"portrait of a {YAHYEL_FEATURES[h % len(YAHYEL_FEATURES)]}, "
              f"{YAHYEL_ACCESSORIES[h % len(YAHYEL_ACCESSORIES)]}, "
              f"{YAHYEL_CLOTHING[h % len(YAHYEL_CLOTHING)]}, "
              f"{YAHYEL_POSES[h % len(YAHYEL_POSES)]}, "
              f"{YAHYEL_BG[h % len(YAHYEL_BG)]}, "
              f"{YAHYEL_SUFFIX}")
    return prompt, int(h)

def build_node6_prompt(code, idx):
    """Node 6: 昴宿星 Pleiades - 水晶科技、自然光粒"""
    h = int(hashlib.md5(code.encode()).hexdigest(), 16)
    prompt = (f"portrait of a {PLEIADES_FEATURES[h % len(PLEIADES_FEATURES)]}, "
              f"{PLEIADES_ACCESSORIES[h % len(PLEIADES_ACCESSORIES)]}, "
              f"{PLEIADES_CLOTHING[h % len(PLEIADES_CLOTHING)]}, "
              f"{PLEIADES_POSES[h % len(PLEIADES_POSES)]}, "
              f"{PLEIADES_BG[h % len(PLEIADES_BG)]}, "
              f"{PLEIADES_SUFFIX}")
    return prompt, int(h)

def build_node7_prompt(code, idx):
    """Node 7: 阿努纳奇 Annunaki - 原始力量、壮硕"""
    h = int(hashlib.md5(code.encode()).hexdigest(), 16)
    prompt = (f"portrait of a {ANNUNAKI_FEATURES[h % len(ANNUNAKI_FEATURES)]}, "
              f"{ANNUNAKI_ACCESSORIES[h % len(ANNUNAKI_ACCESSORIES)]}, "
              f"{ANNUNAKI_CLOTHING[h % len(ANNUNAKI_CLOTHING)]}, "
              f"{ANNUNAKI_POSES[h % len(ANNUNAKI_POSES)]}, "
              f"{ANNUNAKI_BG[h % len(ANNUNAKI_BG)]}, "
              f"{ANNUNAKI_SUFFIX}")
    return prompt, int(h)

def build_node8_prompt(code, idx):
    """Node 8: 地球/盖亚 Gaia - 大地女神、植物缠绕"""
    h = int(hashlib.md5(code.encode()).hexdigest(), 16)
    prompt = (f"portrait of a {GAIA_FEATURES[h % len(GAIA_FEATURES)]}, "
              f"{GAIA_ACCESSORIES[h % len(GAIA_ACCESSORIES)]}, "
              f"{GAIA_CLOTHING[h % len(GAIA_CLOTHING)]}, "
              f"{GAIA_POSES[h % len(GAIA_POSES)]}, "
              f"{GAIA_BG[h % len(GAIA_BG)]}, "
              f"{GAIA_SUFFIX}")
    return prompt, int(h)

def build_node9_prompt(code, idx):
    """Node 9: 大角星 Arcturus - 几何之光、蓝紫肤"""
    h = int(hashlib.md5(code.encode()).hexdigest(), 16)
    prompt = (f"portrait of an {ARCTURUS_FEATURES[h % len(ARCTURUS_FEATURES)]}, "
              f"{ARCTURUS_ACCESSORIES[h % len(ARCTURUS_ACCESSORIES)]}, "
              f"{ARCTURUS_CLOTHING[h % len(ARCTURUS_CLOTHING)]}, "
              f"{ARCTURUS_POSES[h % len(ARCTURUS_POSES)]}, "
              f"{ARCTURUS_BG[h % len(ARCTURUS_BG)]}, "
              f"{ARCTURUS_SUFFIX}")
    return prompt, int(h)

NODE_BUILDERS = {
    1: build_node1_prompt,
    2: build_node2_prompt,
    3: build_node3_prompt,
    4: build_node4_prompt,
    5: build_node5_prompt,
    6: build_node6_prompt,
    7: build_node7_prompt,
    8: build_node8_prompt,
    9: build_node9_prompt,
}

NODE_NAMES = {
    1: "灰人联邦 Grey",
    2: "艾莎莎尼 Essassani",
    3: "天狼星 Sirius",
    4: "猎户座 Orion",
    5: "雅耶奥 Yahyel",
    6: "昴宿星 Pleiades",
    7: "阿努纳奇 Annunaki",
    8: "地球/盖亚 Gaia",
    9: "大角星 Arcturus",
}

def generate_one(code, prompt, seed, node):
    prompt_enc = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{prompt_enc}?width=768&height=1024&seed={seed}&model=flux&nologo=true"
    
    for attempt in range(5):
        try:
            resp = requests.get(url, timeout=120)
            if resp.status_code == 200 and len(resp.content) > 50000:
                with open(os.path.join(IMG_DIR, f'code_{code}.jpg'), 'wb') as f:
                    f.write(resp.content)
                return True
            elif resp.status_code == 429:
                wait = 60 * (attempt + 1)
                print(f'  ⏳ 429限速, 等{wait}秒...', flush=True)
                time.sleep(wait)
            else:
                time.sleep(5 + attempt * 3)
        except Exception as e:
            time.sleep(5 + attempt * 3)
    return False

def _extract_node(code):
    """从code提取node编号"""
    if len(code) < 3:
        return None
    d1 = int(code[0])
    d2 = int(code[1])
    d3 = int(code[2])
    if 1 <= d1 <= 9:
        return d1
    return None

# ============================================================
# 主流程
# ============================================================

# 读取v18目标codes（从quality_scan_v17.json中筛选出有问题的codes）
import json
with open(r'D:\AAA我的文件\慈海九宫格_整合版\quality_scan_v17.json', encoding='utf-8') as f:
    v17_report = json.load(f)

# 从categories提取所有问题code（非0开头 = 属于Node 1-9的长者图）
all_problem_codes = []
for cat, items in v17_report.get('categories', {}).items():
    for item in items:
        code = item.get('code', '')
        if code and not code.startswith('0'):
            all_problem_codes.append(code)

# 去重+排序
all_problem_codes = sorted(list(set(all_problem_codes)))
problem_codes = [c for c in all_problem_codes if _extract_node(c) is not None]

print('=' * 70)
print('慈海九宫格 v18 - 9种族风格差异化重生成系统')
print(f'总待重生成: {len(problem_codes)} 张')
print('=' * 70)
print()

# 按node分组统计
from collections import defaultdict
by_node = defaultdict(int)
for code in problem_codes:
    n = _extract_node(code)
    if n:
        by_node[n] += 1

print('各节点待重生成数量:')
for n in range(1, 10):
    if n in by_node:
        print(f'  Node {n} ({NODE_NAMES[n]}): {by_node[n]} 张')
print()

# 断点恢复
done_set = set()
if os.path.exists(DONE_LOG):
    with open(DONE_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^(\d+)$', line.strip())
            if m:
                done_set.add(m.group(1))

need = [c for c in problem_codes if c not in done_set]

success = 0
fail = 0
start = time.time()

with open(DONE_LOG, 'a', encoding='utf-8') as log_f:
    for i, code in enumerate(need):
        node = _extract_node(code)
        elapsed = time.time() - start
        rate = (i + 1) / max(elapsed, 0.1)
        remain_sec = (len(need) - i - 1) / max(rate, 0.01)
        
        if node is None or node not in NODE_BUILDERS:
            print(f'[{i+1}/{len(need)}] code={code} | 无对应节点，跳过')
            continue
            
        node_name = NODE_NAMES[node]
        print(f'[{i+1}/{len(need)}] code={code} [{node_name}] | ~{remain_sec/60:.0f}min剩余', flush=True)
        
        prompt, seed = NODE_BUILDERS[node](code, i)
        
        ok = generate_one(code, prompt, seed, node)
        
        if ok:
            success += 1
            log_f.write(f'{code}\n')
            log_f.flush()
            print(f'  ✓ done', flush=True)
        else:
            fail += 1
            print(f'  ✗ FAILED', flush=True)
        
        time.sleep(1.5)

total = time.time() - start
print(f"\n重生成完成: 成功{success} 失败{fail} 耗时{total/60:.1f}分钟")

# 更新deities.js
print("更新 deities.js...", flush=True)
with open(DEITIES_FILE, encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
changed = 0
new_lines = []
for line in lines:
    cm = re.search(r'code:\s*"(\d+)"', line)
    im = re.search(r'image:\s*"([^"]*)"', line)
    if cm and im:
        c = cm.group(1)
        old = im.group(1)
        new = f'generated-images/code_{c}.jpg'
        if os.path.exists(os.path.join(IMG_DIR, f'code_{c}.jpg')) and old != new:
            new_lines.append(line.replace(old, new))
            changed += 1
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

shutil.copy2(DEITIES_FILE, DEITIES_FILE + '.bak_v18')
with open(DEITIES_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print(f"deities.js: {changed}个路径更新", flush=True)
print("全部完成!")
