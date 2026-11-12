import os
import time
import json
import uuid
import random
import urllib.parse
from email.utils import formatdate
from xml.sax.saxutils import escape
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SITE_URL = "https://catherinewilliamshub.github.io"

BOARDS_CONFIG = {
    "nails": {
        "board_name": "Trending Nails & Aesthetic Manicure",
        "xml_file": "nails.xml",
        "instruction": "Include the nail shape (Almond, Coffin, Short Square), color palette, and salon request tips.",
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
        "instruction": "Include 3 practical pet care tips or reasons why US dog and cat owners love this setup.",
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
        "instruction": "Include a clear step-by-step routine order (Step 1, Step 2, Step 3) or practical self-care tips.",
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
        "instruction": "Include estimated Calories & Protein macros, plus ingredients and quick prep steps.",
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

def generate_pin_content(board_name, topic, extra_instruction):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
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
      "image_prompt": "Ultra-realistic professional vertical lifestyle photography of {topic}, bright natural lighting, Pinterest aesthetic, magazine quality, 8k, no text on image"
    }}
    """
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    text_data = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text_data)

def download_image(image_prompt, filename):
    os.makedirs("images", exist_ok=True)
    filepath = os.path.join("images", filename)
    encoded_prompt = urllib.parse.quote(image_prompt)
    headers = {"User-Agent": "Mozilla/5.0"}

    for attempt in range(3):
        try:
            seed = random.randint(1000, 999999)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1000&height=1500&seed={seed}&nologo=true"
            response = requests.get(image_url, headers=headers, timeout=90)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(response.content)
            return f"{SITE_URL}/images/{filename}", len(response.content)
        except Exception as e:
            print(f"Retry {attempt + 1} for image download: {e}")
            time.sleep(5)
    raise Exception("Failed to generate image.")

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

        content = generate_pin_content(cfg["board_name"], topic, cfg["instruction"])
        pin_id = str(uuid.uuid4())[:8]
        img_filename = f"{key}_{pin_id}.jpg"

        img_url, img_size = download_image(content["image_prompt"], img_filename)

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
        time.sleep(8)

    save_history(history)
