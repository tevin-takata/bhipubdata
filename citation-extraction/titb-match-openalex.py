import json
from tqdm import tqdm
import requests

titb_publications_path = "data/extraction/titb_publications.json"
output_path = "data/titbpubdata.json"

def load_titb_publications(path):
    with open(path, "r") as file:
        return json.load(file)

# Normalize DOI by removing "https://doi.org/" prefix
def normalize_doi(doi):
    if doi and doi.startswith("https://doi.org/"):
        return doi[len("https://doi.org/") :]
    return doi

def query_openalex(doi):
    base_url = "https://api.openalex.org/works/https://doi.org/"
    response = requests.get(base_url + doi)

    if response.status_code == 200:
        return response.json()
    else:
        return None

# Match and enrich BHI publications
def enrich_bhi_publications(bhi_publications):
    enriched_publications = []
    matched_count = 0
    unmatched_count = 0

    print("PROCESS: Start enriching TITB publications with OpenAlex data...")
    pbar = tqdm(total=len(bhi_publications), desc="Enriching", position=0, leave=True)

    for publication in bhi_publications:
        ee = publication.get("ee")
        matched = False

        for ee_entry in ee:
            normalized_ee = normalize_doi(ee_entry)
            openalex_data = query_openalex(normalized_ee)
            if openalex_data:
                publication.update({
                    "id": openalex_data.get("id"),
                    "concepts": openalex_data.get("concepts"),
                    "referenced_works": openalex_data.get("referenced_works"),
                    "cited_by_count": openalex_data.get("cited_by_count"),
                })
                matched = True
                break

        if matched:
            matched_count += 1
        else:
            unmatched_count += 1

        enriched_publications.append(publication)
        pbar.update(1)

    pbar.close()
    print("PROCESS: Enrichment completed.")
    print(f"LOG: Total publications: {len(bhi_publications)}, Matched: {matched_count}, Unmatched: {unmatched_count}")

    return enriched_publications

def save_enriched_publications(path, data):
    with open(path, "w") as file:
        json.dump(data, file, indent=4)

print("PROCESS: Loading TITB publications...")
titb_publications = load_titb_publications(titb_publications_path)
print("LOG: Loaded {} TITB publications.".format(len(titb_publications)))

enriched_publications = enrich_bhi_publications(titb_publications)

print("PROCESS: Saving enriched publications...")
save_enriched_publications(output_path, enriched_publications)
print("LOG: Enriched publications saved to {}".format(output_path))
print("DONE")