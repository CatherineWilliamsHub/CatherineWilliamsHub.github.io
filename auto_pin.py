import os
import re
import time
import json
import uuid
import random
import urllib.parse
from email.utils import formatdate
from xml.sax.saxutils import escape
import requests

GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
SITE_URL = "https://catherinewilliamshub.github.io"

BOARDS_CONFIG = {
    "nails": {
        "board_name": "Trending Nails & Aesthetic Manicure",
        "xml_file": "nails.xml",
        "search_query": "manicure nail art aesthetic nails",
        "instruction": "Include the nail shape (Almond, Coffin, Short Square), color palette, and salon request tips.",
        "hashtags": "#TrendingNails #NailArtIdeas #AcrylicNails #ManicureInspo #AestheticNails",
        "fallback_images": [
            "https://images.unsplash.com/photo-1604654894610-df63bc536371?w=1000&h=1500&fit=crop",
            "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1000&h=1500&fit=crop",
            "https://images.unsplash.com/photo-1632345031435-8727f6897d53?w=1000&h=1500&fit=crop"
        ],
        "topics": [
            "Classy French Tip Acrylic Nails with a Modern Twist",
            "Minimalist Neutral Gel Manicure for Short Nails",
            "Glazed Donut Chrome Nails Aesthetic",
            "Cozy Seasonal Fall and Winter Nail Art Ideas",
            "Soft Pink Milky Bath Nails Inspiration",
            "Chic Floral Accent Almond Shaped Nails"
        ]
    },
    "pets": {
        "board_name": "Must-Have Pet Products & Care",
        "xml_file": "pets.xml",
        "search_query": "cute dog puppy cat indoor pet cozy",
        "instruction": "Include 3 practical pet care tips or reasons why US dog and cat owners love this setup.",
        "hashtags": "#PetProducts #DogMomLife #CatLovers #PetCareTips #CozyPetHome",
        "fallback_images": [
            "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=1000&h=1500&fit=crop",
            "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=1000&h=1500&fit=crop",
            "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=1000&h=1500&fit=crop"
        ],
        "topics": [
            "Cozy Orthopedic Dog Bed Setup in Aesthetic Living Room",
            "Modern Wooden Cat Tree Tower for Small Apartments",
            "Smart Automatic Pet Feeder and Water Fountain Station",
            "Dog Grooming at Home Essentials for a Shiny Coat",
            "Interactive Puzzle Toys to Keep Indoor Puppies Busy",
            "Organized Pet Food Storage and Feeding Station Ideas"
        ]
    },
    "beauty": {
        "board_name": "Health and Beauty Routines",
        "xml_file": "beauty.xml",
        "search_query": "skincare serum beauty routine aesthetic spa",
        "instruction": "Include a clear step-by-step routine order (Step 1, Step 2, Step 3) or practical self-care tips.",
        "hashtags": "#SkincareRoutine #GlowingSkin #BeautyTips #SelfCareRoutine #CleanBeauty",
        "fallback_images": [
            "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=1000&h=1500&fit=crop",
            "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=1000&h=1500&fit=crop",
            "https://images.unsplash.com/photo-1612817288484-6f916006741a?w=1000&h=1500&fit=crop"
        ],
        "topics": [
            "Morning Skincare Routine for Glowing Glass Skin",
            "Nighttime Anti-Aging Skincare Layering Order",
            "Natural Hair Oiling and Scalp Care Routine for Thick Hair",
            "Everything Shower Routine for Ultimate Self-Care",
            "Clean Beauty Vanity Organization and Daily Essentials",
            "Hydrating Winter Skincare Routine for Dry Skin"
        ]
    },
    "diet": {
        "board_name": "Healthy Diet & Weight Loss Meals",
        "xml_file": "diet.xml",
        "search_query": "healthy salad bowl smoothie meal prep food",
        "instruction": "Include estimated Calories & Protein macros, plus ingredients and quick prep steps.",
        "hashtags": "#HighProteinMeals #HealthyMealPrep #WeightLossRecipes #LowCalorieMeals #CleanEating",
        "fallback_images": [
            "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1000&h=1500&fit=crop",
            "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=1000&h=1500&fit=crop",
            "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=1000&h=1500&fit=crop"
        ],
        "topics": [
            "High Protein Chicken and Avocado Meal Prep Bowls",
            "Flat Belly Green Smoothie with Spinach Chia and Berries",
            "Low Calorie 20-Minute Salmon and Roasted Veggie Dinner",
            "High Protein Overnight Oats for Weight Loss Breakfast",
            "Refreshing Cucumber Lemon Mint Detox Water Recipe",
            "Keto Friendly Low Carb Turkey Lettuce Wraps"
        ]
    }
}

