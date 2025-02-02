from opensearchpy import OpenSearch
import yaml
import json
import os


domain_endpoint = os.environ.get("DOMAIN_ENDPOINT")
master_user = os.environ.get("MASTER_USER")
master_passwd = os.environ.get("MASTER_PASSWORD")
index_name = os.environ.get("INDEX_NAME")

# OpenSearch 클라이언트 설정
client = OpenSearch(
    hosts=[{'host': domain_endpoint, 'port': 443}],
    http_auth=(master_user, master_passwd),  # 필요한 경우 인증 정보 입력
    use_ssl=True,
    verify_certs=True
)

try:
    response = client.indices.delete(index=index_name)
    print(f"인덱스 '{index_name}' 삭제 결과:", response)
except Exception as e:
    print(e)

index_mapping = {
    "settings": {
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 2
        }
    },
    "mappings": {
        "properties": {
            "current_stock": {
                "type": "integer"
            },
            "name": {
                "type": "text"
            },
            "category": {
                "type": "keyword"
            },
            "style": {
                "type": "text",
                "fields": {
                    "type": "keyword",
                    "ignore_above": 256
                }
            },
            "description": {
                "type": "text"
            },
            "price": {
                "type": "integer"
            },
            "image": {
                "type": "keyword"
            },
            "gender_affinity": {
                "type": "keyword"
            },
            "where_visible": {
                "type": "keyword"
            }
        }
    }
}
response = client.indices.create(index=index_name, body=index_mapping)
print(f"인덱스 '{index_name}' 생성 결과:", response)

# YAML 파일 열기
with open('products_ko.yaml', 'r', encoding='utf-8') as file:
    # YAML 파일 내용을 Python 객체로 로드
    arr = yaml.safe_load(file)

url_prefix = "https://raw.githubusercontent.com/YonghoChoi/genai-search/refs/heads/main/assets"
bulk_data = ""
count = 0
for data in arr:
    image_url = f"{url_prefix}/{data['category']}/{data['image']}"
    data['image_url'] = image_url
    index = {
        "index": {
            "_index": index_name,
            "_id": data.pop("id")
        }
    }
    bulk_data = bulk_data + f"{json.dumps(index)}\n{json.dumps(data)}\n"
    if count == 1000:
        # Bulk 인덱싱 수행
        resp = client.bulk(bulk_data)
        print(resp)

        # 초기화
        bulk_data = ""
        count = 0
        continue

    count += 1


resp = client.search(body={
    "size": 10,
    "_source": {
        "includes": [
            "name",
            "description",
            "image_url"
        ]
    },
    "query": {
        "query_string": {
              "query": "watch",
              "default_field": "description"
            }
    }
}, index=index_name)
print(resp)