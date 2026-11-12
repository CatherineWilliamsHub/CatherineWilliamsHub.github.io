import os
import time
import json
import base64
import random
import datetime
import urllib.parse
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PINTEREST_TOKEN = os.environ.get("PINTEREST_ACCESS_TOKEN")
EVENT_NAME = os.environ.get("GITHUB_EVENT_NAME", "manual")

# ==========================================
# আপনার ৪টি বোর্ড এবং USA-তে ভাইরাল সাব-টপিক
# ==========================================
BOARDS_CONFIG = {
    "Trending Nails & Aesthetic Manicure": {
        "instruction": "Include the nail shape (e.g., Almond, Coffin, Short Square), exact color palette, and what to ask the nail tech at the salon.",
        "topics": [
            "Classy French Tip Acrylic Nails with a Modern Twist",
            "Minimalist Neutral Gel Manicure for Short Nails",
            "Glazed Donut Chrome Nails Aesthetic",
            "Cozy Seasonal Fall and Winter Nail Art Ideas",
            "Soft Pink Milky Bath Nails Inspiration",
            "Chic Floral Accent Almond Shaped Nails"
        ]
    },
    "Must-Have Pet Products & Care": {
        "instruction": "Include 3 practical pet care tips or reasons why US dog and cat owners love this setup for a clean, happy home.",
        "topics": [
            "Cozy Orthopedic Dog Bed Setup in Aesthetic Living Room",
            "Modern Wooden Cat Tree Tower for Small Apartments",
            "Smart Automatic Pet Feeder and Water Fountain Station",
            "Dog Grooming at Home Essentials for a Shiny Coat",
            "Interactive Puzzle Toys to Keep Indoor Puppies Busy",
            "Organized Pet Food Storage and Feeding Station Ideas"
        ]
    },
    "Health and Beauty Routines": {
        "instruction": "Include a clear step-by-step order of application (Step 1, Step 2, Step 3) or practical self-care tips so women save this pin.",
        "topics": [
            "Morning Skincare Routine for Glowing Glass Skin",
            "Nighttime Anti-Aging Skincare Layering Order",
            "Natural Hair Oiling and Scalp Care Routine for Thick Hair",
            "Everything Shower Routine for Ultimate Self-Care",
            "Clean Beauty Vanity Organization and Daily Essentials",
            "Hydrating Winter Skincare Routine for Dry Skin"
        ]
    },
    "Healthy Diet & Weight Loss Meals": {
        "instruction": "Include estimated Calories & Protein macros, plus a short list of ingredients and quick prep steps inside the description.",
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

def get_user_boards():
    """পিন্টারেস্ট অ্যাকাউন্ট থেকে বোর্ডগুলোর আইডি খুঁজে বের করা"""
    url = "https://api.pinterest.com/v5/boards"
    headers = {"Authorization": f"Bearer {PINTEREST_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    boards = {}
    for item in response.json().get("items", []):
        boards[item["name"].strip().lower()] = item["id"]
    return boards

def generate_pin_content(board_name, topic, extra_instruction):
    """Gemini AI দিয়ে আমেরিকান ইংলিশে ভাইরাল টাইটেল, ডেসক্রিপশন এবং ছবির প্রম্পট তৈরি"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""
    You are a top US Pinterest SEO expert creating a high-saving viral Pin for the board "{board_name}".
    Topic: "{topic}"
    
    Rules:
    1. Use natural American English.
    2. {extra_instruction}
    3. Respond ONLY in valid JSON format with these exact 3 keys:
    {{
      "title": "Catchy US Pinterest SEO title under 90 characters",
      "description": "Value-packed SEO description (300-450 characters) following the rules above, ending with 5 trending hashtags",
      "image_prompt": "Ultra-realistic professional vertical lifestyle photography of {topic}, bright natural lighting, Pinterest aesthetic, magazine quality, 8k resolution, strictly no text or letters on the image"
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

def generate_image_base64(image_prompt):
    """Pollinations AI দিয়ে পিন্টারেস্টের সাইজে (1000x1500) ছবি তৈরি"""
    encoded_prompt = urllib.parse.quote(image_prompt)
    for attempt in range(3):
        try:
            seed = random.randint(1000, 999999)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1000&height=1500&seed={seed}&nologo=true"
            response = requests.get(image_url, timeout=90)
            response.raise_for_status()
            return base64.b64encode(response.content).decode("utf-8")
        except Exception as e:
            print(f"ছবি তৈরির চেষ্টা {attempt + 1} ব্যর্থ হয়েছে, আবার চেষ্টা করা হচ্ছে...")
            time.sleep(5)
    raise Exception("ছবি তৈরি করা যায়নি।")

def post_to_pinterest(board_id, title, description, image_b64):
    """পিন্টারেস্টের নির্দিষ্ট বোর্ডে পিন পাবলিশ করা"""
    url = "https://api.pinterest.com/v5/pins"
    headers = {
        "Authorization": f"Bearer {PINTEREST_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "board_id": board_id,
        "title": title[:100],
        "description": description[:500],
        "media_source": {
            "source_type": "image_base64",
            "content_type": "image/jpeg",
            "data": image_b64
        }
    }
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

if __name__ == "__main__":
    all_board_names = list(BOARDS_CONFIG.keys())
    current_utc_hour = datetime.datetime.now(datetime.timezone.utc).hour

    # ম্যানুয়ালি টেস্ট করলে ৪টি বোর্ডেই পোস্ট হবে, আর টাইমারে চললে ২টা করে বোর্ডে পোস্ট হবে
    if EVENT_NAME == "workflow_dispatch":
        target_boards = all_board_names
    elif current_utc_hour < 2:
        target_boards = all_board_names[:2] # সকাল ৬টায় ১ম ২টি বোর্ড
    else:
        target_boards = all_board_names[2:] # সকাল ৯টায় পরের ২টি বোর্ড

    existing_boards = get_user_boards()

    for board_name in target_boards:
        board_id = existing_boards.get(board_name.strip().lower())
        if not board_id:
            print(f"⚠️ '{board_name}' নামের বোর্ডটি পিন্টারেস্টে খুঁজে পাওয়া যায়নি! বানান চেক করুন।")
            continue

        config = BOARDS_CONFIG[board_name]
        chosen_topic = random.choice(config["topics"])
        print(f"📌 বোর্ড: {board_name} | আজকের টপিক: {chosen_topic}")

        content = generate_pin_content(board_name, chosen_topic, config["instruction"])
        print(f"✍️ তৈরি হওয়া টাইটেল: {content['title']}")

        img_b64 = generate_image_base64(content["image_prompt"])
        post_to_pinterest(board_id, content["title"], content["description"], img_b64)
        print(f"✅ '{board_name}' বোর্ডে সফলভাবে পোস্ট হয়েছে!\n")
        time.sleep(12)
