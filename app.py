import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import cv2
import pytesseract
import re

# Вредни Е-номера
harmful_e_numbers = {
    "E407": "Карагенан (възпаления, храносмилателни проблеми)",
    "E621": "Натриев глутамат (главоболие, алергии)",
    "E262": "Натриев ацетат (дразни стомаха)",
    "E300": "Аскорбинова киселина (в големи дози дразни стомаха)",
    "E330": "Лимонена киселина (уврежда зъбния емайл)",
    "E250": "Натриев нитрит (риск от рак, в месо)",
}

harmful_keywords = {
    "нитрит": "Натриев нитрит – използва се в меса, свързан е с рак",
    "глутамат": "Натриев глутамат – може да предизвика главоболие и алергии",
    "карагинан": "Карагенан – свързан с възпаления в червата",
    "фосфат": "Фосфати – могат да влияят негативно на бъбреците",
    "консерван": "Консерванти – често съдържат нитрати или сулфити",
    "лактоза": "Лактоза – може да причини стомашен дискомфорт при непоносимост",
}

food_categories = {
    "луканка": "преработено месо",
    "салам": "преработено месо",
    "наденица": "преработено месо",
    "суджук": "преработено месо",
    "пастет": "преработено месо",
    "сирене": "млечен продукт",
    "кашкавал": "млечен продукт",
}

category_alternatives = {
    "преработено месо": [
        "🥗 Вместо колбас – печено пилешко филе с подправки.",
        "🍛 Леща яхния с моркови и подправки.",
        "🥚 Яйца с авокадо и свежи зеленчуци.",
    ],
    "млечен продукт": [
        "🥥 Веган сирене от кашу.",
        "🧄 Тофу с билки – идеално за салата.",
    ]
}

st.title("📸 Завъртане + OCR на етикет + съставки и алтернативи")

uploaded_file = st.file_uploader("Качи изображение на етикет:", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    image_np = np.array(image)
    image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    # Завъртане с pytesseract
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    osd = pytesseract.image_to_osd(gray)
    rotation = int(re.search(r'(?<=Rotate: )\d+', osd).group(0))

    if rotation != 0:
        # Завъртаме изображението
        if rotation == 90:
            rotated = cv2.rotate(image_cv, cv2.ROTATE_90_CLOCKWISE)
        elif rotation == 180:
            rotated = cv2.rotate(image_cv, cv2.ROTATE_180)
        elif rotation == 270:
            rotated = cv2.rotate(image_cv, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            rotated = image_cv
    else:
        rotated = image_cv

    # Покажи завъртяното изображение
    st.image(rotated, caption="🔄 Завъртяно изображение", channels="BGR", use_column_width=True)

    # OCR с EasyOCR
    reader = easyocr.Reader(['bg', 'en'])
    results = reader.readtext(rotated)

    st.subheader("📄 Разпознат текст:")
    full_text = ""
    for _, text, conf in results:
        st.write(f"- {text} (точност: {conf:.2f})")
        full_text += text + " "

    full_text_lower = full_text.lower()
    report_lines = []

    # Вредни E-кодове
    st.subheader("🧪 Вредни съставки (E-номера):")
    found = []
    for e, desc in harmful_e_numbers.items():
        if e.lower() in full_text_lower:
            st.error(f"{e} - {desc}")
            found.append(f"{e} - {desc}")

    if not found:
        st.success("✅ Няма открити вредни E-номера.")
        report_lines.append("Няма открити вредни E-номера.")
    else:
        report_lines.append("Открити вредни E-номера:")
        report_lines.extend(found)

    # Вредни думи
    st.subheader("🧬 Засечени съставки (по дума):")
    keyword_found = []
    for word, desc in harmful_keywords.items():
        if word in full_text_lower:
            st.warning(f"⚠️ {word} – {desc}")
            keyword_found.append(f"{word} – {desc}")

    if not keyword_found:
        st.success("✅ Няма засечени вредни думи.")
        report_lines.append("Няма засечени съставки по ключови думи.")
    else:
        report_lines.append("Засечени съставки по дума:")
        report_lines.extend(keyword_found)

    # Категория храна
    product_category = None
    for k, v in food_categories.items():
        if k in full_text_lower:
            product_category = v
            break

    if (found or keyword_found) and product_category:
        st.subheader(f"🍽 Алтернативи на {product_category.capitalize()}:")
        for alt in category_alternatives.get(product_category, []):
            st.info(alt)

    # Генериране на отчет
    st.subheader("📥 Генериран отчет:")
    report_text = "📄 OCR отчет за етикета:\n\n"
    report_text += "РАЗПОЗНАТ ТЕКСТ:\n" + full_text + "\n\n"
    report_text += "\n".join(report_lines)
    st.download_button("⬇️ Изтегли отчет", data=report_text.encode("utf-8"), file_name="ocr_otchet.txt", mime="text/plain")
