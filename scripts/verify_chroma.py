import chromadb
import sys

# This script runs on your LOCAL machine, not in Docker.
# It connects to the ChromaDB port you exposed.
client = chromadb.HttpClient(host="localhost", port=8000)

collection = client.get_collection(name="ingestiq_content")

if len(sys.argv) > 1:
    client_id_filter = sys.argv[1]
    print(f"\nQuerying for client_id: '{client_id_filter}'")
    results = collection.get(where={"client_id": client_id_filter})
else:
    print("\nQuerying for all documents in the collection...")
    results = collection.get()



count = collection.count()
print(f"\nTotal vectors in collection: {count}")

if results['documents']:
    print("\n--- Sample of Ingested Documents ---")
    for i, doc in enumerate(results['documents'][:5]):
        meta = results['metadatas'][i]
        print(f"  - Doc {i+1} (client: {meta.get('client_id')}, file: {meta.get('file_path')}):\n    '{doc[:100]}...'")
    print("------------------------------------\n")
else:
    print("No documents found matching the filter.")

