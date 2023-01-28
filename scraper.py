import re
from urllib.parse import urlparse, urldefrag
from bs4 import BeautifulSoup

def tokenize(text):
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

def computeWordFrequencies(Token:list)->dict:
    d = {}
    for item in Token:
        if item not in d.keys():
            d[item] = 1
        else:
            d[item] += 1
    return d

def print_frequencies(Frequencies:dict)->None:
    for k, v in sorted(Frequencies.items(), key=lambda x: (-x[1], x[0])):
        print(k + " -> " + str(v))

def find_intersection(dict1, dict2):
    intersection = set()

    for key in dict1.keys():
        if key in dict1.keys() and key in dict2.keys() and dict1[key] >= 1 and dict2[key] >= 1:
            intersection.add(key)
            dict1[key] -= 1
            dict2[key] -= 1

    return len(intersection)

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    return list()

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
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
