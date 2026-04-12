from flask import url_for


def resolve_image_path(image_value):
    image_value = (image_value or "").strip()

    if not image_value:
        return url_for("static", filename="images/product-item1.jpg")

    lowered = image_value.lower()

    if lowered.startswith(("http://", "https://", "//", "data:")):
        return image_value

    normalized = image_value.replace("\\", "/").lstrip("/")

    if normalized.startswith("static/"):
        normalized = normalized[len("static/"):]

    if normalized.startswith("images/"):
        return url_for("static", filename=normalized)

    return url_for("static", filename=f"images/{normalized}")


def split_products_for_sections(products):
    women_labels = {"women", "woman", "female", "ladies", "lady", "girls", "girl"}
    men_labels = {"men", "man", "male", "gents", "gent", "boys", "boy"}
    men_keywords = (
        "men", "man", "male", "gents", "gent", "boy",
        "cufflink", "chain", "band", "watch", "brooch"
    )

    women_products = []
    men_products = []

    for product in products:
        category_name = str(product.get("CATEGORY_NAME", "")).strip().lower()
        searchable_text = " ".join(
            str(product.get(key, "")).lower()
            for key in ("PRODUCT_NAME", "CATEGORY_NAME", "DESCRIPTION", "MATERIAL_NAME")
        )

        if category_name in women_labels:
            women_products.append(product)
        elif category_name in men_labels or any(keyword in searchable_text for keyword in men_keywords):
            men_products.append(product)

    return women_products, men_products
