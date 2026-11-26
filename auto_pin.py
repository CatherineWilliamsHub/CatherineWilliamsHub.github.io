import os, re, io, json, uuid, base64, random, datetime
from email.utils import formatdate, parsedate_to_datetime
from xml.sax.saxutils import escape
import requests
from PIL import Image, ImageOps

GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
CF_ACCOUNT_ID = (os.environ.get("CF_ACCOUNT_ID") or "").strip()
CF_API_TOKEN = (os.environ.get("CF_API_TOKEN") or "").strip()
SITE_URL = "https://catherinewilliamshub.github.io"
HISTORY_FILE = "pins_history_v6.json"
_GEMINI_TEXT_MODELS = None

BOARDS_CONFIG = {
    "jewelry": {
        "board_name": "Luxury Jewelry & Engagement Rings",
        "xml_file": "jewelry.xml",
        "niche_focus": "fine jewelry, engagement rings, layered gold necklaces, tennis bracelets, pearl earrings, birthstone rings, luxury watch stacks, minimalist gold jewelry gifts",
        "instruction": "Mention specific metal (14k/18k Gold, Platinum, Rose Gold), gemstone cut (Oval, Emerald, Marquise, Radiant, Pear), and styling or gifting tips.",
        "hashtags": "#LuxuryJewelry #EngagementRings #GoldJewelry #DiamondRing #JewelryGiftIdeas",
        "style": "High-end close-up commercial luxury jewelry photography on aesthetic cream velvet, silk, or white marble, soft sunlit diamond sparkles, crystal-clear facets and polished gold texture, 8k photorealistic, sharp focus, no text, no watermarks",
        "topics": [
            "brilliant oval cut solitaire diamond engagement ring with hidden halo on thin 18k yellow gold band in a cream velvet box",
            "layered dainty 14k gold herringbone necklace with solitaire diamond pendant and small gold hoop earrings on white silk",
            "emerald cut diamond engagement ring stacked with a dainty diamond eternity band on a graceful hand"
        ],
        "backup": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=1080&h=1620&fit=crop&q=95"
    },
    "nails": {
        "board_name": "Trending Nails",
        "xml_file": "nails.xml",
        "niche_focus": "almond nails, short squoval gel nails, French tip variations, chrome glazed nails, cat-eye velvet manicure, minimalist micro nail art, aura nails, seasonal nail colors",
        "instruction": "Mention nail shape (Almond/Short Square/Coffin), exact polish finish (chrome, velvet cat-eye, sheer milky, glossy gel), and salon request tips.",
        "hashtags": "#TrendingNails #AlmondNails #NailArtIdeas #GelManicure #NailInspo",
        "style": "Close-up luxury nail salon photograph of a woman's graceful hand resting on a soft aesthetic fabric or cozy knit, all five manicured fingernails clearly visible, neat cuticles, glossy gel topcoat, bright studio lighting, sharp focus, 8k photorealistic, no text",
        "topics": [
            "glossy deep cranberry red and gold chrome swirl almond nails with mirror gloss finish",
            "sheer milky white almond nails with delicate pearl chrome glaze and subtle micro sparkles",
            "emerald green velvet cat-eye almond manicure with dainty gold star accents"
        ],
        "backup": "https://images.unsplash.com/photo-1604654894610-df63bc536371?w=1080&h=1620&fit=crop&q=95"
    },
    "hairstyles": {
        "board_name": "Trending Hairstyles & Hair Color",
        "xml_file": "hairstyles.xml",
        "niche_focus": "layered haircuts, butterfly cut, Italian bob, balayage shades, glossy espresso brunette, copper auburn, honey blonde, half-up ribbon styles, sleek buns, effortless braids, blowout waves",
        "instruction": "Mention the exact haircut or updo style, hair color/gloss technique, and a quick styling tip to recreate it at home or request it at the salon.",
        "hashtags": "#TrendingHairstyles #HairColorIdeas #BalayageHair #HairInspo #SalonHair",
        "style": "Back or three-quarter angle luxury hair salon photography showing a woman's voluminous healthy hair clearly, silky glossy strands, soft natural studio lighting, ultra-sharp focus on hair texture and color dimension, 8k photorealistic, no text",
        "topics": [
            "romantic half-up wavy hairstyle secured with a velvet ribbon bow on dimensional caramel balayage hair",
            "glossy espresso brunette butterfly haircut with bouncy blowout layers and curtain bangs",
            "elegant braided low chignon updo with pearl hair pins on honey blonde wavy hair"
        ],
        "backup": "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1080&h=1620&fit=crop&q=95"
    },
    "homedecor": {
        "board_name": "Home Decor",
        "xml_file": "homedecor.xml",
        "niche_focus": "cozy neutral living rooms, small apartment decor, kitchen counter styling, bedroom bedding layers, entryway console tables, warm lighting, organic modern interiors, seasonal home styling",
        "instruction": "Include 3 practical interior styling tips to recreate this cozy aesthetic in a US home or apartment.",
        "hashtags": "#HomeDecorIdeas #CozyHomeDecor #LivingRoomDecor #ApartmentDecor #InteriorInspo",
        "style": "Architectural Digest interior design photography, warm natural sunlight and inviting ambient glow, cozy neutral textures and natural oak wood aesthetic, ultra-sharp focus, 8k photorealistic, no text",
        "topics": [
            "cozy neutral living room with plush cream bouclé sofa, textured throw pillows, oak coffee table, and arched brass mirror",
            "chic small apartment entryway console styled with ceramic vases, warm table lamp, framed art, and woven baskets",
            "warm organic modern bedroom with layered linen bedding, soft ambient bedside lamps, and natural wood accents"
        ],
        "backup": "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=1080&h=1620&fit=crop&q=95"
    },
    "patio": {
        "board_name": "Cozy Patio, Garden & Backyard Ideas",
        "xml_file": "patio.xml",
        "niche_focus": "American front porch decor, backyard fire pit seating, wooden pergola patios, small apartment balcony makeovers, garden pathways, outdoor string light setups, planter styling",
        "instruction": "Include 3 outdoor styling tips covering lighting, greenery/planters, and comfortable seating for a US porch, patio, or backyard.",
        "hashtags": "#PatioDecor #BackyardIdeas #PorchDecor #OutdoorLiving #CozyPatio",
        "style": "Architectural Digest outdoor living and American porch/backyard photography at golden hour dusk, warm glowing string lights, cozy natural wood, stone, and lush greenery, 8k photorealistic, sharp focus, no text",
        "topics": [
            "welcoming American front porch with wooden rocking chairs, glowing lanterns, layered doormat, and lush potted evergreens",
            "cozy backyard stone fire pit seating circle with cushioned wood chairs, woven throw blankets, and Edison string lights",
            "small apartment balcony makeover at dusk with rattan chair, outdoor rug, warm fairy lights, and potted plants"
        ],
        "backup": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1080&h=1620&fit=crop&q=95"
    },
    "pets": {
        "board_name": "Must-Have Pet Products & Care",
        "xml_file": "pets.xml",
        "niche_focus": "orthopedic dog beds, modern wooden cat trees, elevated ceramic pet bowls, smart water fountains, stylish dog harnesses, pet grooming essentials, cozy pet corners, interactive enrichment toys",
        "instruction": "Highlight why this pet product is a practical upgrade for US dog or cat owners, plus 2 quick pet care or styling tips.",
        "hashtags": "#PetProducts #DogMomMustHaves #CatFurniture #CozyPetHome #PetCareTips",
        "style": "High-end commercial pet product catalog photograph in a bright aesthetic American home, crystal clear sharp focus on the stylish pet product and a cute well-groomed dog or cat using it, warm natural lighting, 8k photorealistic, no text",
        "topics": [
            "Golden Retriever puppy resting inside a round cream plush bouclé orthopedic donut dog bed in a cozy living room",
            "British Shorthair cat lounging on a modern natural oak wood cat tree tower with white sherpa cushions",
            "elevated bamboo dog feeding station with two matte white ceramic bowls beside a cute French Bulldog"
        ],
        "backup": "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=1080&h=1620&fit=crop&q=95"
    },
    "beauty": {
        "board_name": "Health and Beauty Routines",
        "xml_file": "beauty.xml",
        "niche_focus": "glass skin morning routines, anti-aging night skincare, body care everything-shower setups, scalp and hair oiling rituals, clean makeup vanities, gua sha & barrier repair skincare",
        "instruction": "Include a clear step-by-step routine order (Step 1, Step 2, Step 3) that women will want to save and follow.",
        "hashtags": "#SkincareRoutine #GlowingSkinTips #SelfCareAesthetic #CleanBeauty #BeautyRoutine",
        "style": "Luxury beauty skincare commercial flat-lay photograph on a clean white marble vanity, soft morning sunlight, aesthetic frosted glass dropper bottles, ceramic cream jars, and clean textures, ultra-sharp focus, 8k photorealistic, no text",
        "topics": [
            "hydrating glass skin morning skincare lineup with frosted hyaluronic serum bottles, barrier cream jar, and rose quartz roller on marble tray",
            "calming nighttime retinol and peptide skincare flat-lay with amber dropper bottle, whipped moisturizer, and silk sleep mask",
            "spa-inspired everything-shower body care tray with sugar scrub jar, botanical body oil, dry brush, and folded white towels"
        ],
        "backup": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=1080&h=1620&fit=crop&q=95"
    },
    "diet": {
        "board_name": "Healthy Diet & Weight Loss Meals",
        "xml_file": "diet.xml",
        "niche_focus": "high-protein meal prep bowls, low-calorie weight loss dinners, overnight oats & chia jars, macro-friendly salads, air fryer healthy meals, protein smoothie bowls, Mediterranean bowls, guilt-free snacks",
        "instruction": "Include estimated Calories & Protein macros, key fresh ingredients, and quick prep steps for busy healthy eating.",
        "hashtags": "#HighProteinMeals #HealthyMealPrep #WeightLossRecipes #LowCalorieMeals #CleanEating",
        "style": "Professional food magazine overhead photograph on a bright white marble kitchen counter, vibrant fresh colorful ingredients, appetizing plating, natural morning daylight, ultra-sharp focus, 8k photorealistic, no text",
        "topics": [
            "high-protein meal prep glass containers filled with grilled herb chicken, sliced avocado, roasted sweet potato, and steamed broccoli",
            "Mediterranean quinoa and grilled shrimp power bowl with cucumber, cherry tomatoes, feta, and lemon herb dressing",
            "three glass mason jars layered with high-protein berry vanilla overnight oats, chia pudding, and sliced almonds"
        ],
        "backup": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=1620&fit=crop&q=95"
    }
}

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for k in BOARDS_CONFIG:
                data.setdefault(k, [])
            return data
    return {k: [] for k in BOARDS_CONFIG}

