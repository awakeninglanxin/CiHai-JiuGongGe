"""
慈海九宫格 - v14 佛教/道家庄严相好版
基于《三十二相》与东方佛像美学重新设计提示词
单线程、断点续传、429智能退避、自动更新deities.js
"""
import os, sys, time, random, hashlib, re, shutil, requests

sys.stdout.reconfigure(line_buffering=True)

PROJECT = r'D:\AAA我的文件\慈海九宫格_整合版'
IMG_DIR = os.path.join(PROJECT, 'generated-images')
DEITIES_FILE = os.path.join(PROJECT, 'deities.js')
DONE_LOG = os.path.join(PROJECT, 'v14_done.txt')

# ============================================================
# 佛教/道家庄严相好提示词模板库
# 核心特征：三十二相 + 八十随形好 + 东方美感
# ============================================================

# 共享的核心相好描述（所有模板通用）
CORE_MARKS = (
    "ushnisha cranial protuberance (顶上肉髻相), "
    "urna white curl between eyebrows (眉间白毫相), "
    "long pendulous earlobes touching shoulders (耳垂垂肩相), "
    "golden radiant skin (身金色相), "
    "blue-black hair curling rightward (身毛右旋相), "
    "compassionate deep blue eyes like lotus petals (目绀青色相), "
    "cow-king eyelashes long and orderly (眼睫如牛王相), "
    "broad rounded shoulders (两肩圆满相), "
    "webbed fingers and toes (手足缦网相), "
    "dharmachakra wheel marks on palms and soles (手足轮相), "
    "forty even white teeth (四十齿相), "
    "broad long tongue (广长舌相), "
    "lion-like jaw (两颊隆满相), "
    "straight upright posture (身形端直相)"
)

# 共享背景选项
BACKGROUNDS = [
    "pure land with lotus pond and jeweled trees, soft golden dawn light",
    "ancient temple hall with sandalwood incense, warm candlelight glow",
    "auspicious five-colored clouds, celestial palace with flying apsaras",
    "wutai mountain sacred peak, misty pine forest, morning light",
    "lotus throne floating on seven-jeweled pond, surrounded by blooming lotuses",
    "cave temple with thousand buddhas mural, soft amber lighting",
    "bamboo grove meditation site, dappled sunlight, tranquil atmosphere",
    "jade terrace with railings, moonlit night, gentle breeze",
]

# 共享手印选项
MUDRAS = [
    "dharmachakra mudra (转法轮印) - teaching gesture",
    "bhumisparsha mudra (触地印) - earth witness gesture",
    "dhyana mudra (禅定印) - meditation gesture in lap",
    "abhaya mudra (施无畏印) - fearlessness gesture, right hand raised",
    "varada mudra (施愿印) - wish-granting gesture, left hand extended downward",
    "vitarka mudra (说法印) - discourse gesture, thumb and index touching",
    "anjali mudra (合掌印) - prayer gesture at heart center",
    "uttarabodhi mudra (最高菩提印) - supreme enlightenment gesture",
]

# 共享持物/法器选项
ATTRIBUTES = [
    "holding a crystal lotus stem blooming at shoulder",
    "holding a wish-fulfilling jewel (cintamani) radiating light",
    "holding a dharma wheel (dharmachakra) with eight spokes",
    "holding a vajra scepter and bell (金刚铃杵)",
    "holding a sutra scroll with golden Sanskrit letters",
    "holding a willow branch and pure water vase (净瓶杨枝)",
    "holding a mala prayer beads (念珠) with 108 beads",
    "empty hands displaying mudra only",
]

# 共享光背/舟相选项
MANDORLAS = [
    "full body mandorla (舟光/身光) with lotus petal rays in gold and coral",
    "head halo (头光) with seven concentric rings of rainbow light",
    "double mandorla head and body with flame-pattern border (火焰光背)",
    "lotus petal mandorla with seven jeweled tiers (七宝莲花光背)",
    "simple circular nimbus with golden radiating lines (圆光)",
]

# ============================================================
# 10大类神祇/圣者模板 - 各具特色但都具足三十二相
# ============================================================

