from dataclasses import dataclass
import secrets
from typing import Literal

from app.schemas.eco_sort import EcoSortWasteItem


WasteCategory = Literal["wet", "dry", "recyclable"]


@dataclass(frozen=True)
class WasteItem:
    id: int
    name: str
    description: str
    category: WasteCategory
    explanation: str


WASTE_ITEMS = (
    WasteItem(
        id=1,
        name="Vegetable peels",
        description="Organic scraps left after preparing vegetables.",
        category="wet",
        explanation=(
            "Vegetable peels are organic waste. Compost them where possible "
            "or follow local wet-waste collection rules."
        ),
    ),
    WasteItem(
        id=2,
        name="Leftover food",
        description="Uneaten cooked food remaining after a meal.",
        category="wet",
        explanation=(
            "Food scraps belong with wet waste or compost only where accepted; "
            "follow local collection guidance."
        ),
    ),
    WasteItem(
        id=3,
        name="Used tissue",
        description="A used paper tissue that may be soiled.",
        category="wet",
        explanation=(
            "Used tissues are generally treated as wet or soiled waste where "
            "local collection accepts them; they are not recyclable paper."
        ),
    ),
    WasteItem(
        id=4,
        name="Dry leaves",
        description="Leaves gathered during home or garden cleanup.",
        category="wet",
        explanation=(
            "Many local systems collect leaves with wet or compostable waste, "
            "but follow your area's separate garden-waste rules."
        ),
    ),
    WasteItem(
        id=5,
        name="Clean cardboard",
        description="A dry cardboard box with no food or oil residue.",
        category="recyclable",
        explanation=(
            "Clean cardboard is commonly recyclable when local services accept "
            "it. Keep it dry and follow local sorting rules."
        ),
    ),
    WasteItem(
        id=6,
        name="Newspaper",
        description="Clean, dry newsprint without food or liquid contamination.",
        category="recyclable",
        explanation=(
            "Clean, dry newspaper is commonly recyclable where paper collection "
            "is available; check local requirements."
        ),
    ),
    WasteItem(
        id=7,
        name="Plastic bottle",
        description="An empty plastic drink bottle.",
        category="recyclable",
        explanation=(
            "Plastic bottles are recyclable only where the local collection "
            "accepts that type of plastic. Check the local rules."
        ),
    ),
    WasteItem(
        id=8,
        name="Metal can",
        description="An empty metal food or drink can.",
        category="recyclable",
        explanation=(
            "Metal cans are commonly accepted for recycling, but acceptance "
            "and preparation rules vary by location."
        ),
    ),
    WasteItem(
        id=9,
        name="Glass jar",
        description="An empty glass jar with its lid removed.",
        category="recyclable",
        explanation=(
            "Glass jars may be recyclable where local services accept them. "
            "Keep broken glass separate and follow safety guidance."
        ),
    ),
    WasteItem(
        id=10,
        name="Multilayer snack wrapper",
        description="A flexible wrapper made from joined layers of materials.",
        category="dry",
        explanation=(
            "Multilayer packaging is usually not accepted in regular recycling. "
            "Put it in dry or reject waste according to local collection rules."
        ),
    ),
    WasteItem(
        id=11,
        name="Broken ceramic cup",
        description="A broken ceramic cup, wrapped to contain sharp pieces.",
        category="dry",
        explanation=(
            "Ceramic is not accepted with ordinary glass recycling in many "
            "places. Secure sharp pieces and follow local dry-waste guidance."
        ),
    ),
    WasteItem(
        id=12,
        name="Soiled plastic packaging",
        description="Plastic packaging with food or oil residue.",
        category="dry",
        explanation=(
            "Soiled packaging may not be accepted for recycling. Follow local "
            "dry or reject-waste rules rather than assuming it is recyclable."
        ),
    ),
)

ITEMS_BY_ID = {item.id: item for item in WASTE_ITEMS}
ITEM_IDS = tuple(ITEMS_BY_ID)
POINTS_PER_CORRECT_ANSWER = 10
GAME_ITEM_COUNT = 10


def select_game_item_ids() -> list[int]:
    return secrets.SystemRandom().sample(ITEM_IDS, GAME_ITEM_COUNT)


def get_public_items(
    item_ids: list[int] | None = None,
) -> list[EcoSortWasteItem]:
    items = WASTE_ITEMS if item_ids is None else (
        ITEMS_BY_ID[item_id] for item_id in item_ids
    )

    return [
        EcoSortWasteItem(
            id=item.id,
            name=item.name,
            description=item.description,
        )
        for item in items
    ]