def parse_pub_date(item):
    try:
        dt = parsedate_to_datetime(item.get("pub_date", ""))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

def get_oldest_board(history, board_keys):
    oldest_key = board_keys[0]
    oldest_dt = datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)
    for k in board_keys:
        items = history.get(k, [])
        if not items:
            return k
        dt = parse_pub_date(items[0])
        if dt < oldest_dt:
            oldest_dt = dt
            oldest_key = k
    return oldest_key

def get_season_context():
    now = datetime.datetime.now(datetime.timezone.utc)
    month_name = now.strftime("%B")
    m = now.month
    if m in (11, 12):
        vibe = "cozy late fall, Christmas & festive holiday season"
    elif m in (1, 2):
        vibe = "cozy winter, fresh New Year & chic Valentine's season"
    elif m in (3, 4, 5):
        vibe = "fresh spring & bright seasonal refresh"
    elif m in (6, 7, 8):
        vibe = "bright summer & effortless warm-weather aesthetic"
    else:
        vibe = "cozy autumn & warm fall aesthetic"
    return f"{month_name} ({vibe})"

def get_gemini_text_models():
    global _GEMINI_TEXT_MODELS
    if _GEMINI_TEXT_MODELS is not None:
        return _GEMINI_TEXT_MODELS
    models = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
    if GEMINI_API_KEY:
        try:
            r = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}",
                timeout=20
            )
            if r.status_code == 200:
                for m in r.json().get("models", []):
                    name = m.get("name", "").replace("models/", "")
                    low = name.lower()
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        if "flash" in low and not any(x in low for x in ["image", "audio", "tts", "live", "embedding"]):
                            if name not in models:
                                models.append(name)
        except Exception:
            pass
    _GEMINI_TEXT_MODELS = models
    return models

