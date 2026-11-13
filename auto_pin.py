import os, re, io, glob, time, json, uuid, random, urllib.parse
from email.utils import formatdate
from xml.sax.saxutils import escape
import requests
from PIL import Image, ImageOps

GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
SITE_URL = "https://catherinewilliamshub.github.io"
HISTORY_FILE = "pins_history_v3.json"

BOARDS_CONFIG = {
    "nails": {
        "board_name": "Trending Nails",
        "xml_file": "nails.xml",
        "instruction": "Mention nail shape (Almond/Coffin), colors, and salon tips.",
        "hashtags": "#TrendingNails #NailArtDesigns #AlmondNails #AcrylicNails #ManicureInspo",
        "style": "Clear studio photograph of a woman's graceful full hand resting on a cozy cream knit sweater, all five manicured fingernails clearly visible from normal distance, f/8 aperture, everything in sharp focus, zero blur, bright salon lighting, 8k, no text",
        "topics": [
            "glossy lavender and blue ombre almond nails with delicate butterfly nail art",
            "milky pink almond nails with clean white floral petals and thin gold lines",
            "royal blue and gold marble swirl coffin acrylic nails with glossy topcoat",
            "classic pink French tip almond nails with tiny red cherry nail art",
            "icy blue glitter ombre almond nails with clean silver chrome tips",
            "burgundy red and nude swirl almond gel nails with gold foil accents"
        ],
        "backup": [
            "https://images.unsplash.com/photo-1604654894610-df63bc536371?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1632345031435-8727f6897d53?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1519014816548-bf5fe059798b?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1607779097040-26e80aa78e66?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1610992015732-2449b76344bc?w=1080&h=1620&fit=crop&q=95"
        ]
    },
    "homedecor": {
        "board_name": "Home Decor",
        "xml_file": "homedecor.xml",
        "instruction": "Include 3 interior styling tips to recreate this cozy look in a US home.",
        "hashtags": "#HomeDecor #CozyHome #LivingRoomDecor #InteriorDesignIdeas #ApartmentDecor",
        "style": "Wide angle Architectural Digest interior design photograph, warm natural sunlight, beige and oak wood aesthetic, f/8 aperture, sharp focus throughout room, zero blur, 8k, no text",
        "topics": [
            "cozy neutral living room with cream cloud sofa, knit pillows, oak coffee table, and arched mirror",
            "modern farmhouse kitchen with white quartz island, brass pendant lights, and wooden barstools",
            "aesthetic small bedroom with beige linen bedding, warm fairy lights, and indoor plants",
            "luxury bathroom with freestanding tub, backlit round mirror, and wooden bath tray",
            "cozy apartment balcony at dusk with warm string lights, rattan chair, and olive trees"
        ],
        "backup": [
            "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1080&h=1620&fit=crop&q=95"
        ]
    },
    "pets": {
        "board_name": "Must-Have Pet Products & Care",
        "xml_file": "pets.xml",
        "instruction": "Highlight why this pet product is a must-have for US pet owners, plus 2 care tips.",
        "hashtags": "#PetProducts #DogMomMustHaves #CatFurniture #CozyPetHome #PetCareTips",
        "style": "Full-frame commercial pet lifestyle photograph in a bright clean American living room, f/8 sharp focus on both the pet product and cute pet, natural daylight, zero blur, 8k, no text",
        "topics": [
            "cute Golden Retriever puppy resting inside a round cream plush orthopedic donut dog bed on hardwood floor",
            "fluffy gray cat sitting on a modern wooden cat tree tower with white cushions in a bright living room",
            "bamboo dog feeding station with two white ceramic bowls beside a cute French Bulldog",
            "modern white ceramic pet water fountain and automatic feeder in a clean kitchen beside a tabby cat",
            "cute Dachshund puppy wearing a sage-green padded dog harness and leash on a cozy rug"
        ],
        "backup": [
            "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1537151608828-ea2b11777ee8?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=1080&h=1620&fit=crop&q=95"
        ]
    },
    "beauty": {
        "board_name": "Health and Beauty Routines",
        "xml_file": "beauty.xml",
        "instruction": "Include a step-by-step routine order (Step 1, Step 2, Step 3) for women to save.",
        "hashtags": "#SkincareRoutine #GlowingSkinTips #BeautyRoutine #SelfCareAesthetic #CleanBeauty",
        "style": "Clean overhead flat-lay beauty photograph on a white marble counter, bright morning light, f/8 sharp focus across all bottles and jars, zero blur, 8k commercial photography, no text",
        "topics": [
            "esthetic skincare lineup with frosted glass serum dropper bottles, cream jar, and rose quartz roller on marble tray",
            "evening skincare arrangement with amber glass serum bottle, moisturizer jar, and silk sleep mask",
            "hair care flat-lay with glass rosemary oil bottle, wooden paddle brush, scalp massager, and silk scrunchies",
            "spa shower essentials with pink body scrub jar, body oil bottle, wooden dry brush, and folded white towels"
        ],
        "backup": [
            "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1612817288484-6f916006741a?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1608248597359-0e6d526a6828?w=1080&h=1620&fit=crop&q=95"
        ]
    },
    "diet": {
        "board_name": "Healthy Diet & Weight Loss Meals",
        "xml_file": "diet.xml",
        "instruction": "Include estimated Calories & Protein macros, plus ingredients and quick prep steps.",
        "hashtags": "#HighProteinMeals #HealthyMealPrep #WeightLossRecipes #LowCalorieMeals #CleanEating",
        "style": "Overhead food magazine table photograph on white marble counter, vibrant fresh ingredients, f/8 sharp focus across the entire meal, natural daylight, zero blur, 8k, no text",
        "topics": [
            "high-protein meal prep bowls with grilled chicken breast, sliced avocado, roasted sweet potato, and broccoli",
            "green smoothie in a clear glass jar topped with fresh berries, chia seeds, and sliced almonds",
            "pan-seared salmon fillet with roasted asparagus and lemon wedges on a white ceramic plate",
            "three mason jars filled with overnight oats, chia seeds, and fresh blueberries and strawberries"
        ],
        "backup": [
            "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=1080&h=1620&fit=crop&q=95"
        ]
    }
}

