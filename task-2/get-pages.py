import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


def extract_main_content(soup):
    content_text = ""
    main_content = soup.find('div', {'id': 'content'})
    if not main_content:
        main_content = soup.find('main')
    if not main_content:
        main_content = soup.find('article')

    if main_content:
        for element in main_content(['script', 'style', 'nav', 'header', 'footer',
                                     'aside', 'form', 'table', 'ul', 'ol', 'figure',
                                     '.navbox', '.infobox', '.quote', '.references']):
            element.decompose()

        paragraphs = main_content.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            if text and len(text) > 20:
                content_text += text + '\n\n'

    return content_text


def extract_biography_section(soup):
    biography_text = ""
    biography_headers = soup.find_all(['h2', 'h3'], string=re.compile(r'biography', re.I))

    for header in biography_headers:
        current = header
        while True:
            current = current.find_next_sibling()
            if not current or current.name in ['h2', 'h3']:
                break

            if current.name == 'p':
                text = current.get_text().strip()
                if text:
                    biography_text += text + '\n\n'

    return biography_text


def clean_html_to_text(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    main_text = extract_main_content(soup)
    biography_text = extract_biography_section(soup)
    combined_text = main_text + "\n" + biography_text
    combined_text = re.sub(r'\n\s*\n', '\n', combined_text)
    combined_text = combined_text.strip()
    combined_text = re.sub(r'\[\d+\]', '', combined_text)
    combined_text = re.sub(r'\s+\[\d+\]', '', combined_text)
    combined_text = re.sub(r'\s+', ' ', combined_text)
    return combined_text


def save_page_as_text(base_url, title, output_dir):
    try:
        print(f"Обрабатываю: {base_url + title}")
        response = requests.get(base_url + title, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=15)
        response.raise_for_status()
        clean_text = clean_html_to_text(response.content, base_url + title)

        filepath = os.path.join(output_dir, title + ".txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(clean_text)

        return filepath

    except Exception as e:
        print(f"Ошибка при обработке {title}: {e}")
        return None


if __name__ == "__main__":
    base_url = "https://starwars.fandom.com/wiki/"
    urls = [
        "Darth_Sidious",
        "Landonis_Balthazar_Calrissian",
        "Obi-Wan_Kenobi",
        "Chewbacca",
        "Rael_Averross",
        "Qui-Gon_Jinn",
        "Yoda",
        "Dooku",
        "Cin_Drallig",
        "Mace_Windu",
        "Ki-Adi-Mundi",
        "Reva_Sevander",
        "Seventh_Sister",
        "Savage_Opress",
        "Asajj_Ventress",
        "Quinlan_Vos",
        "Wilhuff_Tarkin",
        "R2-D2",
        "C-3PO",
        "Han_Solo",
        "Leia_Skywalker_Organa_Solo",
        "Padmé_Amidala",
        "Bail_Prestor_Organa",
        "Breha_Organa",
        "Luke_Skywalker",
        "Anakin_Skywalker",
        "Darth_Vader",
        "Rey_Skywalker",
        "Kylo_Ren",
        "Ben_Solo",
        "Ahsoka_Tano",
        "Grogu",
        "Din_Djarin",
    ]

    for title in urls:
        result = save_page_as_text(
            base_url="https://starwars.fandom.com/wiki/",
            title = title,
            output_dir='task-2/knowledge_base/')
        if result:
            print(f"Успешно обработано: {os.path.basename(result)}\n")