import json
import os

def generate_complex_soul(nation, archetype, traumas, mandate, rivalries, resources):
    soul = {
        "nation": nation,
        "historical_archetype": archetype,
        "collective_memory": {
            "core_traumas": traumas,
            "historical_rivals": rivalries
        },
        "civilizational_mandate": mandate,
        "resources": resources,
        "behavioral_anchors": "Actions must align with historical survival patterns."
    }
    path = f"C:/Users/cance/.gemini/antigravity/scratch/Warren Wayne/WIN_System/agents/nations/{nation.lower().replace(' ', '_')}_soul.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(soul, f, indent=2)
    return path

# Expanded Global List (195-Nation Blueprint)
# Note: Generating a representative batch for the major power blocs first
global_blueprint = [
    ["Israel", "Prophetic/Security Citadel", ["Holocaust", "1948/1967 Wars"], "Existential survival and technological dominance", ["Iran", "Hezbollah", "Hamas"], "High-Tech, Intelligence, Gas"],
    ["Ukraine", "Frontier Shield of the West", ["Holodomor", "2022 Invasion"], "Preservation of sovereignty and integration into the West", ["Russia"], "Agriculture, Iron, Defense Tech"],
    ["Poland", "The Martyr of Europe", ["Partitions", "WWII Occupation"], "Becoming the primary military power of the EU to contain the East", ["Russia", "Germany (Historical)"], "Manufacturing, Military Industry"],
    ["Saudi Arabia", "Guardians of the Two Mosques", ["Ottoman control", "Oil volatility"], "Leading the Islamic world and diversifying beyond oil (Vision 2030)", ["Iran"], "Oil, Sovereign Wealth, Logistics"],
    ["Japan", "Shogun/Techno-Zen Hybrid", ["Hiroshima/Nagasaki", "Lost Decades"], "Maintenance of economic status and defense against regional giants", ["China", "North Korea"], "High-Tech, Automation, Maritime Power"],
    ["Vietnam", "The Resilient Dragon", ["Indochina Wars", "Chinese occupations"], "Economic rise through strategic neutrality and export dominance", ["China"], "Manufacturing, Rare Earths"],
    ["Argentina", "The Fallen Giant", ["Hyperinflation", "Malvinas War"], "Restoration of status and radical economic freedom", ["Great Britain (Historical)"], "Agriculture, Lithium, Shale Gas"]
]

if __name__ == "__main__":
    for data in global_blueprint:
        generate_complex_soul(*data)
        print(f"[+] Global Soul Synced: {data[0]}")
