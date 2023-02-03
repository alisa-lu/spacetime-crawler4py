from calendar import c
import re
from urllib.parse import urlparse, urldefrag, urljoin
from bs4 import BeautifulSoup

# Global variables to produce report
visited_links = set()
max_words_in_a_page = 0
page_with_max_words = ""
unique_word_frequencies = {} # key: unique word -> value: word frequency across all pages found
ics_subdomain_page_frequencies = {} # key: subdomain url -> value: set of unique pages in the subdomain

content_of_five_most_recent_pages = []
# the ith item in the list is a list of non-stop word tokens
# found in (i + 1)th most recent page crawled


def tokenize(text:str) -> list:
    """
    Tokenizes the given text into a list of **non-unique** tokens.
    This is copy pasted from Alisa's assignment 1.
    """
    tokens = []

    for line in text.split('\n'):
        alnumword = ''
        for c in line:
            # if the character is alphanumeric, we add it to the current word
            if bool(re.match('^[a-zA-Z0-9]+$', c)):
                alnumword += c.lower()
            
            # if the character isn't alphanumeric, we've reached the end of the current alnum word
            # so, we will add the word to words_to_add and then reset it so we can collect more words
            # or, if there is no current alnum word (it's empty), then we keep going
            else:
                if alnumword != '':
                    tokens.append(alnumword)
                    alnumword = ''
        
        # after we've processed all the characters in the line, make sure that we add any remaining word stored in alnumword
        # for when the last char in a line is alphanumeric and the above else statement is not executed
        if alnumword != '':
            tokens.append(alnumword)

    return tokens

def remove_stop_words(tokens: list) -> list:
    """
    Return list of tokens excluding stop words.
    """
    stop_words = {'ours', 'd', 'hasn', 'don', 'being', 'who', 'wouldn', 'a',
    'would', 'was', 'i', 'having', 'above', 'm', 'against', 'to', 'doing',
    'his', 'for', 'if', 'our', 'been', 'an', 'such', 'between', 'in', 'out',
    'should', 'haven', 'own', 'some', 'few', 'and', 'how', 'himself', 'up', 'under',
    'me', 'were', 'after', 'over', 'at', 'is', 'could', 'wasn', 'before',
    'themselves', 'be', 'itself', 'most', 'all', 'hers', 'yourselves', 'can',
    'these', 'they', 't', 'it', 'had', 'them', 'do', 'here', 'cannot', 'of',
    'you', 'because', 'mustn', 're', 'same', 'didn', 'from', 'more', 'your',
    'once', 'ought', 'yourself', 'hadn', 's', 'there', 'only', 'my', 'does',
    'ourselves', 'this', 'about', 'both', 'what', 'has', 'off', 'he', 'myself',
    'theirs', 'the', 'through', 'have', 'where', 'other', 'not', 'why', 'with',
    'won', 'as', 'below', 'll', 'any', 'whom', 'each', 'him', 'nor', 'we', 'did',
    'or', 'shouldn', 'herself', 'until', 'yours', 'she', 'that', 'are', 'those',
    'into', 'shan', 'during', 'too', 'than', 'further', 'when', 'no', 'by', 'then',
    'again', 'aren', 'down', 'her', 'which', 'let', 'on', 'am', 'but', 'isn',
    'doesn', 've', 'while', 'so', 'their', 'its', 'weren', 'couldn', 'very'}
    
    return [token for token in tokens if token not in stop_words]


def computeWordFrequencies(tokens: list, url) -> dict:
    """
    Takes a list of tokens and adds it into the global dictionary storing token frequencies.
    It also writes into a file that tracks all the token dictionaries for individual URLs for reference.
    Returns the dictionary containing the token dictionaries of the URL.
    """
    global unique_word_frequencies
    tokens = remove_stop_words(tokens)

    word_freq = {} # stores the frequencies of tokens found in this url in a local dict
    for item in tokens:
        # add item to unique_word_frequencies
        if item not in unique_word_frequencies:
            unique_word_frequencies[item] = 1
        else:
            unique_word_frequencies[item] += 1

        # add item to dictionary storing just this value
        if item not in word_freq:
            word_freq[item] = 1
        else:
            word_freq[item] += 1

    return word_freq

