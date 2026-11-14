import os, re, io, glob, time, json, uuid, random, urllib.parse
from email.utils import formatdate
from xml.sax.saxutils import escape
import requests
from PIL import Image, ImageOps
from gradio_client import Client

GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
HF_TOKEN = (os.environ.get("HF_TOKEN") or "").strip()
SITE_URL = "https://catherinewilliamshub.github.io"
HISTORY_FILE = "pins_history_v6.json"

BOARDS_CONFIG = {
    "nails": {
        "board_name": "Trending Nails",
        "xml_file": "nails.xml",
        "instruction": "Mention nail shape (Almond/Coffin), colors, and salon request tips.",
        "hashtags": "#TrendingNails #NailArtDesigns #AlmondNails #AcrylicNails #ManicureInspo",
        "style": "Close-up beauty salon photograph of a woman's graceful hand resting on a cream sweater, all five manicured fingernails clearly visible, intricate nail art on every single nail, glossy gel topcoat, bright studio lighting, sharp focus, 8k photorealistic, no text",
        "topics": [
            "glossy lavender and blue ombre almond nails with delicate 3D butterfly nail art and silver sparkles",
            "sheer milky pink almond nails with 3D white floral petals and thin gold chrome swirls",
            "deep royal blue and gold marble swirl coffin acrylic nails with mirror gloss finish",
            "soft blush pink French tip almond nails with cute hand-painted red cherry micro art",
            "icy blue glitter ombre almond nails with clean silver chrome French tips",
            "warm tortoise-shell and burgundy red floral swirl almond gel nails with gold foil"
        ]
    },
    "homedecor": {
        "board_name": "Home Decor",
        "xml_file": "homedecor.xml",
        "instruction": "Include 3 interior styling tips to recreate this cozy look in a US home.",
        "hashtags": "#HomeDecor #CozyHome #LivingRoomDecor #InteriorDesignIdeas #ApartmentDecor",
        "style": "Architectural Digest interior design photography, warm golden sunlight streaming through windows, cozy beige and natural oak wood aesthetic, ultra-sharp focus, 8k photorealistic, no text",
        "topics": [
            "cozy neutral living room with plush cream cloud sofa, knit throw pillows, oak wood coffee table, and arched brass mirror",
            "modern farmhouse kitchen with white quartz waterfall island, brass pendant lights, and woven wooden barstools",
            "aesthetic small bedroom makeover with layered beige linen bedding, warm glowing fairy lights, and indoor olive tree",
            "luxury spa bathroom with freestanding soaking tub, warm backlit round mirror, and wooden bath tray with candles",
            "cozy apartment balcony patio at dusk with warm string lights, rattan egg chair, and potted Mediterranean plants"
        ]
    },
    "pets": {
        "board_name": "Must-Have Pet Products & Care",
        "xml_file": "pets.xml",
        "instruction": "Highlight why this pet product is a must-have for US pet owners, plus 2 care tips.",
        "hashtags": "#PetProducts #DogMomMustHaves #CatFurniture #CozyPetHome #PetCareTips",
        "style": "High-end commercial pet product catalog photograph in a bright aesthetic beige American living room, crystal clear sharp focus on the luxury pet product and a cute well-groomed pet using it, natural daylight, 8k photorealistic, no text",
        "topics": [
            "adorable Golden Retriever puppy resting inside a round cream plush boucle orthopedic donut dog bed on oak hardwood floor",
            "fluffy British Shorthair cat lounging on a modern aesthetic natural oak wood cat tree tower with white sherpa cushions",
            "elevated bamboo dog feeding station with two matte white ceramic bowls beside a cute French Bulldog puppy",
            "modern white ceramic pet water fountain and smart automatic feeder in a bright clean kitchen beside a cute tabby cat",
            "cute miniature Dachshund puppy wearing a luxury sage-green corduroy padded dog harness with brass hardware"
        ]
    },
    "beauty": {
        "board_name": "Health and Beauty Routines",
        "xml_file": "beauty.xml",
        "instruction": "Include a step-by-step routine order (Step 1, Step 2, Step 3) for women to save.",
        "hashtags": "#SkincareRoutine #GlowingSkinTips #BeautyRoutine #SelfCareAesthetic #CleanBeauty",
        "style": "Luxury beauty skincare commercial flat-lay photograph on a clean white marble vanity, soft morning sunlight, aesthetic frosted glass dropper bottles and cream jars, ultra-sharp focus, 8k photorealistic, no text",
        "topics": [
            "glowing glass skin morning skincare lineup with frosted glass serum dropper bottles, cream jar, and rose quartz roller on marble tray",
            "nighttime anti-aging skincare arrangement with amber glass retinol bottle, peptide cream jar, and silk sleep mask",
            "natural hair care flat-lay with glass rosemary oil dropper bottle, wooden bamboo paddle brush, and silk scrunchies",
            "everything shower spa routine essentials with whipped pink body scrub jar, body oil bottle, dry brush, and white towels"
        ]
    },
    "diet": {
        "board_name": "Healthy Diet & Weight Loss Meals",
        "xml_file": "diet.xml",
        "instruction": "Include estimated Calories & Protein macros, plus ingredients and quick prep steps.",
        "hashtags": "#HighProteinMeals #HealthyMealPrep #WeightLossRecipes #LowCalorieMeals #CleanEating",
        "style": "Professional food magazine overhead photograph on a bright white marble kitchen counter, vibrant fresh ingredients, natural morning daylight, ultra-sharp focus, 8k photorealistic, no text",
        "topics": [
            "high-protein meal prep glass containers filled with grilled herb chicken breast, sliced avocado, roasted sweet potato, and broccoli",
            "thick creamy green smoothie in a clear glass jar topped with fresh raspberries, chia seeds, and sliced almonds",
            "pan-seared honey garlic salmon fillet with roasted asparagus spears and lemon wedges on a white ceramic plate",
            "three glass mason jars layered with high-protein vanilla overnight oats, chia pudding, and fresh blueberries and strawberries"
        ]
    }
}

