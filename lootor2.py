
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import re
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults



# Initialize ChatGroq
chat = ChatGroq(
    temperature=0,
    model="mixtral-8x7b-32768",
    api_key="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" # Optional if not set as an environment variable
)

# Define the system prompt


# app = FastAPI()

# @app.get("/generate_query")
# def generate_query(user_query: str):
#     # Create a prompt and generate a response
#     prompt = ChatPromptTemplate.from_messages([("system", system), ("human", user_query)])
#     chain = prompt | chat
#     generated_query = chain.invoke({"text": {user_query}})
    
#     # Create a JSON response
#     response = {
#         "generated_query": generated_query.content
#     }
    
#     return response

# To run the application, use the command below:
# uvicorn your_script_name:app --reload





app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat = ChatGroq(
    temperature=0,
    model="mixtral-8x7b-32768",
    api_key="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"
)




#for genrating questions
@app.get("/generate_query")
def generate_query(user_query: str):
    system = """
As an expert shopping assistant, Lootor, developed by Kavish Shah and Dhruv in India, your role is to assist users in finding the perfect product by asking clarifying questions based on their initial query. Here are the guidelines to follow:

### Instructions:

1. Begin by asking questions related to the user's initial query to help narrow down their options. Provide 4 relevant and diverse options for each question, and the last option/4th option will be "Any".
2. Always be polite, engaging, and informative in your responses.
3. If you are unable to provide a satisfactory answer, kindly ask the user if they would like to provide more information or rephrase their query.
4. Your goal is to understand the user's needs and preferences, making the shopping experience as enjoyable and efficient as possible.

### Context:

The user has requested assistance in finding a specific product. As Lootor, you will ask a series of questions to better understand their needs and provide tailored recommendations.

Example interaction:
---
Hello! I'm Lootor, your helpful shopping assistant from India. I'd be delighted to assist you in finding the perfect product. To help narrow down the options, may I ask:

1. Which category does the product you're looking for fall under? You can choose between (technology), (fashion), (home decor), (kitchen appliances), or (Any).
2. Do you prefer a particular brand or would you like to explore multiple options? You can select from (Apple), (Zara), (IKEA), (Prestige), or (Any).
3. Is there a specific price range you have in mind? You can choose between (₹500-₹2000), (₹2000-₹5000), (₹5000-₹10000), or (Any).
4. Are you looking for a product with specific features (e.g., smart technology, sustainable materials, customizable options)? If so, please specify.
5. Would you like a new or a refurbished product? You can choose between (new), (refurbished), or (Any).

Once I have this information, I can provide a more tailored and accurate product recommendation for you. Looking forward to your answers!
---
"""
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", user_query)])
    chain = prompt | chat
    generated_query = chain.invoke({"text": {user_query}})
    
    response2 = {
        "generated_questions": generated_query.content
    }
    
    return response2






#for making shopping query

