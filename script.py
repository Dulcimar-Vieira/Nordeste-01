import requests
import gzip
import xml.etree.ElementTree as ET
import io
import json
import os

# URL do feed
feed_url = "https://feeds.whatjobs.com/sinerj/sinerj_pt_BR.xml.gz"

# Criar pasta para os arquivos JSON
json_folder = "json_parts"
os.makedirs(json_folder, exist_ok=True)

# Contador de arquivos
file_count = 1

# Estados do Nordeste (minúsculo para comparação)
estados_desejados = [
    "alagoas",
    "ceará",
    "maranhão",
    "paraíba",
    "pernambuco",
    "piauí",
    "rio grande do norte",
    "sergipe",
    "bahia"
]

# Cidades que NÃO queremos
cidades_excluidas = [
    "salvador",
    "camaçari",
    "lauro de freitas",
    "feira de santana",
    "simões filho"
]

# Mapa de estados -> sigla (para título SEO)
siglas_estados = {
    "alagoas": "AL",
    "ceará": "CE",
    "maranhão": "MA",
    "paraíba": "PB",
    "pernambuco": "PE",
    "piauí": "PI",
    "rio grande do norte": "RN",
    "sergipe": "SE",
    "bahia": "BA"
}

# Baixar o feed XML comprimido
try:
    response = requests.get(feed_url, stream=True, timeout=60)
except requests.exceptions.RequestException as e:
    print(f"Erro ao baixar o feed: {e}")
    exit(1)

if response.status_code == 200:
    with gzip.open(io.BytesIO(response.content), "rt", encoding="utf-8") as f:
        jobs = []
        for event, elem in ET.iterparse(f, events=("end",)):
            if elem.tag == "job":

                location_elem = elem.find("locations/location")
                city = location_elem.findtext("city", "").strip() if location_elem is not None else ""
                state = location_elem.findtext("state", "").strip() if location_elem is not None else ""

                if not city or not state:
                    elem.clear()
                    continue

                city_lower = city.lower()
                state_lower = state.lower()

                # FILTRO PRINCIPAL
                if state_lower in estados_desejados and city_lower not in cidades_excluidas:

                    company = elem.findtext("company/name", "").strip()
                    if not company:
                        company = "Confidencial"

                    original_title = elem.findtext("title", "").strip()

                    # SIGLA DO ESTADO
                    uf = siglas_estados.get(state_lower, "")

                    # TÍTULO AUTOMÁTICO SEO
                    titulo_final = f"{original_title} em {city} ({uf})"

                    job_data = {
                        "title": titulo_final,
                        "description": elem.findtext("description", "").strip(),
                        "company": company,
                        "city": city,
                        "state": state,
                        "url": elem.findtext("urlDeeplink", "").strip(),
                        "tipo": elem.findtext("jobType", "").strip(),
                    }

                    jobs.append(job_data)

                elem.clear()

                # Salvar a cada 1000 vagas
                if len(jobs) >= 1000:
                    json_path = os.path.join(json_folder, f"part_{file_count}.json")
                    with open(json_path, "w", encoding="utf-8") as json_file:
                        json.dump(jobs, json_file, ensure_ascii=False, indent=2)

                    print(f"Arquivo salvo: {json_path}")
                    jobs = []
                    file_count += 1

        # Salvar restante
        if jobs:
            json_path = os.path.join(json_folder, f"part_{file_count}.json")
            with open(json_path, "w", encoding="utf-8") as json_file:
                json.dump(jobs, json_file, ensure_ascii=False, indent=2)

            print(f"Arquivo final salvo: {json_path}")

    print(f"JSONs gerados: {os.listdir(json_folder)}")

else:
    print(f"Erro ao baixar o feed: código HTTP {response.status_code}")
    exit(1)
