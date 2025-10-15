from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, add_messages
import random
import uuid
import json
import os
from typing import List, TypedDict, Annotated
import re
import json


# Define AgentState using TypedDict
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# Generate fake hotel data
def generate_fake_hotels(num_hotels=1000):
    cities = ["New York", "Paris", "Tokyo", "London", "Dubai"]
    amenities_list = ["pool", "wifi", "gym", "spa", "parking"]
    hotels = []
    for _ in range(num_hotels):
        hotel = {
            "id": str(uuid.uuid4()),
            "name": f"Hotel {random.randint(1, 1000)}",
            "city": random.choice(cities),
            "price_per_night": random.randint(50, 500),
            "amenities": random.sample(amenities_list, k=random.randint(1, 5))
        }
        hotels.append(hotel)
    return hotels


# Load or create FAISS vector store
def load_or_create_vectorstore(hotels_file="hotels.json", index_file="hotel_index.faiss"):
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    if os.path.exists(index_file) and os.path.exists(hotels_file):
        print("Loading existing vector store...")
        vectorstore = FAISS.load_local(index_file, embedding_model, allow_dangerous_deserialization=True)
        with open(hotels_file, "r") as f:
            hotels = json.load(f)
        return vectorstore, hotels

    print("Creating new vector store...")
    hotels = generate_fake_hotels()
    texts = [
        f"{h['name']} in {h['city']} with price ${h['price_per_night']} per night, amenities: {', '.join(h['amenities'])}"
        for h in hotels
    ]
    metadatas = [
        {"id": h["id"], "city": h["city"], "price_per_night": h["price_per_night"], "amenities": h["amenities"]} for h
        in hotels]
    vectorstore = FAISS.from_texts(texts, embedding_model, metadatas=metadatas)

    vectorstore.save_local(index_file)
    with open(hotels_file, "w") as f:
        json.dump(hotels, f)

    return vectorstore, hotels


# Initialize Mistral LLM
llm = ChatOllama(model="mistral", temperature=0)

# Prompt for extracting city, price range, and amenities
extract_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a hotel recommendation assistant. Extract the following from the conversation history and latest input:
    - city: Must be one of New York, Los Angeles, Seattle, Las Vegas.
    - cuisine: A comma-separated list like Asian, American, Italian , output as ["Asian", "American" ,"Italian"].

    Output *only* valid JSON with this exact structure:

    {{
      "city": "<city or null>",
      "cuisine": ["cuisine1", "cuisine2"] or null,
      "response": "<message to user>"
    }}

    Rules:
    - Output JSON only, no additional text, whitespace, or explanations.
    - If the input contains a city not in [New York, Los Angeles, Seattle, Las Vegas], set "city" to null and "response" to "City not supported. Supported cities are New York, Los Angeles, Seattle, Las Vegas." 
    - If all fields (city, cuisines) are present, set "response" to "Ready to search".
    - If any field is missing, set "response" to a polite request for the missing information in this order: city, cuisine.
    - For cuisine, parse inputs like "Asian, American" or "Asian,American" into ["Asian", "American"].
    - If input is unclear, set "response" to a clarification request for the missing field.
    Examples:
    - Input: "Restaurant in New York", History: "", Output: {{"city": "New York", "cuisine": null, "response": "Please provide cuisine details (e.g., American , Asian , Italian)."}}
    - Input: "American", History: "human: Restaurant in New York", Output: {{"city": "New York", "cuisine": ["American"],"response": "Ready to search"}}
    History: {history}
    Latest input: {input}"""),
    ("user", "{input}")
])

# Prompt for formatting search results
result_prompt = ChatPromptTemplate.from_messages([
    ("system", """Format the restaurant search results into a user-friendly response. If no restaurants are found, return: "No restaurants found matching your criteria." 
    Results: {results}
    For each restaurants, format as: "<name> in <city>: Cuisine: <cuisine>" """),
    ("user", "Format the results")
])


# Node to process user input with Mistral LLM
def process_input(state: List[HumanMessage | AIMessage]) -> List[HumanMessage | AIMessage]:
    history = "\n".join([f"{msg.type}: {msg.content}" for msg in state])
    latest_input = state[-1].content if state else ""

    chain = extract_prompt | llm
    try:
        result = chain.invoke({"history": history, "input": latest_input})
        print(f"Raw LLM output: {result.content}")  # Debugging
        extracted = json.loads(result.content.strip())  # Strip whitespace
        if not all(key in extracted for key in ["city", "cuisine", "response"]):
            raise ValueError("Missing required JSON keys")
    except Exception as e:
        print(f"Error parsing LLM output: {e}")  # Debugging
        return state + [AIMessage(
            content=f"Sorry, I couldn't process your request due to an error: {str(e)}. Please try again with a clear format (e.g., 'Hotel in Paris', '$100-$200', 'pool, wifi').")]

    response = extracted["response"]
    if response == "Ready to search":
        search_params = {
            "city": extracted["city"],
            "cuisine": extracted["cuisine"],
        }
        return state + [AIMessage(content=f"Search: {json.dumps(search_params)}")]

    return state + [AIMessage(content=response)]


# Node to search hotels
def search_hotels(state: List[HumanMessage | AIMessage]) -> List[HumanMessage | AIMessage]:
    last_message = state[-1].content
    if not last_message.startswith("Search:"):
        return state

    try:
        params = json.loads(last_message.replace("Search: ", ""))
        city = params["city"]
        cuisine = params["cuisine"]
    except:
        return state + [AIMessage(content="Error processing search parameters.")]

    query = f"Restaurant in {city} with cuisines {cuisine}"
    print(f"Search query: {query}")
    results = vectorstore.similarity_search_with_score(query, k=5)

    filtered_hotels = [
        doc.metadata for doc, score in results
        if doc.metadata["city"] == city
           and all(cuisine in doc.metadata["cuisines"] for cuisine in cuisine)
    ]

    chain = result_prompt | llm
    result = chain.invoke({"results": filtered_hotels})

    return state + [AIMessage(content=result.content)]


# Initialize or load vector store
vectorstore, hotels = load_or_create_vectorstore()

# Define LangGraph workflow
workflow = StateGraph(List[HumanMessage | AIMessage])
workflow.add_node("process_input", process_input)
workflow.add_node("search_hotels", search_hotels)
workflow.add_edge("process_input", "search_hotels")
workflow.add_edge("search_hotels", END)
workflow.set_entry_point("process_input")
app = workflow.compile()


# Function to run the agent
def run_hotel_agent(user_input: str, state: List[HumanMessage | AIMessage] = None):
    if state is None:
        state = [HumanMessage(content=user_input)]
    else:
        state = state + [HumanMessage(content=user_input)]

    return app.invoke(state)


# Interactive session
def interactive_session():
    state = None
    print("Restaurant recommender AI Agent: Enter your query (e.g., 'Italian restaurant in New york') or 'exit' to quit.")

    while True:
        user_input = input("> ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        state = run_hotel_agent(user_input, state)
        print(state[-1].content)

        if state[-1].content.startswith("No restauranta found") or not state[-1].content.startswith("Please"):
            state = None


if __name__ == "__main__":
    interactive_session()