def pick_least_used_fallback_topic(cfg, recent_titles):
    joined = " ".join(recent_titles[:15]).lower()
    scored = []
    for t in cfg["topics"]:
        words = [w for w in re.findall(r"[a-z]{4,}", t.lower())]
        overlap = sum(1 for w in words if w in joined)
        scored.append((overlap, random.random(), t))
    scored.sort()
    return scored[0][2]

def generate_pin_content(cfg, recent_titles):
    season_ctx = get_season_context()
    recent_block = "\n".join(f"- {t}" for t in recent_titles[:25]) if recent_titles else "- None yet"

    prompt = f"""You are a viral US Pinterest content strategist for the board "{cfg['board_name']}".
Current month/season: {season_ctx}
Niche variety ideas: {cfg['niche_focus']}

RECENTLY PUBLISHED TITLES ON THIS BOARD (DO NOT repeat these exact ideas, dishes, nail colors, hairstyles, rooms, or products):
{recent_block}

Task:
1. Invent ONE brand-new, fresh, highly saveable US Pinterest Pin concept that fits "{cfg['board_name']}" and the current season, and is clearly different from all recent titles above.
2. Write a catchy SEO title (under 85 characters).
3. Write an engaging SEO description (250-380 characters). {cfg['instruction']} End the description with 6-8 relevant hashtags (mixing {cfg['hashtags']} with 2-3 specific seasonal/topic hashtags).
4. Write a vivid "visual_subject" (1-2 sentences) describing the exact main object/scene, colors, textures, and composition for an AI photorealistic image generator (do NOT mention text, logos, or words).

Respond ONLY with valid JSON:
{{"title": "...", "description": "...", "visual_subject": "..."}}"""

    if GEMINI_API_KEY:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.95
            }
        }
        for model in get_gemini_text_models()[:5]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                r = requests.post(url, json=payload, timeout=25)
                if r.status_code == 200:
                    txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    try:
                        data = json.loads(txt)
                    except Exception:
                        m = re.search(r"\{.*\}", txt, re.DOTALL)
                        data = json.loads(m.group(0)) if m else {}

                    title = (data.get("title") or "").strip()
                    desc = (data.get("description") or "").strip()
                    visual = (data.get("visual_subject") or "").strip()
                    if title and desc and visual:
                        print(f"✍️ Gemini unique pin ({model}): {title}", flush=True)
                        return {
                            "title": title[:95],
                            "description": desc,
                            "image_prompt": f"{visual}. {cfg['style']}"
                        }
                else:
                    print(f"⚠️ Gemini {model} failed ({r.status_code}): {r.text[:140]}", flush=True)
            except Exception as e:
                print(f"⚠️ Gemini {model} error: {e}", flush=True)

    print("ℹ️ Using fallback topic/template.", flush=True)
    topic = pick_least_used_fallback_topic(cfg, recent_titles)
    clean_title = topic.strip().title()
    if len(clean_title) > 68:
        clean_title = clean_title[:68].rsplit(" ", 1)[0]
    return {
        "title": f"{clean_title} | Ideas",
        "description": f"Save this {cfg['board_name'].lower()} inspiration featuring {topic}. Tap the link for full styling details and more ideas! {cfg['hashtags']}",
        "image_prompt": f"{topic}. {cfg['style']}"
    }