def write_url_word_frequencies_to_file(word_freq: dict, url: str) -> None:
    """ 
    Stores the url-specific dictionary in a file to keep track
    """
    f = open("track_dictionary.txt", "a")
    f.write(str(url) + " -> "+str(len(word_freq)))
    f.write("\n<-------------->\n") # separator for the file for different URLs
    f.close()

def write_global_word_frequencies_to_file(Frequencies: dict) -> None:
    """
    Stores the global dictionary of token frequencies across all pages found in a file.
    """
    f = open("unique_word_frequencies.txt", "w")
    f.write("we found "+str(len(visited_links))+" URLs")
    f.write('\n')
    for k, v in sorted(Frequencies.items(), key=lambda x: (-x[1], x[0])):
        f.write(k + " -> " + str(v))
        f.write('\n')
    f.close()

def write_unique_links_to_text_file(url: str) -> None:
    """
    Stores the current url in a file to keep track of all unique links found.
    """
    f = open("links.txt", "a")
    f.write(str(url))
    f.write("\n<-------------->\n")
    f.close()

def max_words(tokens:list, resp):
    global max_words_in_a_page
    global page_with_max_words

    # Determine the number of words in the page    
    page_num_of_words = len(tokens)

    # Checks if this is greater than the currently stored longest page
    if page_num_of_words > max_words_in_a_page:
        max_words_in_a_page = page_num_of_words
        page_with_max_words = urldefrag(resp.url)

    # Update file storing the longest page in terms of the number of words
    f = open("longest_page.txt", "w")
    f.write(f"Longest page: {page_with_max_words}\nNumber of words in page: {max_words_in_a_page}\n")
    f.close()

def ics_subdomains(resp):
    global ics_subdomain_page_frequencies

    # Determine if page is in a subdomain of ics.uci.edu
    if (re.match(r".*\.ics\.uci\.edu", urlparse(resp.url).netloc) != None):
        # Extract subdomain
        # subdomain = (urlparse(resp.url).netloc).split(".")[0] # change this
        subdomain_url = urlparse(resp.url).netloc
        
        # Add subdomain url key to dict with value being a set of its pages
        if subdomain_url not in ics_subdomain_page_frequencies:
            ics_subdomain_page_frequencies[subdomain_url] = set([urldefrag(resp.url).url])
        else:
            ics_subdomain_page_frequencies[subdomain_url].add(urldefrag(resp.url).url)

    # Update file storing the subdomains of ics.uci.edu
    f = open("subdomains.txt", "w")
    for k, v in sorted(ics_subdomain_page_frequencies.items()):
        f.write(k + " -> " + str(v)+"\nThis subdomain has "+str(len(v))+" unique pages.")
        f.write('\n')
    f.close()

