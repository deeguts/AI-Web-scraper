import os
import time
from dotenv import load_dotenv
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from langchain_text_splitters import HTMLHeaderTextSplitter

# Load the .env file when this module is imported
load_dotenv()

def scrape_website(website, max_retries=3):
    """
    Scrapes the website using a remote Selenium browser via Bright Data,
    with built-in retry logic.
    """
    
    # --- ENVIRONMENT VARIABLE ---
    # Get the Bright Data URL from the environment variable (loaded by this file).
    # -----------------------------
    sbr_webdriver = os.environ.get("BRIGHT_DATA_URL")

    if not sbr_webdriver:
        print("Error: BRIGHT_DATA_URL environment variable not set.")
        raise ValueError("BRIGHT_DATA_URL is not set. Please set this in your .env file.")

    for attempt in range(1, max_retries + 1):
        driver = None
        try:
            print(f"Connecting to Scraping Browser (Attempt {attempt}/{max_retries})...")
            sbr_connection = ChromiumRemoteConnection(sbr_webdriver, "goog", "chrome")
            
            with Remote(sbr_connection, options=ChromeOptions()) as driver:
                print(f"Navigating to: {website}")
                driver.get(website)
                
                print("Waiting for CAPTCHA (if any)...")
                solve_res = driver.execute(
                    "executeCdpCommand",
                    {
                        "cmd": "Captcha.waitForSolve",
                        "params": {"detectTimeout": 10000},
                    },
                )
                print(f"CAPTCHA solve status: {solve_res['value']['status']}")
                
                print("Page loaded successfully. Scraping content...")
                html = driver.page_source
                return html # Success!

        except WebDriverException as e:
            print(f"WebDriverException on attempt {attempt}: {e.msg}")
            if "Internal Server Error" in e.msg and attempt < max_retries:
                print(f"Server error, retrying in {attempt * 2} seconds...")
                time.sleep(attempt * 2) # Exponential backoff
            else:
                raise e # Re-raise if not an internal server error or last attempt
        except Exception as e:
            print(f"An unexpected error occurred during scraping on attempt {attempt}: {e}")
            if attempt < max_retries:
                print(f"Retrying in {attempt * 2} seconds...")
                time.sleep(attempt * 2)
            else:
                raise e # Re-raise on last attempt
        finally:
            if driver:
                # --- THIS IS THE FIX ---
                # We wrap this in a try...except because the session
                # might already be closed by the proxy, causing a
                # harmless "Session not found" error. This prevents
                # it from crashing the whole app.
                try:
                    print("Closing the browser session.")
                    driver.quit()
                except Exception as e:
                    print(f"Non-critical error during browser quit (session likely already closed): {e}")
                # -------------------------

    print("Failed to scrape website after all retries.")
    return None

def extract_body_content(html_content):
    """
    Extracts the <body> tag content from the full HTML.
    """
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""


def clean_body_content(body_content):
    """
    Cleans the HTML body content by removing script, style, and other
    irrelevant tags, but PRESERVES the HTML structure for the LLM.
    """
    if not body_content:
        return ""
    soup = BeautifulSoup(body_content, "html.parser")

    # Remove irrelevant tags
    tags_to_remove = ["script", "style", "noscript", "svg", "img", "footer", "nav"]
    for tag in soup.find_all(tags_to_remove):
        tag.decompose()

    # Optional: Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, str) and "<!--" in text):
        comment.extract()
    
    # Remove attributes that are not useful for parsing
    for tag in soup.find_all(True):
        tag.attrs = {key: value for key, value in tag.attrs.items() if key in ['href', 'title']}

    return str(soup)


def split_html_content(html_content):
    """
    Splits the cleaned HTML content into semantic chunks based on headers.
    """
    if not html_content:
        return []

    # This splitter is good at grouping content under its nearest header
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
        ("h4", "Header 4"),
    ]

    html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    chunks = html_splitter.split_text(html_content)
    
    # Convert Document objects to simple strings
    string_chunks = [chunk.page_content for chunk in chunks]
    
    print(f"Split HTML into {len(string_chunks)} chunks for parallel processing.")
    return string_chunks