@app.get("/search")
def search(user_query: str):
    # API keys
    tavily_api_keys = ["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","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"]
    groq_api_keys = [
        "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",
        "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"
    ]
    def api_call_with_retry(func, api_keys, *args, **kwargs):
     for api_key in api_keys:
        try:
            return func(api_key, *args, **kwargs)
        except Exception as e:
            print(f"Error with API key {api_key}: {e}")
     raise Exception("All API keys failed.")

    # Generate query for product search
    def generate_shopping_query(api_key, user_query):
        system = """
        As an expert AI assistant, you are responsible for creating a precise and meaningful shopping query based on a user's selected preferences. The preferences are provided in a structured format, contained within the variable "selection", which is dynamically updated for each new user. Your primary goal is to parse this variable and extract the user's chosen options for each category, in order to generate a clear and concise shopping query tailored to their preferences. When formulating the shopping query, ensure it is both realistic and suitable for use in internet search engines. To achieve this, follow these steps:
        Parse the "selection" variable to identify user preferences.
        Extract the chosen options for each category.
        Formulate Shopping Query: Utilize the extracted preferences to generate a shopping query.
        Ensure the query is straightforward, simple, and unambiguous.
        Enclose the final shopping query within < >, as it will be directly integrated into search queries on the internet.
        Example: < Women's black running shoes size 8 with excellent arch support >
        """
        
        prompt = ChatPromptTemplate.from_messages([("system", system), ("human", user_query)])
        chat = ChatGroq(temperature=0, model="llama-3.1-70b-versatile", api_key=api_key)
        chain = prompt | chat
        generated_query = chain.invoke({"text": user_query})
        return " ".join(re.findall(r'<(.*?)>', generated_query.content))

    shopping_query = api_call_with_retry(generate_shopping_query, groq_api_keys, user_query)

    # Tavily search
    def tavily_search(api_key, question):
        os.environ["TAVILY_API_KEY"] = api_key
        tool = TavilySearchResults(max_results=20, search_depth="advanced")
        return tool.invoke({"query": question})

    question = f'{shopping_query} in india'
    tavily_data = api_call_with_retry(tavily_search, tavily_api_keys, question)

    # ChatGroq processing
    prompt_template = PromptTemplate(
        input_variables=["reference_table", "draft_table"],
        template="""
        Data:
        {reference_table}

        you are indian ai shopping assistant As a seasoned online shopping expert, with over 15 years of experience in curating the most exceptional products and deals on the internet, your task is to provide a personalized and comprehensive shopping experience for the user's query {draft_table}.
        NOTE:Determine the number of products to suggest based on the product category.

        Product Search and Recommendations
        Search for the top products related to {draft_table} across various online.
        Provide a list of the top recommended products, ranked based on their features, value, and user reviews.
        Enclose each product's name  within angle brackets < >.
        genrate 2-3 line of product's quick introduction and Enclose in  within [] .

        Product Reviews Summary
        Generate a summary of the reviews for each product without mentioning product name, highlighting the key aspects such as pros, cons, and user satisfaction. Present the review summary for each product within curly braces ~  ~.

        Buying Guide Creation
        Develop a comprehensive buying guide for the product category, including essential factors to consider, tips for finding the best deals, and common pitfalls to avoid. Encase the buying guide within round brackets ().

        Final Recommendation
        Based on your expert analysis, recommend the first product from the list and justify why it stands out from the competition. Highlight its advantages in double round brackets |  |.

        Final Output Structure

        List of products in < >.

        product's brief introduction/description in within []

        Review summary for each product within ~ ~.

        A detailed buying guide within ( ).

        Recommended product and its advantages in |  |.

        Take a moment to collect your thoughts, and proceed systematically, step-by-step.

        NOTE: Do Not Write Product Name with < > in Product Reviews Summary,Buying Guide Creation.
        NOTE:Give final list of the top 10 products, ranked in order of preference

        """
    )

    prompt = prompt_template.format(reference_table=tavily_data, draft_table=shopping_query)

    def process_chat(api_key, prompt):
        chat = ChatGroq(temperature=0, model="llama-3.1-70b-versatile", api_key=api_key)
        return chat.invoke(prompt)

    def extract_content(text, start_char, end_char):
        return re.findall(f'\{start_char}(.*?)\{end_char}', text, re.DOTALL)

    try:
        response = api_call_with_retry(process_chat, groq_api_keys, prompt)
        response_content = response.content

        products = list(dict.fromkeys(extract_content(response_content, '<', '>')))
        introductions = extract_content(response_content, '[', ']')
        reviews = extract_content(response_content, '~', '~')
        buying_guide = extract_content(response_content, '(', ')')
        recommendation = extract_content(response_content, '|', '|')

        json_response = {
            "products": products,
            "introductions": introductions,
            "reviews": reviews,
            "buying_guide": buying_guide,
            "recommendation": recommendation
        }

    except Exception as e:
        print(f"Failed to get response: {e}")
        return None

    # Selenium part
    def create_driver():
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        return webdriver.Chrome(options=options)

    def safe_find_element(driver, selector, by=By.CSS_SELECTOR, timeout=10):
        try:
            return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
        except (NoSuchElementException, TimeoutException):
            return None

    def fetch_data(driver, query):
        url = f"https://www.google.com/search?tbm=shop&hl=en&psb=1&ved=0CAAQvOkFahcKEwjQobuuw56FAxUAAAAAHQAAAAAQHw&q={query}"
        driver.get(url)

        elements = {
            'image': ('div.ArOc1c img', By.CSS_SELECTOR),
            'price': ("a8Pemb.OFFNJ", By.CLASS_NAME),
            'marketplace_name': ("aULzUe.IuHnof", By.CLASS_NAME),
            'rating': ("Rsc7Yb", By.CLASS_NAME),
            'first_link': ("a.shntl", By.CSS_SELECTOR),
            'text_content': ("tAxDx", By.CLASS_NAME)
        }

        data = {}
        for key, (selector, by) in elements.items():
            element = safe_find_element(driver, selector, by, timeout=5)
            if element:
                data[key] = element.get_attribute('src') if key == 'image' else element.get_attribute('href') if key == 'first_link' else element.text
            else:
                data[key] = f"No {key.replace('_', ' ')} found"

        return data

    def fetch_all_data(products, max_retries=3, retry_delay=1):
        driver = create_driver()
        results = {}
        try:
            for query in products:
                for attempt in range(max_retries):
                    try:
                        results[query] = fetch_data(driver, query)
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
        finally:
            driver.quit()
        return results

    scraped_data = fetch_all_data(products)

    combined_json_response = {
        "langchain_response": json_response,
        "scraped_data": scraped_data
    }

    return combined_json_response 

# Add this block to run the server automatically
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)