def load_history():
    # আগের সব ঘোলা ও খারাপ ছবি অটোমেটিক ডিলিট করে ফ্রেশ শুরু করা
    if not os.path.exists(HISTORY_FILE):
        for old_f in ["pins_history.json", "pins_history_v2.json"]:
            if os.path.exists(old_f):
                os.remove(old_f)
        for old_img in glob.glob("images/*.jpg"):
            try: os.remove(old_img)
            except Exception: pass
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {k: [] for k in BOARDS_CONFIG}

def generate_pin_content(cfg, topic):
    full_img_prompt = f"{topic}. {cfg['style']}"
    prompt = f"""Create a viral US Pinterest Pin for board "{cfg['board_name']}" on topic "{topic}".
    {cfg['instruction']}
    Respond ONLY in JSON: {{"title": "Catchy SEO title under 85 chars", "description": "SEO description (250-380 chars) ending with {cfg['hashtags']}"}}"""

    for model in ["gemini-flash-lite-latest", "gemini-2.0-flash-lite", "gemini-2.0-flash"]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=25)
            if r.status_code == 200:
                txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                m = re.search(r"\{.*\}", txt, re.DOTALL)
                if m:
                    data = json.loads(m.group(0))
                    data["image_prompt"] = full_img_prompt
                    print(f"✅ Text generated via Gemini ({model})", flush=True)
                    return data
        except Exception:
            pass
    return {
        "title": f"{topic[:65].title()} | Ideas",
        "description": f"Discover {topic}. {cfg['instruction']} {cfg['hashtags']}",
        "image_prompt": full_img_prompt
    }

def save_hd_jpeg(raw_bytes, filepath, crop_bottom=0):
    img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    if crop_bottom > 0 and img.height > 600:
        img = img.crop((0, 0, img.width, img.height - crop_bottom))
    img = ImageOps.fit(img, (1000, 1500), Image.Resampling.LANCZOS)
    img.save(filepath, format="JPEG", quality=95, optimize=True)
    return os.path.getsize(filepath)

