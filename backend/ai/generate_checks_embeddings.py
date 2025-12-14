import json
import os
from typing import List, Dict, TypedDict

from models import CheckType


# from langchain.schema import Document
# from langchain_community.vectorstores import FAISS
# from langchain_openai import OpenAIEmbeddings
#
# from constants import OPENAI_API_KEY


# region GET CHECKS DESCRIPTION
class Check(TypedDict):
    name: str
    description: str


# checks: List[Check] = []

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.abspath(os.path.join(current_dir, '..'))
docs_by_check_type: Dict[CheckType, List[Check]] = {}

for file in [
    (CheckType.COOKIE, os.path.join(project_root, 'checks', 'cookies_checks_description.json')),
    (CheckType.LIGHTHOUSE, os.path.join(project_root, 'checks', 'lighthouse_checks_description.json')),
    (CheckType.NETWORK, os.path.join(project_root, 'checks', 'network_checks_description.json')),
    (CheckType.SCAN_PORTS, os.path.join(project_root, 'checks', 'scan_ports_checks_description.json')),
    (CheckType.TECHNOLOGIES, os.path.join(project_root, 'checks', 'technologies_checks_description.json')),
]:
    with open(file[1], 'r') as f:
        data: List[Check] = json.load(f)
        docs_by_check_type[file[0]] = data
        # checks.extend(data)

# print(checks, "\n\n")
# endregion

# region EMBEDDINGS MAGIC
# docs = [Document(page_content=check["description"], metadata={'name': check['name']}) for check in checks]
#
# embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
#
# db = FAISS.from_documents(docs, embeddings)

# db.save_local("faiss_index")
# endregion
