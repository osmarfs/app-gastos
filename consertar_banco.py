import firebase_admin
from firebase_admin import credentials, firestore

# 1. Liga no seu Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 2. DEFINA O SEU TOKEN AQUI (O que você quer colocar nos gastos antigos)
MEU_TOKEN = "CLAN-NN4HQ" # <--- MUDE ISSO AQUI, OSMAR!

def consertar_registros():
    colecoes = ["gastos", "metas", "consignados", "listas_compras", "rendas"]
    print("🚀 Iniciando carimbo em massa...")

    for col in colecoes:
        docs = db.collection(col).stream()
        contador = 0
        for doc in docs:
            dados = doc.to_dict()
            # Se o documento não tem o token, a gente coloca!
            if "token_familia" not in dados:
                db.collection(col).document(doc.id).update({
                    "token_familia": MEU_TOKEN
                })
                contador += 1
        print(f"✅ Coleção '{col}': {contador} registros atualizados.")

    print("\n🏆 BANCO DE DADOS ATUALIZADO! Pode abrir o app agora.")

consertar_registros()