"""
批量为298个共用图片的code生成独立的AI肖像
每个code需要独特的提示词，基于其node(文明)和role来差异化
"""
import json
import os
import random
import requests
import time
from threading import Lock, Thread
from datetime import datetime

# Config
OUTPUT_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual"
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open("D:/temp/generation_jobs.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

# Shuffle for randomness
random.seed(42)
jobs = sorted(jobs, key=lambda x: x['group_key'])

# Prompt templates by node type
# node=-1: origin/creation, node=0: acquired, node=1-9: Bashar nodes
NODE_PROMPTS = {
    -1: [  # 本源层/创世层 — various cosmic beings
        "A majestic cosmic entity floating in primordial void, translucent crystalline body with golden veins, ancient wisdom etched in its form, ethereal light emanating from within, divine presence radiating authority",
        "An otherworldly guardian deity emerging from nebulous darkness, robes woven from starlight, eyes holding galaxies, a being of pure consciousness standing atop cosmic waves",
        "Divine architect of reality, a luminous figure with geometric fractal patterns across its body, surrounded by floating sacred symbols, ancient cosmic energy swirling around",
        "A celestial sovereign with flowing robes of iridescent light, crown of constellations on head, standing before the fabric of spacetime itself, commanding the forces of creation",
        "Ancient cosmic librarian of the multiverse, a wise being with eyes like twin suns, holding scrolls of infinite knowledge, draped in robes of woven dark matter and starlight",
    ],
    0: [  # 后天童子 — acquired child realm
        "A young celestial being in training, wearing robes of dawn light, holding a staff of pure energy, standing at the gateway between mortal and divine realms, aura of potential radiating outward",
        "An awakened soul in manifestation form, glowing with newborn divine power, surrounded by swirling spiritual energy, a bridge between earth and heaven",
        "A spiritual successor channeling cosmic wisdom, youthful yet ancient eyes, draped in garments of shifting light, standing on clouds of pure intention",
    ],
    1: [  # 灰人/爬虫 — reptilian themes
        "A mysterious scaled warrior emerging from shadow, golden slit eyes gleaming with strategic intelligence, armor forged from volcanic glass, standing in an ancient reptilian temple",
        "A reptilian deity of survival and dominance, muscular form covered in iridescent scales that shift from jade to obsidian, claws that carve destiny into stone tablets",
        "Ancient guardian of primal instincts, a sleek reptilian sage with mercury-silver scales, standing amid desert ruins of a forgotten civilization",
    ],
    2: [  # 艾莎莎尼/新混血 — hybrid themes
        "A shimmering hybrid being of extraordinary beauty, skin that shifts between gold and violet, eyes of twin flames representing two worlds united in perfect harmony",
        "A being of extraordinary synthesis, half-mortal half-divine with wings of crystallized light, standing at the convergence of all timelines",
        "An evolved consciousness manifested as a radiant humanoid with multiple pairs of arms, each holding a tool of creation — compassion, wisdom, courage, mercy, strength, and love",
    ],
    3: [  # 天狼星 — Sirius themes
        "A luminous Sirius ambassador with radiant white-gold robes, standing on a crystalline platform above vast oceans, three suns visible in the sky behind, voice of cosmic music",
        "A being of pure Sirius light, tall and elegant with skin like polished silver, eyes burning with the wisdom of the Dogon star priests, surrounded by sonic frequencies",
        "A celestial musician from Sirius, holding a harp made of light beams, each string a different frequency of creation, robes woven from pulsar emissions",
    ],
    4: [  # 猎户座 — Orion themes
        "A fierce Orion warrior-god with crimson armor studded with binary stars, twin swords of transformation crossing before him, standing atop the ruins of an old paradigm",
        "An Orion enforcer of cosmic justice, tall and imposing with blue-steel skin, eyes of burning white fire, wielding the spear of truth that pierces illusion",
        "A mystical guardian of the Orion Belt constellation, three luminous figures merged into one powerful being, robe adorned with nebula patterns",
    ],
    5: [  # 雅耶奥 — Yahyel/chrononauts
        "A chrononaut of immense spatial mastery, floating through folded dimensions with a compass of light pointing to parallel realities, wearing robes that show different time periods",
        "A spacetime navigator with translucent body revealing swirling galaxies within, holding a quantum anchor, standing in a corridor of infinite doorways",
        "An architect of spacetime itself, a being whose form is constantly rewriting its own geometry, floating in a void of pure mathematical equations made visible",
    ],
    6: [  # 昴宿星 — Pleiades themes
        "A Pleiadian mother being of extraordinary grace, seven auroras of light surrounding her like a halo, wearing garments of rose-gold that shimmer with interstellar dreams",
        "A celestial healer from the Pleiades, hands emanating pulses of restorative turquoise light, eyes holding the depth of cosmic nurseries where stars are born",
        "An empathic Pleiadian diplomat, form composed of crystalline water droplets held together by love, standing in a garden of singing crystal trees",
    ],
    7: [  # 阿努纳奇 — Annunaki
        "An ancient Annunaki overseer with lapis lazuli skin and golden crown, seated on a throne of geological epochs, holding tablets of destiny inscribed with genetic codes",
        "A primordial judge of the underworld, massive and imposing with skin of living bronze, beard braided with copper wire, eyes of molten gold",
        "An Annunaki elder of deep earth wisdom, form partially crystalline revealing geological strata within, standing at the crossroads of mineral and spirit kingdoms",
    ],
    8: [  # 盖亚/地球 — Gaia
        "The living Earth consciousness manifested as a magnificent mother figure, hair of flowing rivers, skin of rich soil dotted with forests, eyes of glacial ice and ocean depths",
        "Gaia herself brought to human form, a being whose feet grow roots into the planet, whose breath is wind and weather, surrounded by symbiotic creatures",
        "An earth elemental sovereign with verdigris skin, crown of growing vines and blooming flowers, holding a globe that pulses with the heartbeat of every living creature",
    ],
    9: [  # 大角星 — Arcturus
        "A wise Arcturian master of the highest octave of love, form glowing with transcendent violet-white light, eyes holding infinite compassion, robe of crystallized wisdom",
        "The cosmic dean of earthly academies, a serene being radiating golden-violet light, staff of ascension in hand, standing at the threshold of dimensional mastery",
        "An Arcturian light-weaver, fingers spinning strands of divine intelligence, form composed of pure crystalline frequency, eyes that see through all veils of illusion",
    ],
    10: [  # 四清玉皇
        "A supreme Jade Emperor in cosmic court regalia, twelve-fold crown blazing with pure white light, holding the scepter of heavenly mandate, floating above a sea of clouds",
        "The Fourth Pure One, a being of immaculate white and gold, four faces representing cardinal directions, each holding a symbol of cosmic governance",
        "A celestial sovereign ascending through four dimensions, form multiplying into quadruplicate representing purity of body, mind, spirit, and essence",
    ],
    11: [  # 三清院长
        "A grand master of the three清 realms, robes of flowing white with cloud patterns, staff topped with a triple jewel, standing between Heaven Earth and Humanity",
        "The dean of the three pure realms, an embodiment of cosmic administration, form translucent showing layers of organizational energy, holding scrolls of heavenly decrees",
        "A celestial administrator of supreme rank, crown of three stacked circles representing the unity of origin, manifestation, and dissolution",
    ],
    12: [  # 12进制修复者
        "A master of duodecimal mathematics, wearing a robe divided into twelve segments each containing a sacred symbol, hands forming the number twelve in geometric perfection",
        "The twelve-fold code restorer, body composed of twelve interlocking rings forming a toroidal structure, eyes containing the infinite recursion of base-12 wisdom",
        "A cosmic accountant of the sacred dozen, scales of balanced duality hovering before a wall of twelve numbered doors, each door a different dimension",
    ],
    13: [  # 0*先天童子
        "A primordial innate child deity, luminous form of perfect potential, crown of jade green light, holding a seed of creation that contains universes within its tiny frame",
        "The first innate being, a child of cosmic consciousness with mature eyes and innocent smile, surrounded by a halo of unborn possibilities",
        "An originary spirit in child form, translucent body showing embryonic starlight within, floating in the void between existence and non-existence",
    ],
}

# Batch size and threading
BATCH_SIZE = 20
THREADS = 5
MAX_RETRIES = 3

progress_lock = Lock()
completed = 0
failed = []

def get_style_prompt(job):
    """Generate a unique prompt for each code based on group + code variation"""
    base_prompts = NODE_PROMPTS.get(job['node'], NODE_PROMPTS[-1])
    
    # Get position within group for differentiation
    group_name = job['group_key'].split('_2026')[0]
    idx = hash(group_name + job['code']) % len(base_prompts)
    
    base = base_prompts[idx]
    
    # Add unique code-based suffix for differentiation
    suffixes = [
        "with subtle fractal patterns reflecting cosmic destiny",
        "glowing with individual quantum signature energy",
        "surrounded by unique astral aura of personal vibration",
        "featuring distinctive cosmic markings of singular identity",
        "with a unique frequency pattern only this being possesses",
        "radiating a personalized energy field of one-of-a-kind resonance",
        "carrying an emblem of their singular cosmic assignment",
        "with eyes that hold a unique constellation only they represent",
    ]
    suffix_idx = hash(job['code']) % len(suffixes)
    
    prompt = f"{base}, {suffixes[suffix_idx]}, ultra detailed digital art, cinematic lighting, divine portrait"
    return prompt

def generate_single(job):
    global completed, failed
    code = job['code']
    prompt = get_style_prompt(job)
    
    encoded_prompt = prompt.replace(' ', '%20')
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={hash(code)}"
    
    output_file = os.path.join(OUTPUT_DIR, f"code_{code}_{int(time.time())}.png")
    
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=300, stream=True)
            if resp.status_code == 200 and len(resp.content) > 50000:
                with open(output_file, 'wb') as f:
                    f.write(resp.content)
                
                with progress_lock:
                    completed += 1
                    if completed % BATCH_SIZE == 0:
                        print(f"[{completed}/{len(jobs)}] Generated: {code} (attempt {attempt+1})")
                return True
        except Exception as e:
            pass
        
        time.sleep(3 if attempt < MAX_RETRIES - 1 else 10)
    
    with progress_lock:
        failed.append({'code': code, 'error': f'Retried {MAX_RETRIES} times'})
    return False

# Process in batches with threads
def process_batch(start_idx):
    batch = jobs[start_idx:start_idx + BATCH_SIZE]
    for job in batch:
        generate_single(job)
        time.sleep(random.uniform(0.5, 2))  # Rate limiting

# Launch thread pool
threads = []
total_batches = (len(jobs) + BATCH_SIZE - 1) // BATCH_SIZE

for i in range(min(total_batches * 3, THREADS)):  # Max 3 concurrent threads
    t = Thread(target=process_batch, args=(i * BATCH_SIZE,))
    t.start()
    threads.append(t)

# Wait for completion
for t in threads:
    t.join()

# Save progress
with open(os.path.join(OUTPUT_DIR, "progress.json"), "w", encoding="utf-8") as f:
    json.dump({
        'total': len(jobs),
        'completed': completed,
        'failed': failed,
        'timestamp': datetime.now().isoformat()
    }, f, ensure_ascii=False, indent=2)

print(f"\n=== Generation Complete ===")
print(f"Total jobs: {len(jobs)}")
print(f"Completed: {completed}")
print(f"Failed: {len(failed)}")
if failed:
    for item in failed[:5]:
        print(f"  Failed: {item['code']}")
