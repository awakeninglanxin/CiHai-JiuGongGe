"""
优化版: 为298个code生成独立AI肖像
- 增加重试到5次，间隔更长
- 改用jpg格式(更快)
- 降低分辨率768x768(足够web展示)
- 逐批提交, 每批之间等待2-4秒
"""
import json
import os
import hashlib
import requests
import time
from datetime import datetime

OUTPUT_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual"
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open("D:/temp/generation_jobs.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

# Already completed
existing_files = set()
for fn in os.listdir(OUTPUT_DIR):
    if fn.startswith("code_") and fn.endswith(".jpg"):
        code = fn.split("_")[1]
        existing_files.add(code)

remaining = [j for j in jobs if j['code'] not in existing_files]
print(f"Total jobs: {len(jobs)}")
print(f"Already done: {len(existing_files)}")
print(f"Remaining: {len(remaining)}")

NODE_STYLES = {
    -1: [
        "ancient cosmic deity floating in primordial void, translucent crystalline body with golden veins, ethereal divine light, cinematic portrait, ultra detailed digital painting",
        "celestial sovereign emerging from nebula, robes of iridescent starlight, crown of constellations, divine presence radiating authority, epic fantasy portrait",
        "divine architect of reality, luminous being with geometric sacred patterns, ancient cosmic energy swirling, majestic warrior of light, cinematic lighting",
        "mystical guardian of the multiverse, flowing robes of dark matter and gold leaf, eyes holding galaxies, ethereal portal of light behind, ultra detailed",
        "primordial spirit of the void, ancient being of pure consciousness, body woven from cosmic dust and starlight, ethereal wings of light, majestic portrait",
    ],
    0: [
        "young celestial being in training, robes of dawn light, holding staff of pure energy, gateway between mortal and divine realms, aura of potential, ethereal portrait",
        "awakened soul manifest form, glowing with newborn divine power, swirling spiritual energy, bridge between earth and heaven, luminescent aura, detailed digital painting",
        "spiritual successor channeling cosmic wisdom, youthful yet ancient eyes, garments of shifting light, standing on clouds of intention, serene divine portrait",
    ],
    1: [
        "mysterious scaled warrior emerging from shadow, golden slit eyes, armor forged from volcanic glass, ancient reptilian temple backdrop, fierce expression, cinematic fantasy art",
        "reptilian deity of survival, muscular form with iridescent scales jade to obsidian, claws carving destiny into stone tablets, primal power, epic warrior portrait",
        "ancient reptilian sage, sleek mercury-silver scales, standing amid desert ruins, eyes of ancient wisdom, warrior of the old world, detailed fantasy art",
    ],
    2: [
        "shimmering hybrid being extraordinary beauty, skin shifts gold and violet, eyes of twin flames, wings of crystallized light, perfect synthesis of worlds, ethereal portrait",
        "evolved consciousness humanoid form, multiple arms each holding creative force, body composed of crystallized light, standing at convergence of timelines, divine being",
        "extraordinary cosmic messenger, luminous form between mortal and divine, iridescent wings, aura of transformed potential, master of the threshold, detailed fantasy painting",
    ],
    3: [
        "Sirius light bearer with brilliant white-gold radiance, standing on crystalline platform above vast oceans, three suns in sky, sonic frequency of cosmic music, divine warrior",
        "celestial musician from Sirius, harp made of light beams, each string a frequency of creation, robes woven from pulsar emissions, transcendent beauty, epic portrait",
        "Sirius ambassador of pure light, tall elegant form of polished silver, eyes burning with Dogon star wisdom, surrounded by sound frequencies, majestic being",
    ],
    4: [
        "fierce Orion warrior-god crimson armor studded with binary stars, twin swords of transformation, ancient reptilian temple ruins, burning determination, epic fantasy portrait",
        "Orion enforcer of cosmic justice, blue-steel skin, eyes of burning white fire, spear of truth piercing illusion, dark warrior of justice, dramatic cinematic art",
        "mystical guardian of Orion Belt, three luminous figures merged into one powerful form, robe of nebula patterns, ancient warrior of the cosmos, detailed fantasy painting",
    ],
    5: [
        "chrononaut of immense spatial mastery, folded dimensions background, compass of light pointing to parallel realities, robes showing different time periods, cosmic navigator",
        "spacetime navigator translucent body revealing swirling galaxies, quantum anchor in hand, corridor of infinite doorways, master of time, epic cosmic portrait",
        "architect of spacetime, form constantly rewriting geometric patterns, floating void of mathematical equations made visible, quantum consciousness, transcendent being",
    ],
    6: [
        "Pleiadian mother being extraordinary grace, seven auroras of light halo, rose-gold garments shimmering with interstellar dreams, compassionate healer, ethereal feminine portrait",
        "celestial healer from the Pleiades, hands emanating restorative turquoise light, eyes holding cosmic nurseries where stars are born, tender compassionate being, soft glow",
        "empathic Pleiadian diplomat, form of crystalline water droplets held by love, garden of singing crystal trees, turquoise healing aura, gentle divine beauty",
    ],
    7: [
        "ancient Annunaki overseer lapis lazuli skin golden crown, throne of geological epochs, tablets of destiny with genetic codes, imposing primordial ruler, dark epic portrait",
        "primordial judge of underworld massive bronze form, beard braided with copper wire, eyes of molten gold, keeper of deep earth secrets, ancient king, dramatic fantasy art",
        "Annunaki elder deep earth wisdom, form partially crystalline showing geological strata, crossroads of mineral and spirit kingdoms, ancient stone sage, mystical being",
    ],
    8: [
        "living Earth consciousness magnificent mother figure, hair of flowing rivers skin of rich soil with forests, eyes of glacial ice and ocean depths, Gaia personified, epic portrait",
        "earth elemental sovereign verdigris skin crown of growing vines and flowers, holding pulsing globe of heartbeat, surrounded by symbiotic creatures, nature goddess, lush fantasy art",
        "Gaia herself brought to human form, feet growing roots into planet, breath as wind and weather, surrounded by all life, mother of the world, transcendent divine being",
    ],
    9: [
        "wise Arcturian master of highest octave of love, transcendent violet-white light, infinite compassion in eyes, staff of ascension, robe of crystallized wisdom, enlightened being",
        "cosmic dean of earthly academies serene golden-violet radiance, divine intelligence in hands, seeing through all veils of illusion, master teacher, transcendent portrait",
        "Arcturian light-weaver fingers spinning strands of divine intelligence, pure crystalline frequency form, eyes seeing through all illusions, ascended master, golden violet glow",
    ],
    10: [
        "supreme Jade Emperor cosmic court regalia, twelve-fold crown blazing pure white light, scepter of heavenly mandate, floating above sea of clouds, imperial divine portrait",
        "Fourth Pure Being immaculate white and gold, four faces representing cardinal directions, each holding symbol of cosmic governance, supreme celestial authority, epic painting",
        "celestial sovereign ascending through four dimensions, form multiplying into quadruplicate purity of body mind spirit essence, supreme divine ruler, majestic cosmic portrait",
    ],
    11: [
        "grand master of three pure realms flowing white robes with cloud patterns, triple jewel staff between Heaven Earth Humanity, cosmic administrator, enlightened sage, detailed painting",
        "celestial administrator supreme rank, translucent form showing layers of organizational energy, scrolls of heavenly decrees, master of cosmic bureaucracy, wise ancient being",
        "earth academy dean of the three realms, crown of three stacked circles unity of origin manifestation dissolution, sacred administrative power, transcendent sage portrait",
    ],
    12: [
        "master of duodecimal mathematics robe divided into twelve segments sacred symbols, geometric perfection of twelve, hands forming sacred number, cosmic calculator, divine mathematician",
        "twelve-fold code restorer body of twelve interlocking rings toroidal structure, eyes containing infinite recursion of base-12 wisdom, master of sacred numbers, geometric portrait",
        "cosmic accountant of sacred dozen scales of balanced duality, wall of twelve numbered doors each a dimension, mathematical divinity, transcendent numerologist, detailed fantasy",
    ],
    13: [
        "primordial innate child deity luminous form of perfect potential, crown of jade green light, seed of creation holding universes, divine innocence, baby cosmic being, ethereal portrait",
        "first innate being child form cosmic consciousness, mature eyes innocent smile, halo of unborn possibilities, perfect potential, divine child, luminous baby deity, detailed painting",
        "originary spirit in child form, translucent body showing embryonic starlight, floating in void between existence and non-existence, nascent universe, adorable cosmic being",
    ],
}

def get_style(job):
    """Get unique style prompt for a job based on node + code hash"""
    node = job['node']
    styles = NODE_STYLES.get(node, NODE_STYLES[-1])
    idx = int(hashlib.md5(job['code'].encode()).hexdigest(), 16) % len(styles)
    return styles[idx]

results = {'success': [], 'failed': []}
batch_delay = 2.5

for i, job in enumerate(remaining):
    code = job['code']
    style = get_style(job)
    prompt = f"divine portrait of {code}, {style}"
    encoded = prompt.replace(' ', '%20')
    seed = int(hashlib.md5(code.encode()).hexdigest()[:8], 16)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&nologo=true&seed={seed}&model=flux"
    
    output_file = os.path.join(OUTPUT_DIR, f"code_{code}_{int(time.time()*1000) % 10000000000}.jpg")
    
    downloaded = False
    for attempt in range(5):
        try:
            resp = requests.get(url, timeout=120, stream=True)
            if resp.status_code == 200 and len(resp.content) > 30000:
                with open(output_file, 'wb') as f:
                    f.write(resp.content)
                downloaded = True
                break
        except:
            pass
        time.sleep(batch_delay + attempt * 2)
    
    if downloaded:
        results['success'].append(code)
        print(f"[{i+1}/{len(remaining)}] SUCCESS: {code} (attempt {attempt+1})")
    else:
        results['failed'].append(code)
        print(f"[{i+1}/{len(remaining)}] FAILED: {code} after 5 attempts")
    
    # Pace the requests
    if i % 10 == 9:
        time.sleep(5)  # Longer pause every 10

# Save results
with open(os.path.join(OUTPUT_DIR, "results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n=== Generation Complete ===")
print(f"Success: {len(results['success'])}")
print(f"Failed: {len(results['failed'])}")
if results['failed']:
    print(f"Failed codes: {', '.join(results['failed'][:10])}...")
