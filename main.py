import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
from tqdm import tqdm

def get_publication_titles(base_url):
    try:
        # Get the HTML content of the page
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Open a text file to save the results
        with open('publication_links.txt', 'w') as file:
            # Find all publication entries on the page
            publications = soup.find_all('div', class_='article')
            
            # Iterate over all publications and get the title
            for index, pub in enumerate(tqdm(publications, desc="Processing publications"), start=1):
                # Get the title of the paper
                title_tag = pub.find(['h2', 'h3', 'h4'])  # Search for h2, h3, or h4 tags for the title
                title = title_tag.get_text(strip=True) if title_tag else 'No title found'
                file.write(f'{index}. {title}\n')
                title_words = set(title.lower().split())
                
                # Find the [Paper] link
                paper_link = pub.find('a', string='[Paper]')
                if paper_link:
                    href = paper_link.get('href').strip()
                    if href:
                        # Construct the full URL using the base link
                        full_url = href if href.startswith('http') else 'https://spqrlab1.github.io/' + href.lstrip('/')
                        file.write(f'URL: {full_url}\n')

                        # Visit the link and check if the title is in the page content
                        try:
                            paper_response = requests.get(full_url)
                            paper_response.raise_for_status()

                            # Check if the content is a PDF
                            if 'application/pdf' in paper_response.headers.get('Content-Type', '').lower():
                                # Read the PDF content
                                with io.BytesIO(paper_response.content) as pdf_file:
                                    reader = PyPDF2.PdfReader(pdf_file)
                                    pdf_text = ''
                                    for page_num in range(len(reader.pages)):
                                        page_content = reader.pages[page_num].extract_text()
                                        if page_content:
                                            pdf_text += page_content.lower()
                                    pdf_words = set(pdf_text.split())
                                    if len(title_words.intersection(pdf_words)) >= len(title_words) / 2:
                                        file.write(f'Title found in the paper link content\n')
                                    else:
                                        file.write(f'Title NOT found in the paper link content\n')
                                    # Write the first 100 characters of the page content
                                    file.write(f'First 100 characters of content: {pdf_text[:100]}\n')
                            else:
                                # If not a PDF, parse as HTML
                                paper_soup = BeautifulSoup(paper_response.content, 'html.parser')
                                page_text = paper_soup.get_text(separator=' ').strip().lower()
                                page_words = set(page_text.split())
                                if len(title_words.intersection(page_words)) >= len(title_words) / 2:
                                    file.write(f'Title found in the paper link content\n')
                                else:
                                    file.write(f'Title NOT found in the paper link content\n')
                                # Write the first 100 characters of the page content
                                file.write(f'First 100 characters of content: {page_text[:100]}\n')
                        except requests.RequestException as e:
                            file.write(f'Failed to retrieve the paper link: {e}\n')
                    else:
                        file.write('URL: No link found\n')
                else:
                    file.write('URL: No [Paper] link found\n')
                
                # Add two lines of whitespace with a dashed line in the middle
                file.write('\n--------------------\n\n')
    except requests.RequestException as e:
        with open('publication_links.txt', 'w') as file:
            file.write(f'Failed to retrieve the webpage: {e}\n')

if __name__ == "__main__":
    from tqdm import tqdm
    base_url = 'https://spqrlab1.github.io/publications.html'
    get_publication_titles(base_url)
