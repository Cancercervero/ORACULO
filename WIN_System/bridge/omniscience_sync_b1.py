import json
import os

# MASTER DATABASE: Block 1 - Middle East, SE Asia, Eastern Europe, Central America
block_1_data = {
    "Israel": {
        "soul": ["Security Citadel", ["Holocaust", "1948/1967 Wars"], "Existential Survival", ["Iran", "Hezbollah"], "High-Tech, Gas"],
        "leader": ["Benjamin Netanyahu", "Aggressive, security-focused", ["Red Lines", "Existential Threat", "Victory"]]
    },
    "Saudi Arabia": {
        "soul": ["Islamic Hegemon", ["Ottoman control"], "Vision 2030 Transformation", ["Iran"], "Oil, Sovereign Wealth"],
        "leader": ["Mohammed bin Salman", "Visionary, ambitious, neutralist", ["Vision 2030", "Giga-projects", "Stability"]]
    },
    "Vietnam": {
        "soul": ["Resilient Dragon", ["Indochina Wars"], "Strategic Neutrality and Growth", ["China"], "Manufacturing, Rare Earths"],
        "leader": ["To Lam", "Pragmatic, stability-focused", ["Bamboo Diplomacy", "Tech Rise", "Stability"]]
    },
    "Ukraine": {
        "soul": ["Frontier Shield", ["2022 Invasion"], "Sovereignty and EU/NATO integration", ["Russia"], "Agriculture, Defense Tech"],
        "leader": ["Volodymyr Zelenskyy", "Resilient, communicative, urgent", ["Victory Plan", "Reconstruction", "Unity"]]
    },
    "Philippines": {
        "soul": ["Archipelago Shield", ["Colonial occupation"], "US Alliance against Maritime expansion", ["China"], "Mining, Electronics"],
        "leader": ["Bongbong Marcos", "Pro-US, sovereignty-focused", ["Island Security", "Modernization", "Alliance"]]
    },
    "Panama": {
        "soul": ["Global Choke Point", ["US Intervention"], "Maritime Logistics Hub", ["Regional Instability"], "Canal Revenue, Finance"],
        "leader": ["Jose Raul Mulino", "Business-oriented, security-focused", ["Canal Security", "Logistics Hub", "Stability"]]
    }
    # This list will be expanded to the full 50 of Block 1
}

def generate_block_identity(country, soul_data, leader_data):
    # Nation Soul
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
    
    # Leader KB
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

if __name__ == "__main__":
    for country, data in block_1_data.items():
        generate_block_identity(country, data["soul"], data["leader"])
        print(f"[+] Block 1 Synced: {country}")
