import json
import os

def generate_persona(name, role, country, traits, background):
    persona = {
        "name": name,
        "role": role,
        "country": country,
        "background": {
            "experience": background,
            "traits": traits
        },
        "behavioral_patterns": {
            "strategy": "To be populated by real-time intelligence feeds."
        }
    }
    filename = f"{name.lower().replace(' ', '_')}_persona.json"
    path = f"C:/Users/cance/.gemini/antigravity/scratch/Warren Wayne/WIN_System/agents/personas/{filename}"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(persona, f, indent=2)
    return filename

agents_to_create = [
    # Central Asia & Oceania (The Resource Nodes)
    ["Kassym-Jomart Tokayev", "President of Kazakhstan", "Kazakhstan", ["Multivector diplomacy", "Energy security"], "Balancing relations between Russia, China, and the West while controlling massive oil/uranium reserves"],
    ["Shavkat Mirziyoyev", "President of Uzbekistan", "Uzbekistan", ["Reform", "Regional leadership"], "Opening Uzbekistan's economy and positioning it as a Central Asian trade hub"],
    ["Anthony Albanese", "Prime Minister of Australia", "Australia", ["AUKUS", "Indo-Pacific Security"], "Leading Australia's strategic pivot toward a maritime containment of China"],
    
    # European Transitions (2026 Confirmed)
    ["Peter Magyar", "Prime Minister of Hungary", "Hungary", ["Institutional Reform", "EU Alignment"], "Replaced Viktor Orban in 2026, leading a new era of Hungarian-EU cooperation"],
    ["Antonio Jose Seguro", "President of Portugal", "Portugal", ["Stability", "Social Reform"], "Newly elected leader of Portugal, focusing on Atlantic security"],
    ["Friedrich Merz", "Chancellor of Germany", "Germany", ["Re-armament", "Economic Focus"], "Conservative leader who replaced Scholz, moving Germany toward a more hawkish and pro-industry stance"],
    
    # Southeast Asia (The Emerging Giants)
    ["Prabowo Subianto", "President of Indonesia", "Indonesia", ["Nationalism", "Infrastructure"], "Leading Indonesia's rise as a G20 powerhouse and nickel dominant producer"],
    ["Sanae Takaichi", "Prime Minister of Japan", "Japan", ["Defense", "Semiconductor Sovereignty"], "First female PM, focusing on Japanese re-armament and tech dominance"],
    ["Lee Jae-myung", "President of South Korea", "South Korea", ["Social Wealth", "Pragmatism"], "Leading Korea's tech sector and social restructuring"],
    
    # Middle East Refinement
    ["Mojtaba Khamenei", "Supreme Leader of Iran", "Iran", ["Aggressive Defense", "Resistance"], "Leading Iran into a more militant phase after succeeding his father in 2026"],
    ["Delcy Rodriguez", "Acting President of Venezuela", "Venezuela", ["Survival", "Transition"], "Managing a post-Maduro Venezuela under intense global scrutiny"]
]

if __name__ == "__main__":
    os.makedirs("C:/Users/cance/.gemini/antigravity/scratch/Warren Wayne/WIN_System/agents/personas", exist_ok=True)
    created = []
    for agent in agents_to_create:
        fname = generate_persona(*agent)
        created.append(fname)
    
    print(f"[+] Successfully generated {len(created)} core agents.")
    print(f"Files: {', '.join(created)}")
