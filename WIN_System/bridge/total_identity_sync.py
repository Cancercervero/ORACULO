import json
import os

# Database of Leader Rhetoric and National Soul Archetypes for 2026
world_data = {
    "Russia": {
        "soul": ["Third Rome", ["Collapse of USSR", "Western Encirclement"], "Preservation of the Heartland", ["USA", "Poland", "Ukraine"], "Gas, Nuclear, Military Tech"],
        "leader": ["Vladimir Putin", "Stoic, aggressive, historical-focused", ["Multipolarity", "Security Guarantees", "Sovereignty"]]
    },
    "China": {
        "soul": ["Middle Kingdom", ["Century of Humiliation"], "Global Centrality", ["USA", "Japan", "India"], "Manufacturing, Tech, Rare Earths"],
        "leader": ["Xi Jinping", "Disciplined, visionary, ideological", ["Common Prosperity", "Chinese Dream", "Belt and Road"]]
    },
    "France": {
        "soul": ["Imperial Republic", ["Loss of Empire", "Nazi Occupation"], "Grandeur and EU Leadership", ["UK", "Sahel AES"], "Nuclear Energy, Luxury, Aerospace"],
        "leader": ["Emmanuel Macron", "Intellectual, assertive, pro-EU", ["European Sovereignty", "Strategic Autonomy"]]
    },
    "Argentina": {
        "soul": ["Fallen Prosperity", ["Hyperinflation", "Malvinas"], "Economic Liberty and Glory Recovery", ["UK"], "Agriculture, Lithium"],
        "leader": ["Javier Milei", "Eccentric, libertarian, radical", ["Chainsaw", "Anarcho-capitalism", "Freedom"]]
    },
    "El Salvador": {
        "soul": ["Resurgent Safety", ["Civil War", "Gangs"], "Technological and Security Hub", ["Traditional Institutions"], "Bitcoin, Geothermal Energy"],
        "leader": ["Nayib Bukele", "Millennial, tech-savvy, strongman", ["Security First", "Bitcoin City", "New Ideas"]]
    }
    # This list will be expanded to 195 programmatically in the factory script
}

def generate_full_identity(country, soul_data, leader_data):
    # Generate Nation Soul
    soul = {
        "nation": country,
        "archetype": soul_data[0],
        "traumas": soul_data[1],
        "mandate": soul_data[2],
        "rivals": soul_data[3],
        "resources": soul_data[4]
    }
    soul_path = f"C:/Users/cance/.gemini/antigravity/scratch/Warren Wayne/WIN_System/agents/nations/{country.lower().replace(' ', '_')}_soul.json"
    os.makedirs(os.path.dirname(soul_path), exist_ok=True)
    with open(soul_path, 'w', encoding='utf-8') as f:
        json.dump(soul, f, indent=2)
    
    # Generate Leader KB
    kb = {
        "leader": leader_data[0],
        "style": leader_data[1],
        "keywords": leader_data[2],
        "nation": country
    }
    kb_path = f"C:/Users/cance/.gemini/antigravity/scratch/Warren Wayne/WIN_System/agents/knowledge_base/{leader_data[0].lower().replace(' ', '_')}_kb.json"
    os.makedirs(os.path.dirname(kb_path), exist_ok=True)
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(kb, f, indent=2)
    
    return country

if __name__ == "__main__":
    for country, data in world_data.items():
        generate_full_identity(country, data["soul"], data["leader"])
        print(f"[+] Total Identity Synced: {country}")
