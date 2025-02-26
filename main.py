import re
import requests
from bs4 import BeautifulSoup
from typing import Any
from typing import Optional


def extract_visible_text(url: str) -> Optional[str]:
    """
    Fetches the webpage content from the given URL and extracts all visible text.

    Args:
        url (str): The URL of the webpage.

    Returns:
        Optional[str]: The extracted visible text from the webpage, or None if the request fails.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raises an error for bad responses (4xx and 5xx)

        soup = BeautifulSoup(response.text, "html.parser")

        # Function to filter visible text
        def is_visible(element : Any) -> bool:
            if element.parent.name in ["style", "script", "head", "meta", "noscript"]:
                return False
            return True

        text_elements = soup.find_all(string=True)
        visible_texts = filter(is_visible, text_elements)

        return " ".join(text.strip() for text in visible_texts if text.strip())

    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None

# Example usage
# print(extract_visible_text("https://example.com"))


def get_conference_page(url:str) -> str|None:
    """Fetches the main page content of the given conference URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()   
        return str(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def extract_dates(text:str) -> list[str]:
    """Extract conference dates using regex."""
   
    month = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)\.?'
    day = r'\d{1,2}(?:st|nd|rd|th)?'
    dash_day = fr'(?:\s?[-–]\s?{day})'
    year = r'(?:\d{{4}})'

    # Use double {{ }} to work properly with the f string 
    sub_pattern = r'(\d{1,2})([./])(\d{1,2})(\2\d{2,4})?\b'
    date_patterns = [
        # r'\d{1,2}([./-])\d{1,2}(?:\1\d{2,4})?',
        fr'{sub_pattern}(\s?-\s?\d{{1,2}}\2\d{{1,2}}(?:\2\d{{2,4}})?)?(?!\s?{month})' , #(Doesn't end with a month)
        fr'{month}\s?{day}{dash_day}?(?:\s*,?\s*{year})?',
        fr'{day}{dash_day}?\s?{month}(?:\s*,?\s*{year})?'
    ]
    
        # fr'\b{month}\s+\d{1,2},?\s+\d{4}\b',
        # fr'\b{month}\s+\d{{1,2}},?\s+\d{{4}}\b',
        # r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b',
        # r'\b\d{1,2}(?P<date_sep>[./-])\d{1,2}(?:${date_sep}\d{2,4})?\b',
        # r'\b\d{1,2}(?P<date_sep>[./-])\d{1,2}(?:(?P=date_sep)\d{2,4})?\b',
        # fr'\b\d{{1,2}}\s*(?:st|nd|rd|th)?\s*{month}\s*\d{{4}}\b',
        # r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2}\s*(st|nd|rd|th)?\s*([-–]\s*\d{1,2}\s*(st|nd|rd|th)?)?\s*,?\s*(\d{4})?\b',
        # r'\b\d{1,2}\s*(st|nd|rd|th)?\s*([-–]\s*\d{1,2}\s*(st|nd|rd|th)?)?\s(January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*(\d{4})?\b'
        # fr'\b{month}\s?{day}\b',
        # fr'\b{month}\s?{day}\s?(?:[-–]\s*{day})?\s*,?\s*{year}?\b',
        # fr'\b{month}\s?\d{{1,2}}\s?(?:st|nd|rd|th)?\s?(?:[-–]\s*\d{{1,2}}\s*(?:st|nd|rd|th)?)?\s*,?\s*(?:\d{{4}})?\b',

    dates = []
    for pattern in date_patterns:
        # dates.extend(re.findall(pattern, text, re.IGNORECASE))
        dates.extend([''.join(match) for match in re.findall(pattern, text, re.IGNORECASE)] )
    return dates


def main(url: str = "") -> None:
    if url == "":
        url = input("Enter the conference website URL: ")

    
    print(f"Current URL: {url}  <=========================================")

    vis_text = extract_visible_text(url)
    # print(vis_text)
    
    # Extract dates
    if vis_text:
        conference_dates = extract_dates(vis_text)
        print("Extracted Dates:", conference_dates)

    
    # html_content = get_conference_page(url)
    # print(html_content)
    # if vis_text:
    #     soup = BeautifulSoup(html_content, 'html.parser')
    #     text = soup.get_text()
        
    #     # Extract dates
    #     conference_dates = extract_dates(text)
    #     print("Extracted Dates:", conference_dates)

if __name__ == "__main__":

    # test_urls = [ "https://icml.cc/" , "https://nips.cc/"]
    # Example urls
    test_urls =    [
        "https://ijcai24.org/",
        "http://icaps24.icaps-conference.org/",
        "https://www.ecai2024.eu/",
        "https://aaai.org/aaai-24-conference/",
        "https://setn2024.cs.unipi.gr/",
        "https://pci2024.uniwa.gr/",
        "https://www.aamas2024-conference.auckland.ac.nz/",
        "https://kr.org/KR2024/",
        "https://sites.google.com/view/cpaior2024",
        "https://cp2024.a4cp.org/"
    ]

   

    for url in test_urls:
        main(url)
        print()
        # break