def load_history():
    if not os.path.exists(HISTORY_FILE):
        for old_f in glob.glob("pins_history*.json"):
            try: os.remove(old_f)
            except Exception: pass
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
        "title": f"{topic[:65].title()} | Inspiration",
        "description": f"Discover {topic}. {cfg['instruction']} {cfg['hashtags']}",
        "image_prompt": full_img_prompt
    }

def save_pil_image(img, filepath, crop_bottom=0):
    img = img.convert("RGB")
    if crop_bottom > 0 and img.height > 600:
        img = img.crop((0, 0, img.width, img.height - crop_bottom))
    img = ImageOps.fit(img, (1000, 1500), Image.Resampling.LANCZOS)
    img.save(filepath, format="JPEG", quality=95, optimize=True)
    return os.path.getsize(filepath)

def generate_official_ai_image(image_prompt, filepath):
    os.makedirs("images", exist_ok=True)

    # ১ম ইঞ্জিন: অফিশিয়াল FLUX.1 Gradio Spaces (hf_token আর্গুমেন্ট ছাড়া, যাতে কোনো Error না আসে)
    flux_spaces = [
        "black-forest-labs/FLUX.1-schnell",
        "multimodalart/FLUX.1-merged",
        "black-forest-labs/FLUX.1-dev"
    ]
    for space_name in flux_spaces:
        try:
            print(f"🎨 Trying Official Space: {space_name}...", flush=True)
            g_client = Client(space_name)
            result = g_client.predict(
                image_prompt,
                0,
                True,
                1024,
                1536,
                4,
                api_name="/infer"
            )
            img_out = result[0] if isinstance(result, (list, tuple)) else result
            img_path = img_out.get("path") if isinstance(img_out, dict) else img_out
            if img_path and os.path.exists(img_path):
                with Image.open(img_path) as im:
                    sz = save_pil_image(im, filepath)
                print(f"🚀 Ultra-Crisp AI Image generated via {space_name}!", flush=True)
                return sz
        except Exception as e:
            print(f"Space {space_name} note: {e}", flush=True)

    # ২য় ইঞ্জিন: Hugging Face Free Router (SDXL Base 1.0 - যা hf-inference এ এখনো ১০০% ফ্রি)
    if HF_TOKEN:
        try:
            print("🎨 Trying HF Free SDXL 1.0 Router...", flush=True)
            r = requests.post(
                "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0",
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                json={"inputs": image_prompt},
                timeout=60
            )
            if r.status_code == 200 and len(r.content) > 15000:
                im = Image.open(io.BytesIO(r.content))
                sz = save_pil_image(im, filepath)
                print("🚀 Ultra-Crisp AI Image generated via HF SDXL 1.0!", flush=True)
                return sz
        except Exception as e:
            print(f"HF SDXL note: {e}", flush=True)

    # ৩য় ইঞ্জিন: Pollinations FLUX Model (enhance=false সহ শার্প ছবি)
    clean_p = re.sub(r"[^a-zA-Z0-9, ]", "", image_prompt)[:220]
    enc = urllib.parse.quote(clean_p)
    seed = random.randint(10000, 999999)
    r = requests.get(
        f"https://image.pollinations.ai/prompt/{enc}?width=1024&height=1536&seed={seed}&model=flux&enhance=false",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=60
    )
    if r.status_code == 200 and len(r.content) > 20000:
        im = Image.open(io.BytesIO(r.content))
        sz = save_pil_image(im, filepath, crop_bottom=65)
        print("✨ AI Image generated via Flux Fallback!", flush=True)
        return sz

    raise Exception("All AI image engines were temporarily busy.")

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
        topic = random.choice(cfg["topics"])
        print(f"\n📌 Board: {cfg['board_name']} | Topic: {topic}", flush=True)
        content = generate_pin_content(cfg, topic)
        pin_id = str(uuid.uuid4())[:8]
        filename = f"{key}_{pin_id}.jpg"
        filepath = os.path.join("images", filename)

        img_sz = generate_official_ai_image(content["image_prompt"], filepath)
        img_url = f"{SITE_URL}/images/{filename}"

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
        time.sleep(8)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print("\n🎉 All 5 boards updated with Official FLUX.1 HD images!", flush=True)
