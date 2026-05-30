import os

def main():
    filepath = "scripts/publish_article.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Locate generated_products loop and insert a time.sleep(10) before generate_content call
    # Find the loop: for idx, p in enumerate(stockpile_data.get("products", [])[:6], 1):
    # And inside: product_res = model.generate_content
    # Let's search and replace with import time inside function or top-level

    old_header_call = """    header_res = model.generate_content(
        header_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=HEADER_SCHEMA
        )
    )"""

    new_header_call = """    import time
    header_res = model.generate_content(
        header_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=HEADER_SCHEMA
        )
    )"""

    old_product_call = """        product_res = model.generate_content(
            product_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json",
                response_schema=PRODUCT_SCHEMA
            )
        )"""

    new_product_call = """        time.sleep(10)
        product_res = model.generate_content(
            product_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json",
                response_schema=PRODUCT_SCHEMA
            )
        )"""

    old_summary_call = """    summary_res = model.generate_content(
        summary_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=SUMMARY_SCHEMA
        )
    )"""

    new_summary_call = """    time.sleep(10)
    summary_res = model.generate_content(
        summary_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=SUMMARY_SCHEMA
        )
    )"""

    if old_header_call in content:
        content = content.replace(old_header_call, new_header_call)
        print("✅ Added import time to header call")
    else:
        print("❌ Could not find old_header_call")

    if old_product_call in content:
        content = content.replace(old_product_call, new_product_call)
        print("✅ Added sleep to product calls")
    else:
        print("❌ Could not find old_product_call")

    if old_summary_call in content:
        content = content.replace(old_summary_call, new_summary_call)
        print("✅ Added sleep to summary call")
    else:
        print("❌ Could not find old_summary_call")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("🎉 Rate limit protection successfully added!")

if __name__ == "__main__":
    main()
