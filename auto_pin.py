import os
import re
import io
import glob
import time
import json
import uuid
import base64
import random
import urllib.parse
from email.utils import formatdate
from xml.sax.saxutils import escape
import requests
from PIL import Image, ImageOps

GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
SITE_URL = "https://catherinewilliamshub.github.io"

# ==========================================
# ৫টি বোর্ডের নাম, ম্যাক্রো/প্রিমিয়াম প্রম্পট গাইড এবং ভাইরাল টপিক
# ==========================================
BOARDS_CONFIG = {
    "nails": {
        "board_name": "Trending Nails",
        "xml_file": "nails.xml",
        "instruction": "Include the exact nail shape (Almond, Coffin, or Stiletto), color details, and what to ask the nail tech at the salon.",
        "hashtags": "#TrendingNails #NailArtDesigns #AlmondNails #AcrylicNails #ManicureInspo",
        "visual_style": (
            "Extreme macro close-up nail salon photography of a woman's graceful hand, "
            "all five fingernails clearly visible filling 80% of the frame, showing intricate nail art on every single nail, "
            "ultra-glossy gel topcoat finish, dainty gold ring on finger, soft warm blurred bokeh background, "
            "sharp macro focus on the nail details, 8k resolution, no text"
        ),
        "topics": [
            "iridescent 3D purple butterfly wing nail art with glossy lavender chrome ombre almond nails",
            "sheer milky pink almond nails with delicate 3D white floral petals and gold leaf swirls",
            "deep royal blue and gold foil marble swirl coffin acrylic nails with mirror gloss finish",
            "blush pink French tip almond nails with cute hand-painted red cherry micro nail art",
            "shimmering icy blue ombre almond nails with silver glitter flakes and 3D crystal accents",
            "warm autumn amber tortoise-shell and burgundy red floral swirl almond gel nails",
            "turquoise and white ocean wave marble swirl almond nails with gold chrome outline",
            "classy matte and glossy white quilted pattern almond nails with tiny gold pearl studs"
        ],
        "backup_hd": [
            "https://images.unsplash.com/photo-1604654894610-df63bc536371?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1632345031435-8727f6897d53?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1519014816548-bf5fe059798b?w=1080&h=1620&fit=crop&q=95"
        ]
    },
    "homedecor": {
        "board_name": "Home Decor",
        "xml_file": "homedecor.xml",
        "instruction": "Include 3 interior styling tips (colors, lighting, textures) to recreate this cozy look in an American home or apartment.",
        "hashtags": "#HomeDecor #CozyHome #LivingRoomDecor #InteriorDesignIdeas #ApartmentTherapy",
        "visual_style": (
            "Architectural Digest and viral US Pinterest interior design photography, "
            "warm golden hour natural sunlight streaming through large windows, cozy neutral palette with cream, beige, "
            "warm oak wood, and brushed brass accents, magazine editorial quality, 8k sharp focus, no text"
        ),
        "topics": [
            "cozy neutral living room with a plush cream cloud sofa, knit throw pillows, wooden coffee table, and arched mirror",
            "modern farmhouse kitchen with white quartz waterfall island, brass pendant lights, and woven wooden barstools",
            "aesthetic small bedroom makeover with layered beige linen bedding, warm glowing fairy lights, and trailing plants",
            "luxury spa-inspired bathroom with freestanding soaking tub, warm LED backlit round mirror, and wooden bath tray",
            "cozy apartment balcony patio at dusk with warm Edison string lights, rattan egg chair, and potted olive trees",
            "chic entryway console table styling with oversized brass round mirror, woven storage baskets, and pampas grass vase"
        ],
        "backup_hd": [
            "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=1080&h=1620&fit=crop&q=95"
        ]
    },
    "pets": {
        "board_name": "Must-Have Pet Products & Care",
        "xml_file": "pets.xml",
        "instruction": "Highlight why this specific pet product is a must-have for US dog and cat owners, plus 2 practical pet care tips.",
        "hashtags": "#PetProducts #DogMomMustHaves #CatFurniture #CozyPetHome #PetCareTips",
        "visual_style": (
            "High-end commercial pet product lifestyle photography in a bright, clean, aesthetic beige American living room, "
            "crystal-clear focus on the modern luxury pet product and a well-groomed adorable pet using it, "
            "soft natural daylight, warm cozy magazine aesthetic, 8k Sony A7R V photography, no text"
        ),
        "topics": [
            "adorable Golden Retriever puppy curled up inside a thick plush cream bouclé orthopedic donut dog bed on a wooden floor",
            "fluffy British Shorthair cat lounging on a modern aesthetic natural oak wood cat tree tower with white sherpa cushions",
            "elevated bamboo dog feeding station with two matte white ceramic bowls and glass treat jars beside a cute French Bulldog",
            "sleek modern wireless stainless-steel pet water fountain and smart automatic feeder in a bright minimalist kitchen with a cute tabby cat",
            "aesthetic woven pet grooming basket filled with natural dog shampoo bottles, soft waffle towel, and wooden brush next to a cute Maltipoo puppy",
            "cute miniature Dachshund puppy wearing a luxury sage-green corduroy padded dog harness with brass hardware and matching leash"
        ],
        "backup_hd": [
            "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=1080&h=1620&fit=crop&q=95"
        ]
    },
    "beauty": {
        "board_name": "Health and Beauty Routines",
        "xml_file": "beauty.xml",
        "instruction": "Include a clear step-by-step routine order (Step 1, Step 2, Step 3) so women save this pin for their daily routine.",
        "hashtags": "#SkincareRoutine #GlowingSkinTips #BeautyRoutine #SelfCareAesthetic #CleanBeauty",
        "visual_style": (
            "Luxury commercial beauty and skincare editorial photography on a clean white marble vanity, "
            "soft morning sunlight, dewy water droplets, fresh botanical accents, aesthetic glass dropper bottles and jars, "
            "clean girl Pinterest aesthetic, 8k macro product shot, no text"
        ),
        "topics": [
            "glowing glass skin morning skincare lineup with frosted glass serum dropper bottles, moisturizer jar, and rose quartz roller on marble tray",
            "nighttime anti-aging skincare routine arrangement with amber glass retinol bottle, peptide cream jar, silk eye mask, and lit candle",
            "natural hair care flat-lay with glass rosemary oil dropper bottle, wooden bamboo paddle brush, scalp massager, and silk scrunchies",
            "everything shower spa routine essentials with whipped pink body scrub jar, body oil bottle, dry brush, and rolled fluffy white towels",
            "organized minimalist bathroom vanity tray with pastel hydrating serums, glossy lip oil tubes, and plush makeup brushes",
            "winter skin barrier repair routine with rich ceramide cream jar, hyaluronic acid mist spray, and hydrating lip mask on white stone"
        ],
        "backup_hd": [
            "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1608248597359-0e6d526a6828?w=1080&h=1620&fit=crop&q=95"
        ]
    },
    "diet": {
        "board_name": "Healthy Diet & Weight Loss Meals",
        "xml_file": "diet.xml",
        "instruction": "Include estimated Calories & Protein macros, plus a short list of ingredients and quick prep steps.",
        "hashtags": "#HighProteinMeals #HealthyMealPrep #WeightLossRecipes #LowCalorieMeals #CleanEating",
        "visual_style": (
            "Professional 45-degree angle food magazine photography on a bright white marble kitchen counter, "
            "vibrant fresh ingredients, appetizing glossy textures, natural morning daylight, clean eating Pinterest aesthetic, "
            "8k sharp focus on the food, no text"
        ),
        "topics": [
            "high-protein meal prep glass containers filled with grilled herb chicken breast, sliced avocado, roasted sweet potato cubes, and broccoli",
            "thick creamy green smoothie in a clear glass jar topped with fresh raspberries, chia seeds, sliced almonds, and mint leaves",
            "pan-seared honey garlic salmon fillet with roasted asparagus spears and lemon wedges in a matte white ceramic bowl",
            "three aesthetic glass mason jars layered with high-protein vanilla overnight oats, chia pudding, and fresh blueberries and strawberries",
            "refreshing glass pitcher and tumbler of detox water infused with thinly sliced cucumber, fresh lemon wheels, and mint leaves with ice",
            "crisp green butter lettuce wraps filled with savory seasoned lean ground turkey, diced red bell peppers, avocado slices, and cilantro"
        ],
        "backup_hd": [
            "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=1080&h=1620&fit=crop&q=95",
            "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=1080&h=1620&fit=crop&q=95"
        ]
    }
}