STYLE_TEMPLATES = [
    # 1. 如来佛陀类 - 庄严圆满，金色身，转法轮印
    dict(
        category="tathagata",
        title="如来正觉",
        base="portrait of a tathagata buddha, perfectly enlightened one, "
             "golden luminous skin (身金色相), ushnisha topped with lotus bud jewel, "
             "urna glowing softly between eyebrows, long pendulous earlobes, "
             "deep compassionate blue lotus eyes, rightward curling blue-black hair in snail-shell curls, "
             "broad lion-like shoulders, straight upright posture, "
             "dharmachakra mudra (转法轮印) at chest level, "
             "seated on thousand-petaled lotus throne, "
             "{background}, {mandorla}, "
             "classical Chinese Buddhist art style, Dunhuang mural elegance meets Song dynasty sculpture realism, "
             "masterpiece quality, divine serenity, boundless compassion",
        eyes_options=["deep compassionate blue lotus eyes", "serene wisdom eyes like autumn water", "all-seeing compassionate gaze"],
    ),

    # 2. 大菩萨类 - 慈悲庄严，白色/金色身，持莲花/净瓶
    dict(
        category="bodhisattva",
        title="大菩萨",
        base="portrait of a mahasattva bodhisattva, great compassionate being, "
             "radiant golden-white skin (身金色相), tall ushnisha with jeweled crown, "
             "urna white curl, long earlobes adorned with pearl earrings, "
             "gentle compassionate blue eyes, rightward curling hair in high topknot with loose strands, "
             "crown with five buddhas (五佛冠), jeweled ornaments (璎珞), celestial silks, "
             "{attribute}, {mudra}, "
             "seated in royal ease (遊戲坐) on lotus throne, "
             "{background}, {mandorla}, "
             "Tang dynasty Buddhist sculpture style, Yungang/Grottoes aesthetic, "
             "ethereal grace, infinite compassion, supreme elegance",
        eyes_options=["gentle compassionate blue eyes", "loving-kindness eyes like mother gazing at child", "peaceful wisdom eyes"],
    ),

    # 3. 阿罗汉/大弟子类 - 瘦骨嶙峋却庄严，深邃目光，持钵/拂尘
    dict(
        category="arhat",
        title="阿罗汉/大圣弟子",
        base="portrait of an arhat, worthy one who has destroyed defilements, "
             "mature weathered golden skin showing wisdom, ushnisha clear, "
             "urna between brows, long pendulous earlobes from renunciation, "
             "deep penetrating blue eyes with supernatural clarity, "
             "close-cropped blue-black curls or shaven head with ushnisha prominent, "
             "lean ascetic frame yet seven protrusions full (七处隆满相), "
             "patched kasaya robe (袈裟) in ochre/saffron, "
             "{attribute}, {mudra}, "
             "seated on rock seat in mountain cave, "
             "{background}, {mandorla}, "
             "Song dynasty arhat painting style (宋版罗汉图), Li Gonglin linework elegance, "
             "profound realization, tranquil power, ancient wisdom",
        eyes_options=["penetrating wisdom eyes", "liberated gaze beyond duality", "compassionate yet fierce insight"],
    ),

    # 4. 护法神/金刚力士类 - 威猛护法，青蓝/红身，持金刚杵，忿怒相中含慈悲
    dict(
        category="dharmapala",
        title="护法金刚/力士",
        base="portrait of a dharmapala vajra protector, wrathful deity manifestation, "
             "deep lapis lazuli blue or coral red skin (威德身相), "
             "flaming ushnisha with skull crown (五骨冠), third eye (urna) blazing, "
             "long earlobes with bone ornaments, "
             "three round bulging eyes (牛王睫相) fierce yet compassionate, "
             "upward flaming hair (发竖相), tiger skin loincloth, snake ornaments, "
             "holding vajra (金刚杵) raised high, {mudra}, "
             "standing in pratyalidha posture (阿利多步) on lotus-sun disc, "
             "surrounded by wisdom fire (智慧火焰), "
             "{background}, {mandorla}, "
             "Tibetan thangka style meets Chinese temple guardian sculpture, "
             "fierce compassion, protective power, awe-inspiring majesty",
        eyes_options=["three blazing wisdom eyes", "fierce compassionate gaze", "all-seeing protector eyes"],
    ),

    # 5. 道家真人/仙官类 - 道骨仙风，鹤发童颜，长眉垂耳，持拂尘/剑
    dict(
        category="zhenren",
        title="道家真人/仙官",
        base="portrait of a zhenren (true person) daoist immortal, "
             "radiant peach-golden complexion (童颜鹤发相), high forehead (天庭饱满), "
             "long slender eyebrows reaching temples (眉长过目), "
             "large pendulous earlobes touching shoulders (耳垂垂肩, 福寿长耳), "
             "deep dark eyes like hidden pearls (目若藏珠), "
             "long white hair and beard flowing, tied in topknot with jade hairpin, "
             "wearing flowing cloud-patterned daoist robe (云鹤道袍), jade belt, "
             "{attribute}, {mudra}, "
             "seated on crane-back or cloud throne, "
             "{background}, {mandorla}, "
             "Ming/Qing daoist painting style, Quanzhen School aesthetic, "
             "transcendent refinement, vital spirit (元神), harmony with dao",
        eyes_options=["bright spirited eyes like morning stars", "deep still eyes reflecting cosmos", "lively wise eyes with inner light"],
    ),

    # 6. 文殊/普贤/观音/地藏四大菩萨 - 各有标志性法器/坐骑
    dict(
        category="four_bodhisattvas",
        title="四大菩萨",
        base="portrait of a great bodhisattva of the four sacred mountains, "
             "radiant golden-white skin, ushnisha with five-buddha crown, "
             "urna glowing, long pendulous earlobes, compassionate blue lotus eyes, "
             "rightward curling hair in jeweled topknot, "
             "full princely ornaments (璎珞臂钏), celestial silks, "
             "{specific_attribute}, {mudra}, "
             "seated on {mount} throne amid auspicious clouds, "
             "{background}, {mandorla}, "
             "classical Chinese Buddhist sculpture, Dunhuang + Tang elegance, "
             "supreme compassion, perfect wisdom, miraculous manifestation",
        specific_attributes=[
            "holding flaming wisdom sword (文殊剑) and lotus with sutra (文殊菩萨)",
            "holding wish-fulfilling jewel (如意珠) riding white elephant (普贤菩萨)",
            "holding willow branch and pure vase (杨枝净瓶) amid lotus pond (观音菩萨)",
            "holding six-ringed staff (锡杖) and wish-fulfilling jewel (地藏菩萨)",
        ],
        mounts=["lion (狮子)", "six-tusked elephant (六牙白象)", "lotus throne (莲花台)", "lotus throne (莲花台)"],
        eyes_options=["boundless compassion eyes", "wisdom illuminating all beings", "motherly loving gaze"],
    ),

    # 7. 十方佛/药师/阿弥陀/大日等 - 不同本尊色相手印
    dict(
        category="specific_buddhas",
        title="十方诸佛/本尊",
        base="portrait of a specific tathagata, {buddha_name}, "
             "{skin_color} luminous skin, ushnisha with {crown}, "
             "urna white curl, long earlobes, {eyes_desc}, "
             "rightward curling blue-black snail curls, "
             "broad shoulders, straight posture, {mudra}, "
             "seated on jeweled lotus throne in pure land palace, "
             "{background}, {mandorla}, "
             "Tang dynasty imperial Buddhist art, highest ritual standard, "
             "inconceivable merit, supreme blessing",
        buddhas=[
            ("药师琉璃光如来", "lapis lazuli blue (琉璃光色)", "jeweled crown", "holding myrobalan fruit (诃子) in right hand, left in meditation mudra", "medicine buddha pure land with seven-jeweled ground"),
            ("阿弥陀佛", "golden red (紫金色)", "crown with standing buddha", "amitabha meditation mudra (弥陀定印) thumbs touching", "western pure land with lotus ponds and jeweled trees"),
            ("大日如来", "white gold (日轮色)", "five-wisdom crown", "vajra realm mudra (智拳印) or dharmadhatu mudra (法界定印)", "lotus treasury world (莲华藏世界)"),
            ("释迦牟尼佛", "golden (紫磨金色)", "ushnisha only", "bhumisparsha mudra (触地印) calling earth to witness", "bodh gaya vajra seat under bodhi tree"),
            ("弥勒佛", "golden", "crown with stupa", "dharmachakra mudra (转法轮印) or maitreya gesture", "tushita heaven inner court (兜率内院)"),
        ],
        eyes_options=["compassionate all-seeing eyes", "wisdom eyes penetrating illusion", "liberating gaze"],
    ),

    # 8. 天部/龙神/八部众 - 护法善神，威仪整肃
    dict(
        category="deva_naga",
        title="天龙八部/护法善神",
        base="portrait of a {deva_type}, celestial guardian, "
             "radiant {skin_tone} skin, ushnisha or jeweled crown, "
             "urna mark, long earlobes, {eyes_desc}, "
             "rightward curling hair or celestial topknot, "
             "divine armor or celestial robes, {attribute}, {mudra}, "
             "standing on cloud lotus, {background}, {mandorla}, "
             "Dunhuang celestial being style (飞天/天王像), "
             "dignified protection, righteous power, auspicious presence",
        deva_types=["梵天", "帝释天", "四大天王", "龙王", "紧那罗", "摩睺罗伽", "乾闼婆", "阿修罗王"],
        skin_tones=["golden white", "deep blue", "coral red", "emerald green", "sapphire blue"],
        eyes_options=["watchful protective eyes", "righteous dignified gaze", "compassionate guardian eyes"],
    ),

    # 9. 祖师/高僧/传法大德 - 歷史实有，风骨清峻
    dict(
        category="patriarch",
        title="祖师/高僧大德",
        base="portrait of a great patriarch {patriarch_name}, lineage holder, "
             "mature golden skin with wisdom lines, clear ushnisha, "
             "urna between brows, long earlobes from monastic life, "
             "deep compassionate blue eyes, white hair and beard (白毫相现), "
             "wearingpatched kasaya and sitting cloth (坐具), "
             "{attribute}, {mudra}, "
             "seated in meditation hall or mountain hermitage, "
             "{background}, {mandorla}, "
             "Song dynasty portrait painting (宋代高僧像), realistic bone method (骨法用笔), "
             "transmission mind seal, living dharma, venerable presence",
        patriarchs=["达摩祖师", "六祖慧能", "马祖道一", "百丈怀海", "黄檗希运", "赵州从谂", "临济义玄", "曹山本寂", "洞山良价", "永明延寿", "莲池莲池", "印光大师", "弘一大师"],
        eyes_options=["penetrating dharma eye", "kind grandfatherly gaze", "awakened clear vision"],
    ),

    # 10. 女性圣者/度母/吉祥天女 - 庄严柔和，母性慈悲
    dict(
        category="female_saint",
        title="女性圣者/度母/天女",
        base="portrait of a {female_type}, female awakened being, "
             "radiant {skin_tone} golden skin, ushnisha with jeweled crown, "
             "urna glowing, long pendulous earlobes, "
             "gentle compassionate blue lotus eyes, "
             "rightward curling hair in elegant topknot with loose strands framing face, "
             "crowned with five buddhas, adorned with bodhisattva ornaments, "
             "{attribute}, {mudra}, "
             "seated on lotus throne in pure realm, "
             "{background}, {mandorla}, "
             "Tang dynasty female bodhisattva sculpture meets thangka elegance, "
             "supreme feminine wisdom, mother of all buddhas, boundless compassion",
        female_types=["绿度母", "白度母", "吉祥天女", "功德天", "大黑天母", "玛昂吉"],
        skin_tones=["emerald green", "pearl white", "golden yellow", "golden white", "deep blue", "coral red"],
        eyes_options=["motherly compassionate gaze", "swift activity eyes", "loving protective eyes"],
    ),
]

