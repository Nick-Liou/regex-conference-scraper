import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Any, List
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


def extract_dates(text:str) -> list[str]:
    """Extract dates using regex."""
   
    month = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)\.?'
    day = r'\d{1,2}(?:st|nd|rd|th)?'
    dash_day = fr'(?:\s?[-–]\s?{day})'
    year = r'(?:\d{4})'
   
    # Use double {{ }} to work properly with the f string 
    ref_index = 2
    sub_pattern = fr'\d{{1,2}}([./])\d{{1,2}}\{ref_index}\d{{2,4}}?'
    date_patterns = [
        fr'({sub_pattern}(?:\s?-\s?\d{{1,2}}\{ref_index}\d{{1,2}}(?:\{ref_index}\d{{2,4}})?)?(?!\s?{month}))'       + '|' 
        fr'({month}\s?{day}{dash_day}?(?:\s*,?\s*{year})?)'                                   + '|' 
        fr'(\s{day}{dash_day}?\s?{month}(?:\s*,?\s*{year})?)'
    ]
          
    dates = []
    for pattern in date_patterns:
        dates.extend([''.join(match) for match in re.findall(pattern, text, re.IGNORECASE)] )
    return dates


# Not used 
def get_conference_name(url :str) -> str:    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an error for bad responses (4xx and 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the title tag
        title = soup.title.string if soup.title else "No title found"
        
        return title.strip()
        
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return f"Error fetching the webpage: {e}"

def get_full_conference_name(url :str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an error for bad responses (4xx and 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')

        
        # Extract the title
        title = soup.title.string if soup.title else "No title found"
        
        # Extract potential abbreviation (e.g., "ICML 2024")
        match = re.search(r'\b[A-Z]{2,6}(?:\s?\d{4})?\b', title)
        abbreviation = match.group(0) if match else None

        if not abbreviation:
            return title.strip()  # Return the title if no abbreviation is found
        
        def build_regex(abbreviation:str)->str:
            words = list(abbreviation)  # Split abbreviation into letters
            pattern = r""  # Word boundary
            
            for i, letter in enumerate(words):
                if i > 0:
                    pattern += r",?-?\s*(?:(?:on|of|for|and|in|for the)\s+)?"  # Optional connective words
                pattern += rf"\b{letter}\w+\b"  # Match a word starting with the letter

            pattern += r""  # Word boundary
            return "(" + pattern + ")"

        abbreviation = abbreviation.split()[0]
        print(f"Abbreviation: {abbreviation}")
        # Search for the full name in the page text
        text = soup.get_text()

        pattern = build_regex(abbreviation)

        matches = [''.join(match) for match in re.findall(pattern, text, re.IGNORECASE)] 


        if matches:
            def clean_text(s:str)->str:
                return re.sub(r'[\s\xa0]+', ' ', s).strip()  # Replace all whitespace-like chars with a single space

                    
            # Apply cleaning
            cleaned_strings = [clean_text(s) for s in matches]

            from collections import Counter

            def most_frequent_string(strings:list[str]) -> str:
                # Create a Counter object to count occurrences
                counter = Counter(strings)
                
                # Find the most common element
                most_common = counter.most_common(1)  # Returns a list of tuples (item, count)
                
                return most_common[0][0]  # Return the string with the highest count

            return most_frequent_string(cleaned_strings)
        
        return title.strip()
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return f"Error fetching the webpage: {e}"


def get_conference_date(url :str) -> str:

    vis_text = extract_visible_text(url)

    if vis_text:
        conference_dates = extract_dates(vis_text)
        # print("All Dates found:", conference_dates)
    else:
        return "No date found"
    
    if len(conference_dates)>1:
        if conference_dates[0] in conference_dates[1]:
            return conference_dates[1]

    if conference_dates[0][-1] in ['.' , '/']:
        return conference_dates[0][:-1]

    return conference_dates[0]



def find_conference_venue(homepage_url:str) -> str:
    try:
        # Get the homepage content
        response = requests.get(homepage_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links on the homepage
        links = [a['href'] for a in soup.find_all('a', href=True)]
        
        # Filter links that likely contain venue information
        venue_keywords = ['venue', 'location', 'conference-center', 'hotel']
        venue_links = [link for link in links if any(keyword in link.lower() for keyword in venue_keywords)]
        
        if not venue_links:
            return "No venue page found."
                

        venue_url = urljoin(homepage_url, venue_links[0])  # Join relative URLs
        
        venue_response = requests.get(venue_url)
        venue_response.raise_for_status()
        venue_soup = BeautifulSoup(venue_response.text, 'html.parser')
        
        # Extract venue details preserving structure
        paragraphs = [" ".join(p.stripped_strings) for p in venue_soup.find_all(['p','pre','span'])]      
        
        venue_match = next((line for line in paragraphs if re.search(r'(?i)(will take place in|is being held at|will be held at|(the)? venue is|venue of the main conference is|will be located at)', line)), None)
                
        if venue_match:
            return venue_match
        else:
            return "Venue details not found explicitly on the page."
    
    except requests.RequestException as e:
        return f"Error fetching data: {e}"



def find_fees(url:str)->list[list[list[str]]] | str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an error for bad responses (4xx and 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all links on the homepage
        links = [a['href'] for a in soup.find_all('a', href=True)]

        
        # Filter links that likely contain venue information
        fee_keywords = ['register', 'registration']
        fee_links = [link for link in links if any(keyword in link.lower() for keyword in fee_keywords)]
        
        if not fee_links:
            return "No fee/registration page found."
        
        fee_url = urljoin(url, fee_links[0])  # Join relative URLs
        
        response = requests.get(fee_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        fee_finder = re.compile(r'\b(?:early[\W]|late|standard|onsite|on-site|main conference|regular|(eetn|non eetn"|epy|non-epy)\s(member))\b', re.IGNORECASE)

        tables =  [p if re.findall(fee_finder,p.get_text()) else None for p in soup.find_all(['table'])] 
        
        tables_with_fees = []
        for i,t in enumerate(tables,1):
            if t:
                fee_table = []
                for row in t.find_all('tr'): 

                    row_text = [str(td.get_text(strip=True)) for td in row.find_all(['td','th'])]
                    if row_text:
                        fee_table.append(row_text) 
                tables_with_fees.append(fee_table)
        

        
        if tables_with_fees:
            return tables_with_fees
        else:
            return "No fees were extracted"
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return f"Error fetching the webpage: {e}"



def print_fees(tables: List[List[List[str]]] | str ) -> None:

    if isinstance(tables, str):
        print(tables)
        return 
    

    for i,table in enumerate(tables,1):
        print(f"Fee Table {i}:")
        print_table(convert_lists_to_even_lists(table))
        print("\n\n")

def convert_lists_to_even_lists(table: List[List[str]]) -> List[List[str]]:
    max_len = max(len(sub) for sub in table)  # Get max row length
    
    return [[""] * (max_len - len(sub)) + sub for sub in table]  # Prepend empty strings

def print_table(data: List[List[str]]) -> None:
    col_widths = [max(len(row[i]) if i < len(row) else 0 for row in data) for i in range(max(map(len, data)))]
    
    for row in data:
        print("  ".join(cell.ljust(col_widths[i]) if i < len(row) else " " * col_widths[i] for i, cell in enumerate(row)))



def main(url: str = "") -> None:
    if url == "":
        url = input("Enter the conference website URL: ")
    
    print(f"Conference URL: {url}")     

    print("Conference Date :", get_conference_date(url) ) 

    print("Conference Name :", get_full_conference_name(url))  

    print("Venue:" , find_conference_venue(url))

    # Fees:
    print_fees(find_fees(url))
    

if __name__ == "__main__":

    main()

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

    # Run for all test urls
    # for url in test_urls:
    #     main(url)
    #     print()