HISTORY_FILE = "pins_history_v2.json"

def clean_old_bad_files():
    """প্রথমবার নতুন কোড চলার সময় আগের সব খারাপ ছবি ও পুরনো হিস্ট্রি ডিলিট করে ফ্রেশ স্টার্ট করা"""
    if not os.path.exists(HISTORY_FILE):
        print("🧹 Cleaning old low-quality images from previous runs...")
        if os.path.exists("pins_history.json"):
            os.remove("pins_history.json")
        for old_img in glob.glob("images/*.jpg"):
            try:
                os.remove(old_img)
            except Exception:
                pass

def load_history():
    clean_old_bad_files()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {k: [] for k in BOARDS_CONFIG}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def generate_pin_content(board_name, topic, visual_style, extra_instruction, hashtags):
    full_image_prompt = f"{visual_style}. Subject: {topic}."
    prompt = f"""
    You are a US Pinterest SEO expert creating a viral Pin for the board "{board_name}".
    Topic: "{topic}"
    Rules:
    1. Use natural American English.
    2. {extra_instruction}
    3. Respond ONLY in valid JSON format with these exact 2 keys:
    {{
      "title": "Catchy US Pinterest SEO title under 85 characters",
      "description": "Value-packed SEO description (250-400 characters) ending with {hashtags}"
    }}
    """
    models_to_try = [
        "gemini-flash-lite-latest",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]

    for model_name in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(url, json=payload, timeout=25)
            if response.status_code == 200:
                text_data = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                match = re.search(r"\{.*\}", text_data, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    if "title" in data and "description" in data:
                        data["image_prompt"] = full_image_prompt
                        print(f"✅ Text generated via Gemini ({model_name})")
                        return data
        except Exception as e:
            print(f"Skipping text model {model_name}: {e}")

    return {
        "title": f"{topic[:70].title()} | Trending Ideas",
        "description": f"Discover the best {topic}. {extra_instruction} {hashtags}",
        "image_prompt": full_image_prompt
    }

def process_and_save_image(raw_bytes, filepath, crop_bottom=0):
    """ছবিটিকে নিখুঁত 1000x1500 Pinterest Vertical সাইজে রূপান্তর ও Ultra-HD JPEG হিসেবে সেভ করা"""
    img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    if crop_bottom > 0 and img.height > (crop_bottom + 400):
        img = img.crop((0, 0, img.width, img.height - crop_bottom))
    img = ImageOps.fit(img, (1000, 1500), Image.Resampling.LANCZOS)
    img.save(filepath, format="JPEG", quality=95, optimize=True)
    return os.path.getsize(filepath)

def generate_image_with_gemini(image_prompt, filepath):
    """১ম ইঞ্জিন: সরাসরি Google Gemini / Imagen AI দিয়ে ছবি তৈরি"""
    if not GEMINI_API_KEY:
        return False

    gemini_image_models = [
        "gemini-2.0-flash-preview-image-generation",
        "gemini-2.0-flash-exp-image-generation"
    ]
    try:
        r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}", timeout=15)
        if r.status_code == 200:
            for m in r.json().get("models", []):
                name = m.get("name", "").replace("models/", "")
                if ("image" in name or "imagen" in name) and name not in gemini_image_models:
                    gemini_image_models.insert(0, name)
    except Exception:
        pass

    for model_name in gemini_image_models:
        if "imagen" in model_name:
            continue
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": f"Generate a photorealistic vertical Pinterest photo: {image_prompt}"}]}],
                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
            }
            res = requests.post(url, json=payload, timeout=45)
            if res.status_code == 200:
                parts = res.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part and "data" in part["inlineData"]:
                        img_bytes = base64.b64decode(part["inlineData"]["data"])
                        if len(img_bytes) > 10000:
                            process_and_save_image(img_bytes, filepath, crop_bottom=0)
                            print(f"🌟 Ultra-HD Image generated via Google Gemini ({model_name})!")
                            return True
        except Exception as e:
            print(f"Gemini image model {model_name} skipped: {e}")

    for imagen_model in ["imagen-3.0-generate-002", "imagen-3.0-generate-001"]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{imagen_model}:predict?key={GEMINI_API_KEY}"
            payload = {
                "instances": [{"prompt": image_prompt}],
                "parameters": {"sampleCount": 1, "aspectRatio": "3:4"}
            }
            res = requests.post(url, json=payload, timeout=45)
            if res.status_code == 200:
                preds = res.json().get("predictions", [])
                if preds and "bytesBase64Encoded" in preds[0]:
                    img_bytes = base64.b64decode(preds[0]["bytesBase64Encoded"])
                    if len(img_bytes) > 10000:
                        process_and_save_image(img_bytes, filepath, crop_bottom=0)
                        print(f"🌟 Ultra-HD Image generated via Google Imagen ({imagen_model})!")
                        return True
        except Exception as e:
            print(f"Imagen model {imagen_model} skipped: {e}")

    return False