# 通用随机选择器
random.seed(42)

def pick(lst):
    return random.choice(lst)

def build_prompt(code, idx):
    template = STYLE_TEMPLATES[idx % len(STYLE_TEMPLATES)]
    code_hash = int(hashlib.md5(code.encode()).hexdigest(), 16)
    
    # 确定性选择各要素
    bg = BACKGROUNDS[code_hash % len(BACKGROUNDS)]
    mandorla = MANDORLAS[code_hash % len(MANDORLAS)]
    mudra = MUDRAS[code_hash % len(MUDRAS)]
    attribute = ATTRIBUTES[code_hash % len(ATTRIBUTES)]
    eye_var = pick(template.get("eyes_options", ["compassionate blue lotus eyes"]))
    
    # 模板特定变量
    base = template["base"]
    
    # 喵
    # 替换通用变量
    base = base.replace("{background}", bg)
    base = base.replace("{mandorla}", mandorla)
    base = base.replace("{mudra}", mudra)
    base = base.replace("{attribute}", attribute)
    base = base.replace("{eyes_desc}", eye_var)
    
    # 模板特定变量替换
    if "{specific_attribute}" in base:
        specs = template["specific_attributes"]
        base = base.replace("{specific_attribute}", specs[code_hash % len(specs)])
    if "{mount}" in base:
        mounts = template["mounts"]
        base = base.replace("{mount}", mounts[code_hash % len(mounts)])
    if "{buddha_name}" in base:
        buddhas = template["buddhas"]
        buddha = buddhas[code_hash % len(buddhas)]
        base = base.replace("{buddha_name}", buddha[0])
        base = base.replace("{skin_color}", buddha[1])
        base = base.replace("{crown}", buddha[2])
        base = base.replace("{mudra}", buddha[3])  # 覆盖通用mudra
        base = base.replace("{background}", buddha[4])  # 覆盖背景
    if "{deva_type}" in base:
        base = base.replace("{deva_type}", pick(template["deva_types"]))
    if "{skin_tone}" in base:
        base = base.replace("{skin_tone}", pick(template["skin_tones"]))
    if "{patriarch_name}" in base:
        base = base.replace("{patriarch_name}", pick(template["patriarchs"]))
    if "{female_type}" in base:
        ftype = pick(template["female_types"])
        base = base.replace("{female_type}", ftype)
    if "{skin_tone}" in base:  # female也可能有skin_tone
        base = base.replace("{skin_tone}", pick(template["skin_tones"]))
    
    # 最终prompt组装
    prompt = (f"{base}, {CORE_MARKS}, "
              f"classical Chinese Buddhist art masterpiece, "
              f"Dunhuang mural color palette, Tang sculpture volume, "
              f"Song dynasty ink line elegance, "
              f"semi-realistic divine portraiture, "
              f"4k resolution, perfect anatomy, "
              f"sacred geometry composition, "
              f"divine light rendering, subsurface scattering on golden skin, "
              f"museum quality, spiritual presence palpable")
    
    return prompt, int(code_hash)