def scraper(url, resp) -> list:
    """
    Return a list of **valid** links found in the current url.
    """
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp) -> list:
    """
    Returns list of links found in the current url.
    """
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    global unique_word_frequencies
    global visited_links
    global content_of_five_most_recent_pages

    # If we've already visited the URL, return an empty list
    if url in visited_links or resp.url in visited_links or urldefrag(resp.url).url in visited_links:
        return []

    # adds link to global visited_links set
    visited_links.add(urldefrag(resp.url).url)
    write_unique_links_to_text_file(urldefrag(resp.url).url)

    # If there is an error or no content at the current link, return empty list
    if resp.status != 200 or resp.raw_response.content == None or resp.raw_response.content == "":
        return []

    # Get the anchor tags found in the content of the current link
    soup = BeautifulSoup(resp.raw_response.content, 'lxml')
    discovered_a_tags = soup.find_all('a')
    extracted_links = []

    for tag in discovered_a_tags:
        try:
            # Append the href links found in the anchor tags to extracted links list
            link = urldefrag(tag['href']).url
            if link.startswith('/'):
                # print("this is a relative url", link)
                # print("base url: ", urldefrag(resp.url).url)
                link = urljoin(urldefrag(resp.url).url, link)
                # print("we found the absolute url", link)
                # print('\n')

            # if the link is a swiki link, we do not want to find the queries
            if link.startswith('https://swiki.ics.uci.edu') or link.startswith('https://wiki.ics.uci.edu'):
                link = urljoin(link, urlparse(link).path)
            extracted_links.append(link)
            
        except KeyError:
            # If the a tag doesn't have an href, continue
            pass

    # Tokenizes the content of the page
    page_text_content = soup.get_text()
    tokens = tokenize(page_text_content)

    # Compare tokenized page to 5 most recently crawled pages, removes page if it is an exact or near match of a previous chained page
    if len(content_of_five_most_recent_pages) > 0:
        for page_tokens in content_of_five_most_recent_pages:
            if tokens == page_tokens:
                # Current page is an exact match to a previously crawled page;
                # skip crawling this page
                return []

            elif len(set(tokens)) != 0 and len(set(page_tokens)) != 0 and \
                (len(set(tokens).intersection(set(page_tokens))) / len(set(tokens))) >= 0.85\
                and (len(set(tokens).intersection(set(page_tokens))) / len(set(page_tokens))) >= 0.85:
                # Current page is a near match to a previously crawled page
                # skip crawling this page
                return []
            
    # Add tokens of current page to content_of_five_most_recent_pages
    if len(content_of_five_most_recent_pages) == 5:
        content_of_five_most_recent_pages.pop(0)
    content_of_five_most_recent_pages.append(tokens)

    # Adds the tokens to the dictionary storing unique words (part 3 of the report)
    url_token_dict = computeWordFrequencies(tokens, urldefrag(resp.url).url)
    write_url_word_frequencies_to_file(url_token_dict, urldefrag(resp.url).url)
    write_global_word_frequencies_to_file(unique_word_frequencies)

    # Calculates if this page contains the max # of words in a page or not (part 2 of the report)
    max_words(tokens, resp)
    
    # Calculates if this page is an subdomain of ICS, and if so, updates the file and global dictionary (part 4 of the report)
    ics_subdomains(resp)

    return extracted_links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    # we do not want any empty URLs to be crawled.
    if url == '':
        return False

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            # print(str(url), "is_valid: not https or http")
            return False

        if not re.match(r"(.*\.ics\.uci\.edu)|(.*\.cs\.uci\.edu)|(.*\.informatics.uci.edu)|(.*\.stat.uci.edu)",
        parsed.netloc):
            # print(str(url), parsed.netloc, "is_valid: not in the domain we want")
            # url does not have one of the domains specified below:
            # *.ics.uci.edu/*
            # *.cs.uci.edu/*
            # *.informatics.uci.edu/*
            # *.stat.uci.edu/*
            return False

        #TODO: reject low information pages
        # Detect and avoid crawling very large files, especially if they have low information value

        # we do not want to crawl PDFs
        if re.match(r".*\/pdf.*", parsed.path.lower()) or url.endswith(".pdf"):
            return False

        # we do not want to crawl zip files
        if re.match(r".*\/zip.*", parsed.path.lower()) or url.endswith(".zip"):
            return False

        # if it is a login page, it is low information.
        if re.search("login", url):
            return False

        # if it is a calendar site, it is low information.
        if re.search("\?ical", url):
            return False
        
        # we don't want to crawl elms.ics.uci.edu because they are all low information and barred by a login.
        if url.startswith("http://elms.ics.uci.edu"):
            return False

        # we don't want to crawl download sites
        if re.search("\?action=download", url):
            return False

        # we do not want to crawl the social media sharing pages
        if re.search("\?share=", url):
            return False

        # Do not crawl calendar (potential trap) on WICS website
        if parsed.netloc == "wics.ics.uci.edu" and parsed.path.startswith("/events"):
            return False

        # Do not crawl this subdomain; it requires authentication making it low information
        if re.search("grape.ics.uci.edu", url):
            return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
