from googleapiclient.discovery import build
import os


# Function to perform Google search using the API
def google_search(query, api_key, cse_id, num=10):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=query, cx=cse_id, num=num).execute()
    return res['items']


# Main function
if __name__ == "__main__":
    api_key = os.environ.get("GOOGLE_API_KEY")
    cse_id = os.environ.get("GOOGLE_CSE_ID")
    query = ""

    # Perform the search
    try:
        search_results = google_search(query, api_key, cse_id)

        # Print the results
        for result in search_results[:3]:
            print(f"From: {result['title']}")
            print(f"Link: {result['link']}")
            print(f"Snippet: {result['snippet']}\n")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("An error occurred, and no fallback method is available.")