def download_high_quality_image(image_prompt, cfg, filename):
    os.makedirs("images", exist_ok=True)
    filepath = os.path.join("images", filename)

    # ১ম চেষ্টা: সরাসরি Google Gemini Image Generation
    if generate_image_with_gemini(image_prompt, filepath):
        return f"{SITE_URL}/images/{filename}", os.path.getsize(filepath)

    # ২য় চেষ্টা: Flux AI (nologo প্যারামিটার ছাড়া যাতে 402 এরর না আসে + নিচের অংশ অটো-ক্রপ)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    encoded_prompt = urllib.parse.quote(image_prompt[:380])
    for attempt in range(2):
        try:
            seed = random.randint(10000, 999999)
            flux_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1000&height=1580&seed={seed}&model=flux"
            r = requests.get(flux_url, headers=headers, timeout=60)
            if r.status_code == 200 and len(r.content) > 25000:
                size = process_and_save_image(r.content, filepath, crop_bottom=65)
                print("✨ Ultra-HD AI Image generated via Flux Realism Engine!")
                return f"{SITE_URL}/images/{filename}", size
        except Exception as e:
            print(f"Flux attempt {attempt + 1} skipped: {e}")
        time.sleep(10)

    # ৩য় ব্যাকআপ: ভেরিফাইড ম্যাগাজিন গ্রেড HD স্টুডিও ছবি (যাতে কখনোই বাজে ছবি না আসে)
    studio_url = random.choice(cfg["backup_hd"])
    r = requests.get(studio_url, headers=headers, timeout=30)
    r.raise_for_status()
    size = process_and_save_image(r.content, filepath, crop_bottom=0)
    print("📸 Magazine-grade Studio HD photo saved!")
    return f"{SITE_URL}/images/{filename}", size

