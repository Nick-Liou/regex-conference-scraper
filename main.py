import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
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
    year = r'(?:\d{4})'

    # # Use double {{ }} to work properly with the f string 
    # sub_pattern = r'(\d{1,2})([./])(\d{1,2})(\2\d{2,4})?\b'
    # date_patterns = [
    #     fr'{sub_pattern}(\s?-\s?\d{{1,2}}\2\d{{1,2}}(?:\2\d{{2,4}})?)?(?!\s?{month})' , #(Doesn't end with a month)
    #     fr'{month}\s?{day}{dash_day}?(?:\s*,?\s*{year})?',
    #     fr'{day}{dash_day}?\s?{month}(?:\s*,?\s*{year})?'
    # ]
    
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
        # dates.extend(re.findall(pattern, text, re.IGNORECASE))
        dates.extend([''.join(match) for match in re.findall(pattern, text, re.IGNORECASE)] )
    return dates


def get_conference_name(url :str) -> str:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract the title tag
    title = soup.title.string if soup.title else "No title found"
    
    return title.strip()

def get_full_conference_name(url :str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    
    # Extract the title
    title = soup.title.string if soup.title else "No title found"
    
    # Extract potential abbreviation (e.g., "ICML 2024")
    # match = re.search(r'\b[A-Z]{2,6}\s?\d{4}\b', title)
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
    print(f"abbreviation = {abbreviation}")
    # Search for the full name in the page text
    text = soup.get_text()
    # pattern = rf'\b({abbreviation})\b\s+\(([^)]+)\)'

    pattern = build_regex(abbreviation)

    matches = [''.join(match) for match in re.findall(pattern, text, re.IGNORECASE)] 


    if matches:
        def clean_text(s:str)->str:
            return re.sub(r'[\s\xa0]+', ' ', s).strip()  # Replace all whitespace-like chars with a single space

                
        # Apply cleaning
        cleaned_strings = [clean_text(s) for s in matches]
        # print(cleaned_strings)

        from collections import Counter

        def most_frequent_string(strings:list[str]) -> str:
            # Create a Counter object to count occurrences
            counter = Counter(strings)
            
            # Find the most common element
            most_common = counter.most_common(1)  # Returns a list of tuples (item, count)
            
            return most_common[0][0]  # Return the string with the highest count

        return most_frequent_string(cleaned_strings)
    
    return title.strip()
    

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
        
        # print(f"venue_links: {venue_links}")
        if not venue_links:
            return "No venue page found."
        
        # Visit the first likely venue link
        # venue_url = venue_links[0]
        # if not venue_url.startswith('http'):
        #     venue_url = homepage_url.rstrip('/') + '/' + venue_url.lstrip('/')

        venue_url = urljoin(homepage_url, venue_links[0])  # Join relative URLs
        print(f"venue_url: {venue_url}")

        venue_response = requests.get(venue_url)
        venue_response.raise_for_status()
        venue_soup = BeautifulSoup(venue_response.text, 'html.parser')
        
        # Extract venue details using heuristics
        # venue_text = venue_soup.get_text()
        # print("venue_text: \n", venue_text)
        # venue_match = re.search(r'(?i)(venue|location):\s*(.+)', venue_text)

        # venue_text = [line.strip() for line in venue_soup.stripped_strings]
        # print("venue_text: \n", venue_text)
        # venue_match = next((line for line in venue_text if re.search(r'(?i)(will take place in|is being held at|will be held at)', line)), None)
        # print("venue_match old:" , venue_match)

        # Extract venue details preserving structure
        paragraphs = [" ".join(p.stripped_strings) for p in venue_soup.find_all(['p','pre','span'])]
        # print("paragraphs: \n", paragraphs)
        


        
        venue_match = next((line for line in paragraphs if re.search(r'(?i)(will take place in|is being held at|will be held at|(the)? venue is|venue of the main conference is|will be located at)', line)), None)
        # print("venue_match from paragraphs:" , venue_match)
        
        
        if venue_match:
            return venue_match
        else:
            return "Venue details not found explicitly on the page."
    
    except requests.RequestException as e:
        return f"Error fetching data: {e}"


# https://ijcai24.org/register/

def find_fees(url:str)->str:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all links on the homepage
    links = [a['href'] for a in soup.find_all('a', href=True)]
    
    # Filter links that likely contain venue information
    fee_keywords = ['register', 'registation']
    fee_links = [link for link in links if any(keyword in link.lower() for keyword in fee_keywords)]
    
    if not fee_links:
        return "No fee/registration page found."
    
    fee_url = urljoin(url, fee_links[0])  # Join relative URLs
    print(f"fee_url: {fee_url}")


    
    fee_finder = re.compile(r'\b(?:early[\W]|late|standard|onsite|on-site|main conference|regular|(eetn|non eetn"|epy|non-epy)\s(member))\b', re.IGNORECASE)

    # print(soup.find_all(['table'])[0].get_text())


    # tables =  [" ".join(p.stripped_strings) if re.findall(fee_finder,p.get_text()) else "" for p in soup.find_all(['table'])]
    tables =  [p if re.findall(fee_finder,p.get_text()) else None for p in soup.find_all(['table'])] 

    # print("tabels is " , tables)
    # print("len of soup.find_all(['table'])" , len(soup.find_all(['table'])))
    # # If there isn't tables do something else
    # if tables == [''] and len(tables) == 1:
    #     print("hiii")
    #     return " " 

    fees = []
    for t in tables:
        if t:
            fee = []
            print("\n\nNew table")
            for row in t.find_all('tr'): 

                row = [td.get_text(strip=True) for td in row.find_all(['td','th'])]
                # th = [td.get_text(strip=True) for td in row.find_all('th')]
                # if row is 
                print(row)
                if row:
                    fee.append(row) 
            fees.append(fee)
    
    # print(fees)

    # fees_tables = [string for string in tables]

    # [link for link in links if any(keyword in link.lower() for keyword in venue_keywords)]



    return ""

def main(url: str = "") -> None:
    if url == "":
        url = input("Enter the conference website URL: ")

    
    print(f"Current URL: {url}  <=========================================")
     

    # print("Conference Date :", get_conference_date(url) ) 

    print("Conference Name :", get_full_conference_name(url))  

    # print("Venue:" , find_conference_venue(url))
    
    
    # <=====================================================

    # html_content = get_conference_page(url)
    # print(html_content)
    # if vis_text:
    #     soup = BeautifulSoup(html_content, 'html.parser')
    #     text = soup.get_text()
        
    #     # Extract dates
    #     conference_dates = extract_dates(text)
    #     print("Extracted Dates:", conference_dates)

if __name__ == "__main__":

    # find_fees("https://ijcai24.org/register/")
    # find_fees("https://www.ecai2024.eu/registration")
    # find_fees("https://aaai.org/aaai-24-conference/registration/")

    # find_fees("https://setn2024.cs.unipi.gr/index.php/fees-registration-3/")

    

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

    extra_urls = [
        "https://2024.hci.international/",
        "https://isqua.org/events/istanbul-2024-international-conference.html",
        "https://2024.ieee-icra.org/"
    ]



    # for url in  test_urls:
    # # for url in extra_urls:
    # # for url in[
    # #     # "https://ijcai24.org/",
    # #     # "http://icaps24.icaps-conference.org/",
    # #     # "https://www.ecai2024.eu/",
    # #     # "https://aaai.org/aaai-24-conference/"
    # #     # "https://setn2024.cs.unipi.gr/"
    # #     # "https://pci2024.uniwa.gr/"
    # #     # "https://www.aamas2024-conference.auckland.ac.nz/"
    # #     # "https://kr.org/KR2024/"
    # #     # "https://sites.google.com/view/cpaior2024"
    # #     # "https://cp2024.a4cp.org/"
    # #     ]: 
    #     print(f"Url: {url}")
    #     # print("Venue:", get_venue_from_url(url))

    #     print( "Venue:" , find_conference_venue(url) )
    #     print(f"\n==================================\n")

    #     # break

   
    # main("https://isqua.org/events/istanbul-2024-international-conference.html")
    # main("https://2024.ieee-icra.org/")

#     print(extract_dates("""
    
# HCI International 2024 Conference homepage

#     Home
#     About
#     Submissions
#     Registration
#     Program
#     Accommodation
#     Exhibition

# HCI INTERNATIONAL 2024
# 26th International Conference on
# Human-Computer Interaction
# Washington Hilton Hotel, Washington DC, USA
# 29 June - 4 July 2024
# 40 years of HCI International. Join us in Washington DC to celebrate
# Photos

# Photos from the Conference
#  AWARDS

#     Papers/Poster
#     Student Design Competition
#     WUD: Design Challenge

# Stay connected

# Experience the Conference also through

# Web App

# Mobile App
# Program

# including detailed schedule for

#     paper presentations
#     poster presentations
#     tutorials
#     workshops

# Tours

# Explore the US Capital through an exclusive tour
# CMS

# Submissions and registration are handled through the Conference management System
# HCI MEDAL FOR SOCIETAL IMPACT

# Recipient: Vicki Hanson
# Medal to be awarded during the HCII2024 Opening Plenary Session
# KEYNOTE SPEECH

# "Technological Change for Improving Accessibility"

# by Vicki Hanson
# Participants attending the Conference ‘virtually’ are offered two complimentary TUTORIAL registrations

# (i) the Distinguished Tutorial T13 “Generative AI: With Great Power Comes Great Responsibility” offered by Ben Shneiderman

# (ii) any other Tutorial of their choice
# The HCI International (HCII) Conference celebrates the World Usability Day and congratulates the Design Challenge 2023 winners!

# November 9, 2023: On this special day, HCII reaffirms its commitment to prioritizing usability, promoting the creation of digital experiences that are beneficial and empowering for everyone. The HCII2024 sponsors the World Usability Initiative Design Challenge 2023 awards and cordially invites the award winners to receive their prizes and present their work during the conference.
# Thematic Areas & Affiliated Conferences

#     HCI: Human-Computer Interaction Thematic Area
#     HIMI: Human Interface and the Management of Information Thematic Area
#     EPCE: 21st International Conference on Engineering Psychology and Cognitive Ergonomics
#     AC: 18th International Conference on Augmented Cognition
#     UAHCI: 18th International Conference on Universal Access in Human-Computer Interaction
#     CCD: 16th International Conference on Cross-Cultural Design
#     SCSM: 16th International Conference on Social Computing and Social Media
#     VAMR: 16th International Conference on Virtual, Augmented and Mixed Reality
#     DHM: 15th International Conference on Digital Human Modeling & Applications in Health, Safety, Ergonomics & Risk Management
#     DUXU: 13th International Conference on Design, User Experience and Usability
#     C&C: 12th International Conference on Culture and Computing
#     DAPI: 12th International Conference on Distributed, Ambient and Pervasive Interactions

#     HCIBGO: 11th International Conference on HCI in Business, Government and Organizations
#     LCT: 11th International Conference on Learning and Collaboration Technologies
#     ITAP: 10th International Conference on Human Aspects of IT for the Aged Population
#     AIS: 6th International Conference on Adaptive Instructional Systems
#     HCI-CPT: 6th International Conference on HCI for Cybersecurity, Privacy and Trust
#     HCI-Games: 6th International Conference on HCI in Games
#     MobiTAS: 6th International Conference on HCI in Mobility, Transport and Automotive Systems
#     AI-HCI: 5th International Conference on Artificial Intelligence in HCI
#     MOBILE: 5th International Conference on Human-Centered Design, Operation and Evaluation of Mobile Communications

#     Call for Participation
#      Download(153KB)

#     PROCEEDINGS

#     Published by:

# About the Conference
# Google Scholar H5-Index: 38 (last update May 2024)

# HCI International 2024, jointly with the affiliated Conferences, under the auspices of 21 distinguished international boards, to be held under one management and one registration, will take place at Washington Hilton Hotel, Washington DC, USA.
# HCII2024 will run as a 'hybrid' conference.


# The best contributions will be awarded!
# The best paper of each of the HCII 2024 Thematic Areas / Affiliated Conferences will be given an award. The best poster extended abstract will also receive an award.
# World Usability Day - Design Challenge 2023

# HCI International 2024 congratulates the winners and sponsors the awards

#     1 July 2024: The Gold and Silver awards, as well as the Honorable Mention (in lieu of a Bronze award) will be conferred during the Opening Plenary Session
#     2 July 2024: The three awards winners are cordially invited, with complimentary registration, to present their work in a special hybrid session of the Conference


# If you have any requests or inquiries regarding accessibility issues, please contact the Conference Administration
# HCI INTERNATIONAL 2024

#     Contacts
#     Links
#     Privacy policy
#     Terms and Conditions

# HCII2024 CMS

#     Create your account
#     Submit proposals

# Contact us

#     Conference Administration
#     administration@2024.hci.international
#     Program Administration
#     program@2024.hci.international
#     Registration Administration
#     registration@2024.hci.international

#     Washington Hilton Hotel, Washington DC, USA
#     29 June - 4 July 2024

# SSL site seal - click to verify


#     """))

    # main("https://cp2024.a4cp.org/")

    for url in test_urls:
        main(url)
        print()
        # break
