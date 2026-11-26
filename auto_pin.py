import os, re, io, time, json, uuid, random, datetime, urllib.parse
from email.utils import formatdate, parsedate_to_datetime
from xml.sax.saxutils import escape
import requests
from PIL import Image, ImageOps
from gradio_client import Client

GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
HF_TOKEN = (os.environ.get("HF_TOKEN") or "").strip()
SITE_URL = "https://catherinewilliamshub.github.io"
HISTORY_FILE = "pins_history_v6.json"

BOARDS_CONFIG = {
    "jewelry": {
        "board_name": "Luxury Jewelry & Engagement Rings",
        "xml_file": "jewelry.xml",
        "instruction": "Include details about the metal (14k/18k Gold, Platinum), gemstone cut (Oval, Emerald, Pear), and why it makes a stunning holiday engagement ring or Christmas jewelry gift.",
        "hashtags": "#EngagementRings #ChristmasEngagement #HolidayJewelryGifts #LuxuryJewelry #GoldJewelry #DiamondRing #JewelryGiftIdeas",
        "style": "High-end close-up commercial luxury jewelry photography on aesthetic cream velvet and white marble with subtle warm golden bokeh lights, sunlit diamond sparkles, crystal-clear facets and polished 18k gold texture, 8k photorealistic, sharp focus, no text",
        "topics": [
            "brilliant oval cut solitaire diamond engagement ring with hidden halo on thin 18k yellow gold band in a cream velvet ring box with warm holiday glow",
            "aesthetic layered dainty 14k gold necklaces with herringbone chain, diamond pendant, and gold hoop earrings styled as a luxury Christmas gift on white silk",
            "emerald cut diamond engagement ring stacked with a diamond eternity wedding band on a woman's graceful hand",
            "luxury marble jewelry tray displaying a sparkling diamond tennis bracelet, gold chunky rings, and pearl drop earrings",
            "pear-shaped diamond engagement ring with pave gold band sparkling in warm golden sunlight on beige linen",
            "minimalist 18k gold cuff bracelets, vintage gold watch, and stackable diamond rings styled on a woman's wrist"
        ],
        "backup": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=1080&h=1620&fit=crop&q=95"
    },
    "nails": {
        "board_name": "Trending Nails",
        "xml_file": "nails.xml",
        "instruction": "Mention nail shape (Almond/Coffin), festive winter/holiday colors, and salon request tips.",
        "hashtags": "#ChristmasNails #HolidayNailDesigns #WinterNails #TrendingNails #AlmondNails #FestiveManicure #NailArtIdeas",
        "style": "Close-up beauty salon photograph of a woman's graceful hand resting on a cozy cream knit sweater, all five manicured fingernails clearly visible, intricate festive nail art on every single nail, glossy gel topcoat, bright studio lighting, sharp focus, 8k photorealistic, no text",
        "topics": [
            "glossy deep cranberry red and gold chrome swirl almond Christmas nails with mirror gloss finish",
            "sheer milky white almond winter nails with delicate silver snowflake art and subtle glitter sparkles",
            "emerald green velvet cat-eye almond holiday nails with dainty gold star accents",
            "soft blush pink French tip almond nails with cute minimalist red candy cane and bow micro art",
            "icy silver glitter ombre almond nails with clean white chrome French tips for winter",
            "burgundy red and gold foil tortoise-shell almond gel nails with glossy topcoat"
        ],
        "backup": "https://images.unsplash.com/photo-1604654894610-df63bc536371?w=1080&h=1620&fit=crop&q=95"
    },
    "hairstyles": {
        "board_name": "Trending Hairstyles & Hair Color",
        "xml_file": "hairstyles.xml",
        "instruction": "Mention the haircut/layering style, hair color technique (Balayage, Gloss, Highlights), and holiday party styling tips.",
        "hashtags": "#HolidayHairstyles #ChristmasPartyHair #TrendingHairstyles #WinterHairColor #BalayageHair #HairInspo #UpdoHairstyles",
        "style": "Back-angle luxury hair salon photography showing a woman's voluminous healthy hair clearly, silky glossy hair strands, natural studio lighting, ultra-sharp focus on hair texture and color blend, 8k photorealistic, no text",
        "topics": [
            "romantic holiday party half-up wavy hairstyle secured with a luxury velvet ribbon bow on caramel blonde balayage hair",
            "glossy espresso brunette butterfly haircut with bouncy blowout curls and curtain bangs",
            "elegant braided crown updo with pearl hair pins on honey blonde wavy hair for winter events",
            "rich dimensional copper auburn long wavy hair with warm golden shine in natural light",
            "effortless chic French twist claw clip updo on dimensional bronde hair with loose face-framing tendrils",
            "silky vanilla cream blonde lob haircut with soft Hollywood waves and shadow root"
        ],
        "backup": "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1080&h=1620&fit=crop&q=95"
    },
    "homedecor": {
        "board_name": "Home Decor",
        "xml_file": "homedecor.xml",
        "instruction": "Include 3 interior styling tips to recreate this cozy look in a US home, weaving in natural keywords like vintage christmas decor, christmas living room, or apartment christmas decor.",
        "hashtags": "#VintageChristmasDecorIdeas #ChristmasHomeDecor #ChristmasLivingRoom #ApartmentChristmasDecor #ClassicChristmasDecor #SimpleChristmasDecor #ChristmasRoomDecorIdeas #WhimsicalChristmasDecor #VintageChristmasDecor #LivingRoomChristmasDecor #CozyChristmasDecor #ChristmasHouseDecor",
        "style": "Architectural Digest interior design photography, warm golden sunlight and festive christmas glow streaming through windows, cozy beige and natural oak wood aesthetic with subtle tasteful holiday accents, ultra-sharp focus, 8k photorealistic, no text",
        "topics": [
            "vintage christmas decor ideas in a cozy neutral living room with plush cream cloud sofa, knit throw pillows, oak wood coffee table, and arched brass mirror",
            "christmas home decor and living room styling with warm glowing tree lights, garlands, neutral stockings, and natural wood accents",
            "apartment christmas decor in a chic small living space with a slim flocked tree, warm fairy lights, and cozy textured throws",
            "classic christmas decor and cozy christmas decor in a sunlit living room with brass candleholders, pine greenery, and neutral tones",
            "simple christmas decor and whimsical christmas decor in a stylish home interior with subtle festive touches and warm lighting"
        ],
        "backup": "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=1080&h=1620&fit=crop&q=95"
    },
    "patio": {
        "board_name": "Cozy Patio, Garden & Backyard Ideas",
        "xml_file": "patio.xml",
        "instruction": "Include 3 outdoor styling tips (lighting, greenery, seating) to create this cozy American winter porch or backyard.",
        "hashtags": "#ChristmasPorchDecor #OutdoorChristmasDecor #WinterPatio #PatioDecor #BackyardIdeas #OutdoorLights #CozyPorch",
        "style": "Architectural Digest outdoor living and American front porch/backyard photography at golden hour dusk, warm glowing string lights, cozy natural wood and evergreen winter accents, 8k photorealistic, sharp focus, no text",
        "topics": [
            "welcoming American Christmas front porch decor with wooden rocking chairs, evergreen pine garland, warm fairy lights, and lantern planters",
            "cozy winter backyard stone fire pit seating area with cushioned wooden chairs, plaid throw blankets, and warm Edison string lights",
            "covered wooden pergola patio styled for the holidays with evergreen wreaths, woven pendant lamps, and glowing candles",
            "aesthetic small apartment balcony patio at dusk with rattan egg chair, cream throw pillows, mini lit pine tree, and lanterns",
            "modern backyard oasis with wooden deck, outdoor sectional sofa, fire bowl, and warm winter landscape lighting"
        ],
        "backup": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1080&h=1620&fit=crop&q=95"
    },
    "pets": {
        "board_name": "Must-Have Pet Products & Care",
        "xml_file": "pets.xml",
        "instruction": "Highlight why this pet product is a must-have holiday gift or cozy winter essential for US pet owners, plus 2 care tips.",
        "hashtags": "#ChristmasGiftsForDogs #PetProducts #DogMomMustHaves #CatFurniture #CozyPetHome #PetHolidayGifts #PetCareTips",
        "style": "High-end commercial pet product catalog photograph in a bright aesthetic beige American living room with subtle warm holiday lights in the background, crystal clear sharp focus on the luxury pet product and a cute well-groomed pet using it, 8k photorealistic, no text",
        "topics": [
            "adorable Golden Retriever puppy resting inside a round cream plush boucle orthopedic donut dog bed near a softly lit Christmas tree",
            "fluffy British Shorthair cat lounging on a modern aesthetic natural oak wood cat tree tower with white sherpa cushions",
            "elevated bamboo dog feeding station with two matte white ceramic bowls beside a cute French Bulldog puppy",
            "modern white ceramic pet water fountain and smart automatic feeder in a bright clean kitchen beside a cute tabby cat",
            "cute miniature Dachshund puppy wearing a luxury sage-green corduroy padded dog harness with brass hardware"
        ],
        "backup": "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=1080&h=1620&fit=crop&q=95"
    },
    "beauty": {
        "board_name": "Health and Beauty Routines",
        "xml_file": "beauty.xml",
        "instruction": "Include a step-by-step winter skincare or holiday self-care routine order (Step 1, Step 2, Step 3) for women to save.",
        "hashtags": "#WinterSkincareRoutine #HolidayBeautyGifts #SkincareRoutine #GlowingSkinTips #SelfCareAesthetic #CleanBeauty #BeautyGiftSet",
        "style": "Luxury beauty skincare commercial flat-lay photograph on a clean white marble vanity, soft morning sunlight, aesthetic frosted glass dropper bottles and cream jars, ultra-sharp focus, 8k photorealistic, no text",
        "topics": [
            "hydrating winter glass skin morning skincare lineup with frosted glass hyaluronic serum dropper bottles, rich cream jar, and rose quartz roller on marble tray",
            "nighttime anti-aging skincare arrangement with amber glass retinol bottle, peptide cream jar, and silk sleep mask",
            "luxury holiday self-care spa flat-lay with whipped body scrub jar, nourishing body oil bottle, dry brush, and white towels",
            "natural hair repair flat-lay with glass rosemary oil dropper bottle, wooden bamboo paddle brush, and silk scrunchies"
        ],
        "backup": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=1080&h=1620&fit=crop&q=95"
    },
    "diet": {
        "board_name": "Healthy Diet & Weight Loss Meals",
        "xml_file": "diet.xml",
        "instruction": "Include estimated Calories & Protein macros, plus ingredients and quick prep steps for healthy holiday eating.",
        "hashtags": "#HealthyHolidayRecipes #HighProteinMeals #HealthyMealPrep #WeightLossRecipes #LowCalorieMeals #CleanEating #GuiltFreeTreats",
        "style": "Professional food magazine overhead photograph on a bright white marble kitchen counter, vibrant fresh ingredients, natural morning daylight, ultra-sharp focus, 8k photorealistic, no text",
        "topics": [
            "high-protein meal prep glass containers filled with grilled herb chicken breast, sliced avocado, roasted sweet potato, and broccoli",
            "festive cranberry pomegranate high-protein smoothie bowl in a clear glass bowl topped with chia seeds and sliced almonds",
            "pan-seared honey garlic salmon fillet with roasted asparagus spears and lemon wedges on a white ceramic plate",
            "three glass mason jars layered with high-protein cinnamon apple overnight oats, chia pudding, and fresh berries"
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

def generate_pin_content(cfg, topic):
    full_img_prompt = f"{topic}. {cfg['style']}"
    prompt = f"""Create a viral US Pinterest Pin for board "{cfg['board_name']}" on topic "{topic}".
    {cfg['instruction']}
    Respond ONLY with valid JSON: {{"title": "Catchy SEO title under 85 chars", "description": "SEO description (250-380 chars) ending with {cfg['hashtags']}"}}"""

    if not GEMINI_API_KEY:
        print("⚠️ GEMINI_API_KEY is missing in GitHub Secrets!", flush=True)
    else:
        models = [
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash"
        ]
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        for model in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                r = requests.post(url, json=payload, timeout=25)
                if r.status_code == 200:
                    txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    m = re.search(r"\{.*\}", txt, re.DOTALL)
                    if m:
                        data = json.loads(m.group(0))
                        if data.get("title") and data.get("description"):
                            data["image_prompt"] = full_img_prompt
                            print(f"✍️ Gemini text generated using {model}", flush=True)
                            return data
                    print(f"⚠️ Gemini {model} returned unexpected format: {txt[:150]}", flush=True)
                else:
                    print(f"⚠️ Gemini {model} failed ({r.status_code}): {r.text[:180]}", flush=True)
            except Exception as e:
                print(f"⚠️ Gemini {model} error: {e}", flush=True)

    print("ℹ️ Using fallback title/description template.", flush=True)
    clean_title = topic.strip().title()
    if len(clean_title) > 68:
        clean_title = clean_title[:68].rsplit(" ", 1)[0]
    return {
        "title": f"{clean_title} | Ideas",
        "description": f"Save this {cfg['board_name'].lower()} inspiration featuring {topic}. Tap the link for full styling details and more holiday ideas! {cfg['hashtags']}",
        "image_prompt": full_img_prompt
    }

def save_pil_image(img, filepath):
    img = img.convert("RGB")
    img = ImageOps.fit(img, (1000, 1500), Image.Resampling.LANCZOS)
    img.save(filepath, format="JPEG", quality=95, optimize=True)
    return os.path.getsize(filepath)

def create_gradio_client(space_name):
    if HF_TOKEN:
        try:
            return Client(space_name, token=HF_TOKEN)
        except TypeError:
            return Client(space_name, hf_token=HF_TOKEN)
    return Client(space_name)

def generate_official_ai_image(image_prompt, cfg, filepath):
    os.makedirs("images", exist_ok=True)

    # 1) Direct Hugging Face Inference Router API (most reliable with HF_TOKEN)
    if HF_TOKEN:
        hf_models = [
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/stable-diffusion-xl-base-1.0"
        ]
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        for model_id in hf_models:
            try:
                api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
                r = requests.post(
                    api_url,
                    headers=headers,
                    json={
                        "inputs": image_prompt,
                        "parameters": {"width": 768, "height": 1152}
                    },
                    timeout=90
                )
                if r.status_code == 200 and len(r.content) > 20000:
                    im = Image.open(io.BytesIO(r.content))
                    sz = save_pil_image(im, filepath)
                    print(f"🎨 AI Image generated via HF Router ({model_id}) | {sz} bytes", flush=True)
                    return sz
                else:
                    print(f"⚠️ HF Router {model_id} failed ({r.status_code}): {r.text[:180]}", flush=True)
            except Exception as e:
                print(f"⚠️ HF Router {model_id} error: {e}", flush=True)
    else:
        print("⚠️ HF_TOKEN is missing in GitHub Secrets!", flush=True)

    #
