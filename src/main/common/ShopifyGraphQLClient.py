import os
import requests

class ShopifyGraphQLClient:
    def __init__(self):
        self.url = os.getenv("SHOPIFY_GRAPHQL_URL")
        self.access_token = os.getenv("SHOP_TOKEN")
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
    
    def fetch_products(self):
      all_products = []
      cursor = None  

      while True:
          query = f"""
          {{
            products(first: 50{', after: "' + cursor + '"' if cursor else ''}) {{
              edges {{
                cursor
                node {{
                  id
                  title
                  bodyHtml
                  vendor
                  handle
                  tags
                  status
                  createdAt
                  updatedAt
                  productType
                  images(first: 1) {{
                    edges {{
                      node {{
                        src
                      }}
                    }}
                  }}
                  variants(first: 10) {{
                    edges {{
                      node {{
                        id
                        title
                        price
                        inventoryQuantity
                        sku
                        createdAt
                        updatedAt
                        selectedOptions {{
                          name
                          value
                        }}
                      }}
                    }}
                  }}
                }}
              }}
              pageInfo {{
                hasNextPage
                endCursor
              }}
            }}
          }}
          """

          response = requests.post(self.url, json={'query': query}, headers=self.headers)
          if response.status_code != 200:
              response.raise_for_status()

          data = response.json()
          products = data['data']['products']

          all_products.extend(products['edges'])  

          if products['pageInfo']['hasNextPage']:
              cursor = products['pageInfo']['endCursor']
          else:
              break  

      return {"data": {"products": {"edges": all_products}}}
