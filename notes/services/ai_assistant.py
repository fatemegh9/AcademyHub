import pypdf
import requests
import io
from openai import OpenAI
from django.conf import settings

client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

GROQ_MODEL = "llama-3.3-70b-versatile"


def extract_text_from_pdf(file_url, max_chars=15000):
    """متن رو از فایل PDF (که رو Cloudinary یا هر جای دیگه‌ای هست) استخراج می‌کند"""
    text = ""
    try:
        response = requests.get(file_url, timeout=15)
        response.raise_for_status()
        pdf_bytes = io.BytesIO(response.content)

        reader = pypdf.PdfReader(pdf_bytes)
        for page in reader.pages:
            text += page.extract_text() or ""
            if len(text) > max_chars:
                break
    except Exception:
        return ""
    return text[:max_chars]


def summarize_note(note_text):
    """خلاصه‌سازی متن جزوه"""
    prompt = f"""متن زیر یک جزوه درسی است. لطفاً خلاصه‌ای کوتاه و مفید از مهم‌ترین نکات آن به زبان فارسی بنویس:

{note_text}
"""
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def ask_question_about_note(note_text, question):
    """پاسخ به سوال کاربر بر اساس محتوای جزوه"""
    prompt = f"""با توجه به متن جزوه زیر، به سوال کاربر پاسخ بده. اگر جواب توی متن نبود، بگو که اطلاعات کافی در جزوه موجود نیست.

متن جزوه:
{note_text}

سوال کاربر:
{question}
"""
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def generate_quiz_from_note(note_text, num_questions=5):
    """تولید سوال تستی از روی جزوه"""
    prompt = f"""با توجه به متن جزوه زیر، {num_questions} سوال چندگزینه‌ای (هر کدام ۴ گزینه) طراحی کن. خروجی را دقیقا به فرمت JSON زیر بده و هیچ متن اضافه‌ای ننویس:

[
  {{
    "question": "متن سوال",
    "options": ["گزینه ۱", "گزینه ۲", "گزینه ۳", "گزینه ۴"],
    "correct_index": 0
  }}
]

متن جزوه:
{note_text}
"""
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content