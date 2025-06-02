from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.menu_item import MenuItem
from app.models.ingredient import Ingredient
from app.models.menu_item_ingredient import MenuItemIngredient


async def check_and_update_menu_item_availability(db: AsyncSession, menu_item_id: int) -> bool:
    """
    Belirtilen menü öğesinin tüm malzemelerinin stok durumunu kontrol eder
    ve MenuItem.is_available flag'ini günceller.
    """
    menu_item_result = await db.execute(select(MenuItem).where(MenuItem.id == menu_item_id))
    menu_item = menu_item_result.scalar_one_or_none()

    if not menu_item:
        print(f"WARNING: MenuItem with ID {menu_item_id} not found.")
        return False

    # Bu menü öğesinin tüm malzemelerini ve gereken miktarlarını al
    # Gerekli malzeme miktarını ve mevcut stok miktarını karşılaştıracağız.
    required_ingredients_query = await db.execute(
        select(MenuItemIngredient, Ingredient.stock_quantity, Ingredient.low_stock_threshold)
        .join(Ingredient, MenuItemIngredient.ingredient_id == Ingredient.id)
        .where(MenuItemIngredient.menu_item_id == menu_item_id)
    )
    required_ingredients_data = required_ingredients_query.all()

    # Eğer menü öğesi için hiç malzeme tanımlanmamışsa, varsayılan olarak mevcut kabul et (veya değil, iş modelinize göre)
    if not required_ingredients_data:
        # Menü öğesi malzemesizse ve is_available true ise devam et
        if not menu_item.is_available:
            menu_item.is_available = True
            db.add(menu_item)
            await db.commit()
            await db.refresh(menu_item)
            print(f"DEBUG: MenuItem '{menu_item.name}' has no ingredients, set to available.")
        return True

    is_currently_available = True
    for menu_item_ingredient_rel, current_stock, low_stock_threshold in required_ingredients_data:
        required_amount_per_item = menu_item_ingredient_rel.amount_used

        # Eğer mevcut stok, menü öğesi için gereken miktardan az ise, ürün mevcut değildir.
        # İsterseniz burada low_stock_threshold'u da kullanabilirsiniz.
        # Örneğin: if current_stock < required_amount_per_item * SOME_BUFFER:
        if current_stock < required_amount_per_item:
            is_currently_available = False
            break  # Bir malzeme bile eksikse, ürün mevcut değildir

    # MenuItem'ın is_available durumunu güncelle
    if menu_item.is_available != is_currently_available:
        menu_item.is_available = is_currently_available
        db.add(menu_item)  # SQLAlchemy'nin değişikliği izlemesi için ekle
        await db.commit()  # Değişikliği veritabanına kaydet
        await db.refresh(menu_item)  # En son haliyle objeyi yenile
        print(f"DEBUG: MenuItem '{menu_item.name}' availability changed to {menu_item.is_available}")

    return is_currently_available