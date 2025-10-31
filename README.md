AI Web Scraper 🤖

This is a powerful data extraction tool that transforms any website into structured, queryable data using natural language. It's a "No-Code" solution that replaces complex scraper scripts and data management skills with a simple, human-readable prompt.

This project uses a Bright Data proxy to bypass blocks and CAPTCHAs, and then leverages a local Ollama model (llama3.1) to parse the clean HTML, turning unstructured content into clean JSON, tables, and downloadable reports.

(Remember to take a screenshot of your app, upload it to a site like Imgur, and paste the link here)

✨ Features

Intelligent Scraping: Uses a Bright Data proxy to handle dynamic JavaScript-heavy sites, solve CAPTCHAs, and automatically retry on errors.

AI-Powered Parsing: Leverages a local Ollama model to understand natural language prompts. You can ask for data just like you'd ask a person:

"Extract all hotel names, prices, and ratings."

"Get me a table of all product names and their prices from this page."

Structured Data Output: The AI returns clean JSON, which is instantly displayed in an interactive table.

Multiple Export Options: Download your extracted data with a single click as a .csv, .xlsx (Excel), or .pdf file.

Professional UI: A clean, modern, dark-mode interface built with Streamlit, complete with custom themes and styles.

🛠️ Tech Stack

Frontend: Streamlit

Backend: Python

Scraping: Selenium, Bright Data (Proxy)

AI / LLM: Ollama (running llama3.1), LangChain

Data Handling: Pandas, ReportLab (for PDF), openpyxl (for Excel)

🚀 How to Run This Project

1. Prerequisites

Python 3.10+

Ollama installed and running locally.

2. Setup & Installation

1. Clone the repository:

git clone [https://github.com/YOUR_USERNAME/AI-web-scraper.git](https://github.com/YOUR_USERNAME/AI-web-scraper.git)
cd AI-web-scraper


2. Install dependencies:

pip install -r requirements.txt


3. Set up your Environment:
Create a file named .env in the project root and add your Bright Data URL:

BRIGHT_DATA_URL="https"//brd-customer-xxxx:yyyy@brd.superproxy.io:9515"


4. Pull the AI model:

ollama pull llama3.1


3. Running the App

1. Start the AI Server:
In one terminal, start the Ollama server:

ollama serve


2. Run the Streamlit App:
In a second terminal, run the app:

streamlit run main.py


The app will open in your browser at http://localhost:8501.

How to Use

Enter a URL from a website you want to scrape (e.g., an Amazon search page, MakeMyTrip, or quotes.toscrape.com).

Click "Scrape Website" and wait for the success message.

Enter a prompt describing the data you want (e.g., "Get all quotes and their authors").

Click "Parse Content" and wait for the AI to analyze the data.

View your data in the table and use the download buttons to get your report.