"""Trusted safety knowledge regarding Indian Monsoons.
Contains NDMA (National Disaster Management Authority) guidelines for citizens.
Used to ground the RAG safety assistant pipeline.
"""

from typing import Any

MONSOON_SAFETY_GUIDELINES: list[dict[str, Any]] = [
    {
        "id": "PRE_MONSOON_PREP",
        "category": "preparedness",
        "phase": "before",
        "title": "Pre-Monsoon Property and Drainage Prep",
        "content": (
            "1. Clear drains and gutters around your home to prevent waterlogging.\n"
            "2. Repair roof leaks and seal cracks in walls before rains start.\n"
            "3. Trim weak tree branches near buildings and electric wires.\n"
            "4. Identify a safe route to higher ground in case of floods.\n"
            "5. Keep emergency contact numbers printed and saved."
        ),
    },
    {
        "id": "FLOOD_SAFETY_DURING",
        "category": "safety",
        "phase": "during",
        "title": "During a Flood: Safety & Evacuation",
        "content": (
            "1. Avoid wading or driving through flooded streets. 6 inches of moving water can knock you down, and 2 feet can sweep cars away.\n"
            "2. If water enters your building, turn off electricity at the main switchboard and unplug all appliances.\n"
            "3. Do not touch electrical poles, fallen wires, or metal structures in water.\n"
            "4. Stay tuned to local news and official alerts on radio/television.\n"
            "5. Move children, the elderly, and pets to the safest/highest floor first."
        ),
    },
    {
        "id": "THUNDERSTORM_LIGHTNING",
        "category": "safety",
        "phase": "during",
        "title": "Thunderstorm and Lightning Precautions",
        "content": (
            "1. Stay indoors and avoid taking baths or showers during lightning (pipes conduct electricity).\n"
            "2. Unplug computers, televisions, and other expensive electronic devices.\n"
            "3. If caught outdoors, seek shelter in a concrete building or hard-topped vehicle. Do not stand under trees.\n"
            "4. Avoid metal objects like bicycles, fences, and pipes.\n"
            "5. If in open water, get to land immediately."
        ),
    },
    {
        "id": "POST_FLOOD_RECOVERY",
        "category": "recovery",
        "phase": "after",
        "title": "Post-Monsoon/Post-Flood Safety Guidelines",
        "content": (
            "1. Do not enter flood-damaged buildings until they are cleared as safe.\n"
            "2. Watch out for snakes, scorpions, and insects that may have taken refuge indoors.\n"
            "3. Drink only boiled, filtered, or bottled water to prevent waterborne diseases (cholera, typhoid).\n"
            "4. Dispose of food that has come into contact with floodwater.\n"
            "5. Wear protective gloves and boots when cleaning up mud and water."
        ),
    },
    {
        "id": "EMERGENCY_KIT_LIST",
        "category": "supplies",
        "phase": "before",
        "title": "Indian Household Emergency Kit Essentials",
        "content": (
            "1. Drinking water (3-day supply: 4 liters per person per day).\n"
            "2. Dry food items (biscuits, parched rice/poha, nuts, canned food).\n"
            "3. First aid kit with essential personal medicines, ORS packets, and insect repellent.\n"
            "4. Flashlight/torch with extra batteries, and a fully charged power bank.\n"
            "5. Waterproof plastic pouch containing ID cards, property papers, and cash."
        ),
    },
]


def get_relevant_guidelines(query: str) -> str:
    """Simple keyword matching to retrieve relevant safety guidelines for RAG context."""
    query_lower = query.lower()
    matches = []

    for guide in MONSOON_SAFETY_GUIDELINES:
        # Match against title, category, phase, or content keywords
        if (
            query_lower in guide["title"].lower()
            or query_lower in guide["category"].lower()
            or query_lower in guide["phase"].lower()
            or any(kw in query_lower for kw in ["safety", "monsoon", "prepare", "help"])
        ):
            matches.append(f"[{guide['title']}]:\n{guide['content']}")

    if not matches:
        # Fallback to general safety guidelines
        matches = [
            f"[{guide['title']}]:\n{guide['content']}"
            for guide in MONSOON_SAFETY_GUIDELINES[:2]
        ]

    return "\n\n".join(matches)