def save_pil_image(img, filepath):
    img = img.convert("RGB")
    img = ImageOps.fit(img, (1000, 1500), Image.Resampling.LANCZOS)
    img.save(filepath, format="JPEG", quality=95, optimize=True)
    return os.path.getsize(filepath)

def generate_official_ai_image(image_prompt, cfg, filepath):
    os.makedirs("images", exist_ok=True)

    if CF_ACCOUNT_ID and CF_API_TOKEN:
        headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
        cf_models = [
            ("@cf/black-forest-labs/flux-1-schnell", {"prompt": f"{image_prompt}, centered subject, vertical portrait framing", "steps": 6}),
            ("@cf/bytedance/stable-diffusion-xl-lightning", {"prompt": image_prompt, "width": 768, "height": 1152}),
            ("@cf/stabilityai/stable-diffusion-xl-base-1.0", {"prompt": image_prompt, "width": 768, "height": 1152}),
        ]
        for model_id, payload in cf_models:
            try:
                api_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{model_id}"
                r = requests.post(api_url, headers=headers, json=payload, timeout=90)
                if r.status_code == 200:
                    img_bytes = None
                    ctype = r.headers.get("Content-Type", "").lower()
                    if "application/json" in ctype:
                        b64_img = r.json().get("result", {}).get("image")
                        if b64_img:
                            img_bytes = base64.b64decode(b64_img)
                    elif len(r.content) > 15000:
                        img_bytes = r.content

                    if img_bytes:
                        im = Image.open(io.BytesIO(img_bytes))
                        sz = save_pil_image(im, filepath)
                        print(f"🎨 AI Image generated via Cloudflare ({model_id}) | {sz} bytes", flush=True)
                        return sz
                    print(f"⚠️ Cloudflare {model_id} returned empty image payload.", flush=True)
                else:
                    print(f"⚠️ Cloudflare {model_id} failed ({r.status_code}): {r.text[:180]}", flush=True)
            except Exception as e:
                print(f"⚠️ Cloudflare {model_id} error: {e}", flush=True)
    else:
        print("⚠️ CF_ACCOUNT_ID or CF_API_TOKEN is missing in GitHub Secrets!", flush=True)

    print("⚠️ All AI image sources failed — using Unsplash backup image.", flush=True)
    r = requests.get(cfg["backup"], timeout=30)
    im = Image.open(io.BytesIO(r.content))
    return save_pil_image(im, filepath)

