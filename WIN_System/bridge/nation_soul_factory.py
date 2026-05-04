import json
import os

def generate_nation_soul(country_name, archetype, traumas, mandate, resources, religion_culture):
    soul = {
        "nation": country_name,
        "type": "National Soul / Civilizational Agent",
        "historical_archetype": archetype,
        "collective_memory": {
            "core_traumas": traumas,
            "past_glories": "To be populated by historical database."
        },
        "civilizational_mandate": mandate,
        "sub_agents": {
            "geography": "Analysis of physical constraints and borders.",
            "culture_religion": religion_culture,
            "resources": resources,
            "past_conflicts": "Mapping of historical rivalries."
        },
        "logic_gate": "Any action by the current leader must be filtered through this soul. If contradiction > 70%, internal instability arises."
    }
    
    filename = f"{country_name.lower().replace(' ', '_')}_soul.json"
    path = f"C:/Users/cance/.gemini/antigravity/scratch/Warren Wayne/WIN_System/agents/nations/{filename}"
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(soul, f, indent=2)
    return filename

# Initial Batch: The Souls of Power
nations_to_generate = [
    ["Mexico", "Mestizo-Imperial Fusion", ["Loss of 1848 territory", "Colonial legacy"], "Sovereignty at any cost while tethered to the northern giant", "Silver, Lithium, Oil, Strategic Bridge", "Catholic-Guadalupano / Revolutionary Secularism"],
    ["USA", "Exceptionalist Settler Expansionism", ["Civil War division", "Great Depression"], "Global hegemony through Liberal Democracy and Market dominance", "Shale Gas, Tech Supremacy, Global Reserve Currency", "Protestant Ethic / Individualism"],
    ["China", "The Middle Kingdom (Zhongguo)", ["Century of Humiliation", "Great Leap Forward"], "Restoration of Centrality and Internal Harmony", "Rare Earths, Manufacturing Dominance", "Confucian-Communist Synthesis"],
    ["Russia", "Third Rome / Eurasian Fortress", ["Collapse of USSR", "Mongol Invasions"], "Preservation of the Heartland and Anti-Western Containment", "Natural Gas, Nuclear Arsenal, Vast Territory", "Orthodox Christianity / Slavic Identity"],
    ["Hungary", "Magyar Island in a Slavic Sea", ["Treaty of Trianon", "1956 Uprising"], "Survival of the Magyar identity through strategic hedging", "Agricultural richness, Critical transit node", "Christian-Nationalist Conservatism"],
    ["Iran", "Persian Imperial Continuity", ["1953 Coup", "Iran-Iraq War"], "Regional Hegemony and Resistance against Western intervention", "Oil, Strategic Choke Points", "Shia Islam / Persian Pride"]
]

if __name__ == "__main__":
    for nation in nations_to_generate:
        fname = generate_nation_soul(*nation)
        print(f"[+] Soul Generated: {fname}")