def generate_one(code, prompt, seed):
    prompt_enc = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{prompt_enc}?width=768&height=768&seed={seed}&model=flux&nologo=true"
    
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

# === 断点恢复 ===
done_set = set()
if os.path.exists(DONE_LOG):
    with open(DONE_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^(\d+)$', line.strip())
            if m:
                done_set.add(m.group(1))

# 扫描实际已有图片
existing = set()
for f in os.listdir(IMG_DIR):
    m = re.match(r'^code_(\d+)\.jpg$', f)
    if m:
        existing.add(m.group(1))

with open(DEITIES_FILE, encoding='utf-8') as f:
    js = f.read()
all_codes = sorted(set(re.findall(r'code:\s*"(\d+)"', js)))

# 真正需要生成的
complete = existing | done_set
need = [c for c in all_codes if c not in complete]

print("=" * 70)
print("慈海九宫格 v14 - 佛教/道家庄严相好版 (三十二相具足)")
print(f"实际已有: {len(existing)} | 断点恢复: {len(done_set)} | 需生成: {len(need)}")
print("核心相好: 肉髻、白毫、垂耳、金身、右旋毛、绀青目、牛王睫、圆肩、缦网、轮相、四十齿、广长舌、狮子颊、直身...")
print("=" * 70)

success = 0
fail = 0
start = time.time()

with open(DONE_LOG, 'a', encoding='utf-8') as log_f:
    for i, code in enumerate(need):
        elapsed = time.time() - start
        rate = (i + 1) / max(elapsed, 0.1)
        remain_sec = (len(need) - i - 1) / max(rate, 0.01)
        
        print(f'[{i+1}/{len(need)}] code={code} | {remain_sec/60:.0f}min剩余', flush=True)
        
        prompt, seed = build_prompt(code, i)
        ok = generate_one(code, prompt, seed)
        
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
print(f"\n生成完成: 成功{success} 失败{fail} 耗时{total/60:.1f}分钟")

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

shutil.copy2(DEITIES_FILE, DEITIES_FILE + '.bak_v14')
with open(DEITIES_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print(f"deities.js: {changed}个路径更新", flush=True)

# 最终统计
final_codes = set()
for f in os.listdir(IMG_DIR):
    m = re.match(r'^code_(\d+)\.jpg$', f)
    if m:
        final_codes.add(m.group(1))
matching = len(final_codes & set(all_codes))
missing = len(all_codes) - matching
print(f"\n=== 最终: {matching}/{len(all_codes)} | 缺失: {missing} ===", flush=True)