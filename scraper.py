from calendar import c
import re
from urllib.parse import urlparse, urldefrag
from bs4 import BeautifulSoup

# Global variables to produce report
visited_links = set()
max_words_in_a_page = 0
page_with_max_words = ""
unique_word_frequencies = {} # key: unique word -> value: word frequency across all pages found
ics_subdomain_page_frequencies = {} # key: subdomain -> value: set of unique pages in the subdomain


def tokenize(text):
    """
    tokenizes the text into a list of tokens
    """
    res = []

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
                    res.append(alnumword)
                    alnumword = ''
        
        # make sure that we add the alnum word as well
        if alnumword != '':
            res.append(alnumword)

    return res

def computeWordFrequencies(Token:list, url):
    """
    This function takes a list of tokens and adds it into the global dictionary storing token frequencies.
    It also writes into a file that tracks all the token dictionaries for reference.
    """
    global unique_word_frequencies
    stop_words = {'ours', 'd', 'hasn', 'don', 'being', 'who', 'wouldn', 'a', 'would', 'was', 'i', 'having', 'above', 'm', 'against', 'to', 'doing', 'his', 'for', 'if', 'our', 'been', 'an', 'such', 'between', 'in', 'out', 'should', 'haven', 'own', 'some', 'few', 'and', 'how', 'himself', 'up', 'under', 'me', 'were', 'after', 'over', 'at', 'is', 'could', 'wasn', 'before', 'themselves', 'be', 'itself', 'most', 'all', 'hers', 'yourselves', 'can', 'these', 'they', 't', 'it', 'had', 'them', 'do', 'here', 'cannot', 'of', 'you', 'because', 'mustn', 're', 'same', 'didn', 'from', 'more', 'your', 'once', 'ought', 'yourself', 'hadn', 's', 'there', 'only', 'my', 'does', 'ourselves', 'this', 'about', 'both', 'what', 'has', 'off', 'he', 'myself', 'theirs', 'the', 'through', 'have', 'where', 'other', 'not', 'why', 'with', 'won', 'as', 'below', 'll', 'any', 'whom', 'each', 'him', 'nor', 'we', 'did', 'or', 'shouldn', 'herself', 'until', 'yours', 'she', 'that', 'are', 'those', 'into', 'shan', 'during', 'too', 'than', 'further', 'when', 'no', 'by', 'then', 'again', 'aren', 'down', 'her', 'which', 'let', 'on', 'am', 'but', 'isn', 'doesn', 've', 'while', 'so', 'their', 'its', 'weren', 'couldn', 'very'}
    d = {} # stores the tokens for this url
    for item in Token:
        if item not in stop_words:
            # add item to unique_word_frequencies
            if item not in unique_word_frequencies.keys():
                unique_word_frequencies[item] = 1
            else:
                unique_word_frequencies[item] += 1

            #add item to dictionary storing just this value
            if item not in d.keys():
                d[item] = 1
            else:
                d[item] += 1
    
    # store the url-specific dictionary in a file to keep track
    f = open("track_dictionary.txt", "a")
    f.write(str(url))
    f.write('\n')
    f.write(str(d))
    f.write("\n,,,,,,,,,\n")

    # store the global dictionary into a file
    write_frequencies_to_file(unique_word_frequencies)

def write_frequencies_to_file(Frequencies:dict)->None:
    """
    This function stores the global dictionary in a file.
    """
    f = open("unique_word_frequencies.txt", "w")
    for k, v in sorted(Frequencies.items(), key=lambda x: (-x[1], x[0])):
        f.write(k + " -> " + str(v))

def find_intersection(dict1, dict2):
    intersection = set()

    for key in dict1.keys():
        if key in dict1.keys() and key in dict2.keys() and dict1[key] >= 1 and dict2[key] >= 1:
            intersection.add(key)
            dict1[key] -= 1
            dict2[key] -= 1

    return len(intersection)

def unique_links_to_text_file(url):
    f = open("links.txt", "a")
    f.write(str(url))
    f.write("\n,,,,,,,,,\n")

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    global max_words_in_a_page
    global page_with_max_words
    global ics_subdomain_page_frequencies

    if url in visited_links or resp.url in visited_links:
        # if we've already visited the URL, we return an empty list
        return []

    visited_links.add(urldefrag(resp.url))
    unique_links_to_text_file(urldefrag(resp.url)[0])

    if resp.status != 200 or resp.raw_response.content == None:
        return []

    soup = BeautifulSoup(resp.raw_response.content, 'lxml')
    extracted_links = soup.find_all('a')
    extracted_links = [urldefrag(link['href']).url for link in extracted_links]

    # Tokenizes the content of the page
    page_text_content = soup.get_text()
    tokens = tokenize(page_text_content)

    # Adds the tokens to the dictionary storing unique words (part 3 of the report)
    computeWordFrequencies(tokens, urldefrag(resp.url)[0])

    # Determine the number of words in the page
    page_num_of_words = len(tokens)

    if page_num_of_words > max_words_in_a_page:
        max_words_in_a_page = page_num_of_words
        page_with_max_words = urldefrag(resp.url)

    # Update file storing the longest page in terms of the number of words
    f = open("longest_page.txt", "w")
    f.write(f"Longest page: {page_with_max_words}\nNumber of words in page: {max_words_in_a_page}\n")
    f.close()
    
    # Determine if page is in a subdomain of ics.uci.edu
    if (re.match(r"ics\.uci\.edu", urlparse(resp.url).netloc) != None):
        # Extract subdomain
        subdomain = (urlparse(resp.url).netloc).split(".")[0]
        if subdomain in ics_subdomain_page_frequencies:
            ics_subdomain_page_frequencies[subdomain] = set([urldefrag(resp.url)])
        else:
            ics_subdomain_page_frequencies[subdomain].add(urldefrag(resp.url))

    # Update file storing the subdomains of ics.uci.edu
    f = open("subdomains.txt", "w")
    f.write(str(ics_subdomain_page_frequencies))
    f.close()

    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    return extracted_links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    if url == '':
        return False

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not re.match(r"ics\.uci\.edu | cs\.uci\.edu | informatics\.uci\.edu | stat\.uci\.edu",
        parsed.netloc):
            # url does not have one of the domains speciified below:
            # *.ics.uci.edu/*
            # *.cs.uci.edu/*
            # *.informatics.uci.edu/*
            # *.stat.uci.edu/*
            return False

        #TODO: reject low information pages
        # Detect and avoid infinite traps
        # Detect and avoid sets of similar pages with no information
        # Detect and avoid dead URLs that return a 200 status but no data (click here to see what the different HTTP status codes mean Links to an external site.)
        # Detect and avoid crawling very large files, especially if they have low information value
        
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
