from fastapi import APIRouter, HTTPException
from amos import select_elements, sell_elements  # Updated import to use `amos`

element_router = APIRouter()

@element_router.get("/")
def list_elements():
    """
    List all valid elements.
    """
    return {"elements": ["gold", "silver", "platinum", "copper", "palladium"]}

@element_router.post("/select")
def select_elements_endpoint(element_names: list):
    """
    Select elements by name.
    """
    elements = select_elements(element_names)
    if not elements:
        raise HTTPException(status_code=400, detail="Invalid elements")
    return {"selected_elements": elements}

@element_router.post("/sell")
def sell_elements_endpoint(percentage: int, cargo_list: list, commodity_values: dict):
    """
    Sell a percentage of elements in the cargo.
    """
    sold_elements = sell_elements(percentage, cargo_list, commodity_values)
    if not sold_elements:
        raise HTTPException(status_code=400, detail="Failed to sell elements")
    return {"sold_elements": sold_elements}