from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class SemanticSearchService:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def embeded_product(self,product_list):

        product_descriptions = [
            f"{item['Product Name']} - {item['Product Type']}, {item['Variant Option']}, ${item['Price']}"
            for item in product_list
        ]

        product_embeddings = np.array(self.model.encode(product_descriptions))

        index = faiss.IndexFlatL2(product_embeddings.shape[1])
        index.add(product_embeddings)

        return index