def is_valid_local_image(image_url):
    prefix = f"{SITE_URL}/images/"
    if image_url.startswith(prefix):
        fname = image_url[len(prefix):]
        fpath = os.path.join("images", fname)
        return os.path.exists(fpath) and os.path.getsize(fpath) > 5000
    return True

def build_rss(board_title, xml_file, items):
    rss_items = ""
    valid_items = [it for it in items if is_valid_local_image(it.get("image_url", ""))]
    for it in valid_items[:20]:
        rss_items += f"""
    <item>
      <title>{escape(it['title'])}</title>
      <link>{escape(it['link'])}</link>
      <description>{escape(it['description'])}</description>
      <pubDate>{it['pub_date']}</pubDate>
      <guid isPermaLink="false">{escape(it['guid'])}</guid>
      <enclosure url="{escape(it['image_url'])}" length="{it['length']}" type="image/jpeg"/>
      <media:content url="{escape(it['image_url'])}" type="image/jpeg" medium="image" width="1000" height="1500"/>
      <media:thumbnail url="{escape(it['image_url'])}" width="1000" height="1500"/>
    </item>"""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Catherine Williams Hub - {escape(board_title)}</title>
    <link>{SITE_URL}</link>
    <atom:link href="{SITE_URL}/{escape(xml_file)}" rel="self" type="application/rss+xml"/>
    <description>Daily US inspiration for {escape(board_title)}</description>{rss_items}
  </channel>
</rss>"""
    with open(xml_file, "w", encoding="utf-8") as f:
        f.write(xml.strip())

if __name__ == "__main__":
    history = load_history()
    board_keys = list(BOARDS_CONFIG.keys())

    target_board = get_oldest_board(history, board_keys)
    boards_to_run = [target_board]
    print(f"🚀 Processing oldest board -> {target_board}", flush=True)

    for key in boards_to_run:
        cfg = BOARDS_CONFIG[key]
        try:
            recent_titles = [it.get("title", "") for it in history.get(key, [])[:25]]
            print(f"\n📌 Board: {cfg['board_name']} | Avoiding {len(recent_titles)} recent titles", flush=True)
            content = generate_pin_content(cfg, recent_titles)
            pin_id = str(uuid.uuid4())[:8]
            filename = f"{key}_{pin_id}.jpg"
            filepath = os.path.join("images", filename)

            img_sz = generate_official_ai_image(content["image_prompt"], cfg, filepath)
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
            print(f"✅ Created new pin for {key}!", flush=True)
        except Exception as e:
            print(f"⚠️ Skipped {key}: {e}", flush=True)

    for k in board_keys:
        build_rss(BOARDS_CONFIG[k]["board_name"], BOARDS_CONFIG[k]["xml_file"], history.get(k, []))

    all_items = []
    for k in board_keys:
        all_items.extend(history.get(k, []))
    all_items.sort(key=parse_pub_date, reverse=True)
    build_rss("All Latest Inspiration", "facebook.xml", all_items)
    print("✅ Updated all 8 board feeds and master facebook.xml successfully!", flush=True)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print("\n🎉 Done!", flush=True)