def download_image(key, image_prompt, cfg, filename):
    os.makedirs("images", exist_ok=True)
    filepath = os.path.join("images", filename)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # শুধুমাত্র Flux Realism মডেল (enhance=false সহ, যাতে প্রম্পট বিকৃত বা ঘোলা না হয়)
    # কিন্তু Nails বোর্ডে AI আঙুল বিকৃত করার ঝুঁকি এড়াতে সরাসরি আসল সালোন ফটোগ্রাফি বা নিখুঁত Flux ব্যবহার
    if key != "nails":
        clean_p = re.sub(r"[^a-zA-Z0-9, /.-]", "", image_prompt)[:260]
        enc = urllib.parse.quote(clean_p)
        for attempt in range(2):
            try:
                seed = random.randint(10000, 999999)
                flux_url = f"https://image.pollinations.ai/prompt/{enc}?width=1024&height=1536&seed={seed}&model=flux&enhance=false"
                r = requests.get(flux_url, headers=headers, timeout=65)
                if r.status_code == 200 and len(r.content) > 35000:
                    sz = save_hd_jpeg(r.content, filepath, crop_bottom=65)
                    print("✨ Crisp HD Image generated via Flux (enhance=false)!", flush=True)
                    return f"{SITE_URL}/images/{filename}", sz
            except Exception as e:
                print(f"Flux attempt {attempt+1} skipped: {e}", flush=True)
            time.sleep(8)

    # আসল (Real) হাই-রেজোলিউশন পিন্টারেস্ট ফটোগ্রাফি (Nails এবং ব্যাকআপের জন্য ১০০% নিখুঁত ছবি)
    for b_url in random.sample(cfg["backup"], len(cfg["backup"])):
        try:
            r = requests.get(b_url, headers=headers, timeout=30)
            if r.status_code == 200 and len(r.content) > 15000:
                sz = save_hd_jpeg(r.content, filepath)
                print("📸 Real Ultra-HD Salon/Lifestyle Photo saved!", flush=True)
                return f"{SITE_URL}/images/{filename}", sz
        except Exception:
            pass

    raise Exception("Image download failed")

def build_rss(board_title, xml_file, items):
    rss_items = ""
    for it in items[:20]:
        rss_items += f"""
    <item>
      <title>{escape(it['title'])}</title>
      <link>{escape(it['link'])}</link>
      <description>{escape(it['description'])}</description>
      <pubDate>{it['pub_date']}</pubDate>
      <guid isPermaLink="false">{escape(it['guid'])}</guid>
      <enclosure url="{escape(it['image_url'])}" length="{it['length']}" type="image/jpeg"/>
      <media:content url="{escape(it['image_url'])}" type="image/jpeg" medium="image"/>
    </item>"""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>Catherine Williams Hub - {escape(board_title)}</title>
    <link>{SITE_URL}</link>
    <description>Daily US inspiration for {escape(board_title)}</description>{rss_items}
  </channel>
</rss>"""
    with open(xml_file, "w", encoding="utf-8") as f:
        f.write(xml.strip())

if __name__ == "__main__":
    history = load_history()
    for key, cfg in BOARDS_CONFIG.items():
        try:
            topic = random.choice(cfg["topics"])
            print(f"\n📌 Board: {cfg['board_name']} | Topic: {topic}", flush=True)
            content = generate_pin_content(cfg, topic)
            pin_id = str(uuid.uuid4())[:8]
            img_url, img_sz = download_image(key, content["image_prompt"], cfg, f"{key}_{pin_id}.jpg")
            history.setdefault(key, []).insert(0, {
                "guid": f"{key}-{pin_id}",
                "title": content["title"],
                "description": content["description"],
                "link": f"{SITE_URL}/?pin={key}-{pin_id}",
                "image_url": img_url,
                "length": img_sz,
                "pub_date": formatdate(localtime=False, usegmt=True)
            })
            history[key] = history[key][:20]
            build_rss(cfg["board_name"], cfg["xml_file"], history[key])
            print(f"✅ Updated {cfg['xml_file']} successfully!", flush=True)
            time.sleep(10)
        except Exception as e:
            print(f"⚠️ Skipped {key}: {e}", flush=True)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print("\n🎉 All 5 boards processed cleanly!", flush=True)