HISTORY_FILE = "pins_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {k: [] for k in BOARDS_CONFIG}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def generate_pin_content(board_name, topic, extra_instruction, hashtags):
    prompt = f"""
    You are a US Pinterest SEO expert creating a viral Pin for the board "{board_name}".
    Topic: "{topic}"
    Rules:
    1. Use natural American English.
    2. {extra_instruction}
    3. Respond ONLY in valid JSON format with these exact 3 keys:
    {{
      "title": "Catchy US Pinterest SEO title under 90 characters",
      "description": "Value-packed SEO description (250-400 characters) ending with 5 trending hashtags",
      "image_prompt": "Vertical lifestyle photo of {topic}, natural lighting, aesthetic"
    }}
    """
    # আপনার অ্যাকাউন্টে সবচেয়ে দ্রুত কাজ করা মডেলগুলো প্রথমে রাখা হয়েছে
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
            response = requests.post(url, json=payload, timeout=20)
            if response.status_code == 200:
                text_data = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                match = re.search(r"\{.*\}", text_data, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    if "title" in data and "description" in data and "image_prompt" in data:
                        print(f"✅ Generated text using model: {model_name}")
                        return data
        except Exception as e:
            print(f"Skipping {model_name}: {e}")

    print("ℹ️ Using built-in US SEO template fallback.")
    return {
        "title": f"{topic} | Must-Try Inspiration",
        "description": f"Looking for the best {topic.lower()}? Save this pin for your next inspiration! {extra_instruction} {hashtags}",
        "image_prompt": f"Vertical lifestyle photo of {topic}, bright lighting"
    }

def download_image(image_prompt, cfg, filename):
    os.makedirs("images", exist_ok=True)
    filepath = os.path.join("images", filename)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": SITE_URL
    }

    # ১ম চেষ্টা: Pollinations AI (সংক্ষিপ্ত প্রম্পট এবং nologo ছাড়া যাতে 402 না আসে)
    short_prompt = urllib.parse.quote(image_prompt[:90])
    seed = random.randint(1000, 999999)
    pollinations_url = f"https://image.pollinations.ai/prompt/{short_prompt}?width=1000&height=1500&seed={seed}"
    try:
        r = requests.get(pollinations_url, headers=headers, timeout=45)
        if r.status_code == 200 and len(r.content) > 5000:
            with open(filepath, "wb") as f:
                f.write(r.content)
            print("🖼️ Image generated via Pollinations AI!")
            return f"{SITE_URL}/images/{filename}", len(r.content)
    except Exception as e:
        print(f"Pollinations skipped: {e}")

    # ২য় চেষ্টা: Openverse Free Stock Photography API
    try:
        q = urllib.parse.quote(cfg["search_query"])
        ov_url = f"https://api.openverse.org/v1/images/?q={q}&page_size=20"
        ov_res = requests.get(ov_url, headers=headers, timeout=20)
        if ov_res.status_code == 200:
            results = ov_res.json().get("results", [])
            random.shuffle(results)
            for item in results[:5]:
                img_link = item.get("url")
                if img_link:
                    img_r = requests.get(img_link, headers=headers, timeout=25)
                    if img_r.status_code == 200 and len(img_r.content) > 10000:
                        with open(filepath, "wb") as f:
                            f.write(img_r.content)
                        print("🖼️ High-res lifestyle photo downloaded via Openverse!")
                        return f"{SITE_URL}/images/{filename}", len(img_r.content)
    except Exception as e:
        print(f"Openverse skipped: {e}")

    # ৩য় চেষ্টা: নিশ অনুযায়ী ভেরিফাইড Unsplash HD Vertical Photos
    for fb_url in random.sample(cfg["fallback_images"], len(cfg["fallback_images"])):
        try:
            r = requests.get(f"{fb_url}&sig={seed}", headers=headers, timeout=25)
            if r.status_code == 200 and len(r.content) > 5000:
                with open(filepath, "wb") as f:
                    f.write(r.content)
                print("🖼️ High-res lifestyle photo downloaded via Unsplash!")
                return f"{SITE_URL}/images/{filename}", len(r.content)
        except Exception as e:
            print(f"Unsplash fallback skipped: {e}")

    # ৪র্থ গ্যারান্টিড ব্যাকআপ (যাতে কোড কখনোই ক্র্যাশ না করে)
    r = requests.get(f"https://picsum.photos/seed/{seed}/1000/1500", headers=headers, timeout=25)
    r.raise_for_status()
    with open(filepath, "wb") as f:
        f.write(r.content)
    print("🖼️ Fallback vertical photo downloaded!")
    return f"{SITE_URL}/images/{filename}", len(r.content)

def build_rss_xml(board_title, xml_filename, items):
    rss_items = ""
    for item in items[:20]:
        title = escape(item["title"])
        desc = escape(item["description"])
        link = escape(item["link"])
        img_url = escape(item["image_url"])
        guid = escape(item["guid"])
        pub_date = item["pub_date"]
        length = item.get("length", 150000)

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
        print(f"Generating Pin for: {cfg['board_name']} | Topic: {topic}")

        content = generate_pin_content(cfg["board_name"], topic, cfg["instruction"], cfg["hashtags"])
        pin_id = str(uuid.uuid4())[:8]
        img_filename = f"{key}_{pin_id}.jpg"

        img_url, img_size = download_image(content["image_prompt"], cfg, img_filename)

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
        print(f"Updated {cfg['xml_file']} successfully!\n")
        time.sleep(5)

    save_history(history)