def build_rss_xml(board_title, xml_filename, items):
    rss_items = ""
    for item in items[:20]:
        title = escape(item["title"])
        desc = escape(item["description"])
        link = escape(item["link"])
        img_url = escape(item["image_url"])
        guid = escape(item["guid"])
        pub_date = item["pub_date"]
        length = item.get("length", 250000)

        rss_items += f"""
    <item>
      <title>{title}</title>
      <link>{link}</link>
      <description>{desc}</description>
      <pubDate>{pub_date}</pubDate>
      <guid isPermaLink="false">{guid}</guid>
      <enclosure url="{img_url}" length="{length}" type="image/jpeg"/>
      <media:content url="{img_url}" type="image/jpeg" medium="image"/>
    </item>"""

    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>Catherine Williams Hub - {escape(board_title)}</title>
    <link>{SITE_URL}</link>
    <description>Daily US inspiration for {escape(board_title)}</description>{rss_items}
  </channel>
</rss>
"""
    with open(xml_filename, "w", encoding="utf-8") as f:
        f.write(rss_content.strip())

if __name__ == "__main__":
    history = load_history()

    for key, cfg in BOARDS_CONFIG.items():
        topic = random.choice(cfg["topics"])
        print(f"📌 Board: {cfg['board_name']} | Topic: {topic}")

        content = generate_pin_content(
            cfg["board_name"],
            topic,
            cfg["visual_style"],
            cfg["instruction"],
            cfg["hashtags"]
        )
        pin_id = str(uuid.uuid4())[:8]
        img_filename = f"{key}_{pin_id}.jpg"

        img_url, img_size = download_high_quality_image(content["image_prompt"], cfg, img_filename)

        new_item = {
            "guid": f"{key}-{pin_id}",
            "title": content["title"],
            "description": content["description"],
            "link": f"{SITE_URL}/?pin={key}-{pin_id}",
            "image_url": img_url,
            "length": img_size,
            "pub_date": formatdate(localtime=False, usegmt=True)
        }

        history.setdefault(key, []).insert(0, new_item)
        history[key] = history[key][:20]
        build_rss_xml(cfg["board_name"], cfg["xml_file"], history[key])
        print(f"✅ Updated {cfg['xml_file']} successfully!\n")
        # সার্ভার রেট-লিমিট এড়াতে প্রতিটি বোর্ডের মাঝে ১৫ সেকেন্ড বিরতি
        time.sleep(15)

    save_history(history)
