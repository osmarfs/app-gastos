import time
import threading # ADICIONE ESTA LINHA AQUI
import flet as ft
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# --- LIGAÇÃO À NUVEM (FIREBASE) ---
if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

def enviar_notificacao_familia(titulo, mensagem):
    try:
        db.collection("notificacoes").add({
            "titulo": titulo,
            "mensagem": mensagem,
            "timestamp": time.time() # Marca o segundo exato do envio
        })
        print("Aviso salvo na nuvem com sucesso!")
    except Exception as e:
        print(f"Erro ao avisar: {e}")

def main(page: ft.Page):
    # Configurações da aplicação
    page.title = "Controle de Gastos Familiar"
    page.window_width = 400
    page.window_height = 800 
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # ==========================================
    # O MOTORZINHO INVISÍVEL
    # ==========================================
    def motorzinho_de_notificacao():
        ultimo_aviso = time.time() # Grava a hora exata que você abriu o app
        
        while True:
            time.sleep(5) # A cada 5 segundos ele vai checar o banco
            try:
                # Busca apenas a última mensagem
                docs = db.collection("notificacoes").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
                for doc in docs:
                    notif = doc.to_dict()
                    tempo_mensagem = notif.get("timestamp", 0)
                    
                    # Se a mensagem for mais nova que a última que vimos, mostra na tela!
                    if tempo_mensagem > ultimo_aviso:
                        ultimo_aviso = tempo_mensagem # Salva que já vimos essa
                        
                        page.snack_bar = ft.SnackBar(
                            content=ft.Text(f"🔔 {notif.get('titulo')}\n{notif.get('mensagem')}", size=16, weight="bold", color="white"),
                            bgcolor="#00BFFF", # Azul chamativo
                            open=True
                        )
                        page.update()
            except:
                pass

    # Liga o motorzinho assim que o app abre!
    threading.Thread(target=motorzinho_de_notificacao, daemon=True).start()
    # ==========================================

    mes_ano_atual = datetime.date.today().strftime("%m/%Y")

    # --- ELEMENTOS DA INTERFACE PRINCIPAL ---
    texto_renda = ft.Text("Renda: R$ 0.00", size=16, weight=ft.FontWeight.BOLD, color="blue")
    texto_despesas = ft.Text("Despesas: R$ 0.00", size=16, weight=ft.FontWeight.BOLD, color="orange")
    texto_saldo = ft.Text("Saldo: R$ 0.00", size=22, weight=ft.FontWeight.BOLD)
    
    painel_resumo = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"Resumo de {mes_ano_atual}", size=20, weight=ft.FontWeight.BOLD),
                    ft.IconButton(
                        icon=ft.icons.Icons.REFRESH, 
                        icon_color="blue",
                        tooltip="Atualizar dados",
                        on_click=lambda _: carregar_dados()
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                texto_renda,
                texto_despesas,
                texto_saldo
            ]),
            padding=20,
            width=400
        ),
        bgcolor="#f4f4f4" 
    )
    
    cores_categorias = {
        "Alimentação / Supermercado": "blue",
        "Habitação (Renda, Água, Luz)": "red",
        "Transporte": "green",
        "Lazer": "purple",
        "Outros": "orange"
    }
    
    legenda_grafico = ft.Column(spacing=10)
    
    painel_grafico = ft.Card(
        content=ft.Container(
            content=legenda_grafico,
            padding=15
        ),
        visible=False
    )

    input_renda = ft.TextField(label="Atualizar Salário (R$)", width=200, keyboard_type=ft.KeyboardType.NUMBER)
    descricao_input = ft.TextField(label="Descrição", width=300)
    valor_input = ft.TextField(label="Valor Gasto (R$)", width=300, keyboard_type=ft.KeyboardType.NUMBER)
    categoria_dropdown = ft.Dropdown(
        label="Categoria",
        width=300,
        options=[
            ft.dropdown.Option("Alimentação / Supermercado"),
            ft.dropdown.Option("Habitação (Renda, Água, Luz)"),
            ft.dropdown.Option("Transporte"),
            ft.dropdown.Option("Lazer"),
            ft.dropdown.Option("Outros"),
            ft.dropdown.Option("Cartão de Crédito")
        ],
    )
    forma_pagamento_dropdown = ft.Dropdown(
        label="Pagamento",
        width=145,
        options=[
            ft.dropdown.Option("Pix"),
            ft.dropdown.Option("Cartão de Crédito"),
            ft.dropdown.Option("Dinheiro"),
        ],
    )
    
    quem_pagou_dropdown = ft.Dropdown(
        label="Quem Pagou?",
        width=145,
        options=[
            ft.dropdown.Option("Osmar"),
            ft.dropdown.Option("Heloisa"),
            ft.dropdown.Option("Conta Conjunta"),
        ],
    )

    lista_gastos_atual = ft.Column()
    lista_historico_meses = ft.Column()
    lista_de_listas_salvas = ft.Column() 

    # --- NOSSAS 4 TELAS ---
    ecra_inicio = ft.Column(visible=True)
    ecra_compras = ft.Column(visible=False)
    ecra_listas_salvas = ft.Column(visible=False)
    ecra_historico = ft.Column(visible=False)

    # --- FUNÇÕES DE BANCO DE DADOS ---
    def apagar_gasto(doc_id):
        db.collection("gastos").document(doc_id).delete()
        page.snack_bar = ft.SnackBar(ft.Text("Registro eliminado com sucesso!"))
        page.snack_bar.open = True
        carregar_dados()

    def apagar_lista(doc_id):
        db.collection("listas_compras").document(doc_id).delete()
        page.snack_bar = ft.SnackBar(ft.Text("Lista de compras apagada!"))
        page.snack_bar.open = True
        carregar_dados()

    def ver_detalhes_mes(mes_selecionado):
        lista_historico_meses.controls.clear()
        
        id_mes_busca = mes_selecionado.replace("/", "_")
        doc_renda_velha = db.collection("resumo").document(id_mes_busca).get()
        renda_epoca = doc_renda_velha.to_dict().get("renda", 0.0) if doc_renda_velha.exists else 0.0

        lista_historico_meses.controls.append(
            ft.Column([
                ft.Row([
                    ft.IconButton(icon=ft.icons.Icons.ARROW_BACK, on_click=lambda _: carregar_dados()),
                    ft.Text(f"Detalhes: {mes_selecionado}", size=20, weight="bold")
                ]),
                ft.Text(f"Renda na época: R$ {renda_epoca:.2f}", color="blue", weight="bold"),
                ft.Divider()
            ])
        )

        docs = db.collection("gastos").where("mes_ano", "==", mes_selecionado).stream()
        for doc in docs:
            d = doc.to_dict()
            v = float(str(d.get('valor', 0)).replace(',', '.'))
            
            texto_gasto = f"[{d.get('data')}] {d.get('descricao')} - R$ {v:.2f}"
            
            if "itens_detalhados" in d and len(d["itens_detalhados"]) > 0:
                texto_gasto += "\nLista do que foi comprado:"
                for item in d["itens_detalhados"]:
                    subtotal = item["qtd"] * item["preco"]
                    texto_gasto += f"\n  • {item['qtd']}x {item['nome']} (R$ {item['preco']:.2f} cada) = R$ {subtotal:.2f}"

            lista_historico_meses.controls.append(
                ft.Card(content=ft.Container(content=ft.Text(texto_gasto), padding=10))
            )
        page.update()

    def carregar_dados():
        lista_gastos_atual.controls.clear()
        lista_historico_meses.controls.clear()
        lista_de_listas_salvas.controls.clear() 
        
        total_despesas_mes_atual = 0.0
        gastos_por_categoria = {} 
        
        id_mes_atual = mes_ano_atual.replace("/", "_")
        doc_renda = db.collection("resumo").document(id_mes_atual).get()
        renda_atual = doc_renda.to_dict().get("renda", 0.0) if doc_renda.exists else 0.0

        todos_docs = db.collection("gastos").order_by("data_registro", direction=firestore.Query.DESCENDING).stream()
        gastos_por_mes = {}

        for doc in todos_docs:
            dado = doc.to_dict()
            doc_id = doc.id
            v_num = float(str(dado.get('valor', 0)).replace(',', '.'))
            mes_ano_reg = dado.get("mes_ano", "Desconhecido")

            if mes_ano_reg not in gastos_por_mes:
                gastos_por_mes[mes_ano_reg] = 0.0
            gastos_por_mes[mes_ano_reg] += v_num

            if mes_ano_reg == mes_ano_atual:
                total_despesas_mes_atual += v_num

                cat = dado.get("categoria", "Outros")
                if cat not in gastos_por_categoria:
                    gastos_por_categoria[cat] = 0.0
                gastos_por_categoria[cat] += v_num

                texto_item = f"[{dado.get('data')}] {dado.get('descricao')} \nPagou: {dado.get('quem_pagou', '')} via {dado.get('forma_pagamento', '')}\nR$ {v_num:.2f}"
                
                cartao = ft.Card(content=ft.Container(
                    content=ft.Row([
                        ft.Text(texto_item, expand=True), 
                        ft.IconButton(icon=ft.icons.Icons.DELETE, icon_color="red", on_click=lambda e, id=doc_id: apagar_gasto(id))
                    ]), padding=10
                ))
                lista_gastos_atual.controls.append(cartao)

        saldo = renda_atual - total_despesas_mes_atual
        texto_renda.value = f"Renda: R$ {renda_atual:.2f}"
        texto_despesas.value = f"Despesas: R$ {total_despesas_mes_atual:.2f}"
        texto_saldo.value = f"Saldo: R$ {saldo:.2f}"
        texto_saldo.color = "green" if saldo >= 0 else "red"

        legenda_grafico.controls.clear()
        
        if total_despesas_mes_atual > 0:
            legenda_grafico.controls.append(ft.Text("Onde seu dinheiro foi:", weight="bold", size=16))
            
            for cat, valor_cat in gastos_por_categoria.items():
                cor = cores_categorias.get(cat, "grey")
                porcentagem_decimal = valor_cat / total_despesas_mes_atual
                porcentagem_texto = porcentagem_decimal * 100
                
                linha_texto = ft.Row([
                    ft.Text(cat, size=12, weight="bold"), 
                    ft.Text(f"R$ {valor_cat:.2f} ({porcentagem_texto:.0f}%)", size=12)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                
                barra = ft.ProgressBar(value=porcentagem_decimal, color=cor, bgcolor="#e0e0e0", height=8)
                
                legenda_grafico.controls.append(ft.Column([linha_texto, barra], spacing=2))
            
            painel_grafico.visible = True
        else:
            painel_grafico.visible = False

        for mes, soma_mes in gastos_por_mes.items():
            id_m = mes.replace("/", "_")
            d_r = db.collection("resumo").document(id_m).get()
            r_m = d_r.to_dict().get("renda", 0.0) if d_r.exists else 0.0
            
            saldo_m = r_m - soma_mes
            cor_m = "green" if saldo_m >= 0 else "red"

            cabecalho = ft.Container(
                content=ft.Row([
                    ft.Text(f"Mês: {mes}", size=16, weight="bold"),
                    ft.Text(f"Gasto: R$ {soma_mes:.2f} | Saldo: R$ {saldo_m:.2f}", color=cor_m, weight="bold")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor="#e0e0e0", padding=10, border_radius=5,
                on_click=lambda e, m=mes: ver_detalhes_mes(m)
            )
            lista_historico_meses.controls.append(ft.Card(content=cabecalho))

        docs_listas = db.collection("listas_compras").order_by("data_criacao", direction=firestore.Query.DESCENDING).stream()
        for doc in docs_listas:
            d = doc.to_dict()
            doc_id = doc.id
            itens_str = ""
            for item in d.get("itens", []):
                itens_str += f"\n  • {item['qtd']}x {item['nome']} (R$ {item.get('preco', 0):.2f})"
            
            cartao_lista = ft.Card(content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"Data: {d.get('data_texto')}\nPrevisto: R$ {d.get('total_previsto', 0):.2f}", weight="bold", color="blue", expand=True),
                        ft.IconButton(icon=ft.icons.Icons.DELETE, icon_color="red", on_click=lambda e, id=doc_id: apagar_lista(id))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(itens_str)
                ]), padding=10
            ))
            lista_de_listas_salvas.controls.append(cartao_lista)

        page.update()

    def salvar_renda_clique(e):
        if not input_renda.value: return
        try:
            valor = float(input_renda.value.replace(',', '.'))
            id_m = mes_ano_atual.replace("/", "_")
            db.collection("resumo").document(id_m).set({"renda": valor})
            input_renda.value = ""
            carregar_dados()
        except:
            pass

    def adicionar_gasto_clique(e):
        if not descricao_input.value or not valor_input.value: return
        try:
            v = float(valor_input.value.replace(',', '.'))
            hoje = datetime.date.today()
            db.collection("gastos").add({
                "descricao": descricao_input.value,
                "valor": v,
                "categoria": categoria_dropdown.value,
                "forma_pagamento": forma_pagamento_dropdown.value if forma_pagamento_dropdown.value else "Não informado",
                "quem_pagou": quem_pagou_dropdown.value if quem_pagou_dropdown.value else "Não informado",
                "data": hoje.strftime("%d/%m/%Y"),
                "mes_ano": hoje.strftime("%m/%Y"),
                "data_registro": firestore.SERVER_TIMESTAMP
            })
            descricao_input.value = ""
            valor_input.value = ""
            categoria_dropdown.value = None
            forma_pagamento_dropdown.value = None
            quem_pagou_dropdown.value = None
            carregar_dados()
        except:
            pass

    # --- LÓGICA DA ABA DE COMPRAS ---
    itens_mercado = [
        {"nome": "Arroz", "qtd": 0, "preco": 0.0},
        {"nome": "Feijão", "qtd": 0, "preco": 0.0},
        {"nome": "Macarrão", "qtd": 0, "preco": 0.0},
        {"nome": "Óleo", "qtd": 0, "preco": 0.0},
        {"nome": "Açúcar", "qtd": 0, "preco": 0.0},
        {"nome": "Sal", "qtd": 0, "preco": 0.0},
        {"nome": "Café", "qtd": 0, "preco": 0.0},
        {"nome": "Farinha de Trigo", "qtd": 0, "preco": 0.0},
        {"nome": "Farinha de Mandioca", "qtd": 0, "preco": 0.0},
        {"nome": "Cuscuz / Flocão", "qtd": 0, "preco": 0.0},
        {"nome": "Leite", "qtd": 0, "preco": 0.0},
        {"nome": "Manteiga / Margarina", "qtd": 0, "preco": 0.0},
        {"nome": "Queijo", "qtd": 0, "preco": 0.0},
        {"nome": "Presunto / Mortadela", "qtd": 0, "preco": 0.0},
        {"nome": "Pão", "qtd": 0, "preco": 0.0},
        {"nome": "Carne Bovina", "qtd": 0, "preco": 0.0},
        {"nome": "Frango", "qtd": 0, "preco": 0.0},
        {"nome": "Sabão em Pó", "qtd": 0, "preco": 0.0},
        {"nome": "Detergente", "qtd": 0, "preco": 0.0},
        {"nome": "Papel Higiênico", "qtd": 0, "preco": 0.0},
    ]

    lista_ui_compras = ft.Column(scroll=ft.ScrollMode.AUTO)
    texto_total_compras = ft.Text("Total: R$ 0.00", size=22, weight="bold", color="green")

    def recalcular_total_compras():
        total = sum(item["qtd"] * item["preco"] for item in itens_mercado)
        texto_total_compras.value = f"Total: R$ {total:.2f}"
        page.update()

    def criar_linha_item(item):
        campo_qtd = ft.TextField(label="Qtd", width=70, keyboard_type=ft.KeyboardType.NUMBER)
        campo_preco = ft.TextField(label="R$ Unit", width=90, keyboard_type=ft.KeyboardType.NUMBER)
        
        def atualizar_valores(e):
            try: item["qtd"] = int(campo_qtd.value) if campo_qtd.value else 0
            except: item["qtd"] = 0
            
            try: item["preco"] = float(campo_preco.value.replace(',', '.')) if campo_preco.value else 0.0
            except: item["preco"] = 0.0
            
            recalcular_total_compras()

        campo_qtd.on_change = atualizar_valores
        campo_preco.on_change = atualizar_valores

        return ft.Card(content=ft.Container(
            content=ft.Row([
                ft.Text(item["nome"], width=120, weight="bold"),
                campo_qtd,
                campo_preco,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10
        ))

    for item in itens_mercado:
        lista_ui_compras.controls.append(criar_linha_item(item))

    def resetar_formulario_compras():
        for item in itens_mercado:
            item["qtd"] = 0
            item["preco"] = 0.0
        lista_ui_compras.controls.clear()
        for item in itens_mercado:
            lista_ui_compras.controls.append(criar_linha_item(item))
        recalcular_total_compras()

    def finalizar_compra(e):
        total = sum(item["qtd"] * item["preco"] for item in itens_mercado)
        if total == 0:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha algum valor antes de finalizar!"))
            page.snack_bar.open = True
            page.update()
            return
            
        enviar_notificacao_familia(
            "Compras Realizadas! ✅", 
            f"O Osmar finalizou as compras no valor de R$ {total:.2f}."
        )
            
        itens_comprados = [{"nome": i["nome"], "qtd": i["qtd"], "preco": i["preco"]} for i in itens_mercado if i["qtd"] > 0]
        
        hoje = datetime.date.today()
        db.collection("gastos").add({
            "descricao": "Compra de Mercado",
            "valor": total,
            "categoria": "Alimentação / Supermercado",
            "data": hoje.strftime("%d/%m/%Y"),
            "mes_ano": hoje.strftime("%m/%Y"),
            "data_registro": firestore.SERVER_TIMESTAMP,
            "itens_detalhados": itens_comprados
        })
        
        resetar_formulario_compras()
        page.snack_bar = ft.SnackBar(ft.Text(f"Compra de R$ {total:.2f} lançada com sucesso!"))
        page.snack_bar.open = True
        carregar_dados()
        page.navigation_bar.selected_index = 0
        mudar_tab(None)

    def salvar_lista_sem_lancar(e):
        itens_salvar = [{"nome": i["nome"], "qtd": i["qtd"], "preco": i["preco"]} for i in itens_mercado if i["qtd"] > 0]
        if not itens_salvar:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha as quantidades para salvar a lista!"))
            page.snack_bar.open = True
            page.update()
            return

        total_previsto = sum(item["qtd"] * item["preco"] for item in itens_salvar)
        hoje = datetime.date.today()
        
        db.collection("listas_compras").add({
            "data_texto": hoje.strftime("%d/%m/%Y"),
            "data_criacao": firestore.SERVER_TIMESTAMP,
            "itens": itens_salvar,
            "total_previsto": total_previsto
        })

        enviar_notificacao_familia("Nova Lista de Compras! 🛒", "Uma nova lista foi salva. Não esqueça de ir ao mercado!")
        
        resetar_formulario_compras()
        page.snack_bar = ft.SnackBar(ft.Text("Sua lista foi salva na aba 'Listas' com sucesso!"))
        page.snack_bar.open = True
        carregar_dados()
        page.navigation_bar.selected_index = 2 
        mudar_tab(None)

    botao_finalizar = ft.ElevatedButton("Finalizar e Lançar Despesa", on_click=finalizar_compra, bgcolor="green", color="white", width=300)
    botao_salvar_lista = ft.ElevatedButton("Apenas Salvar Lista (Para Depois)", on_click=salvar_lista_sem_lancar, bgcolor="blue", color="white", width=300)

    # --- NAVEGAÇÃO ---
    def mudar_tab(e):
        index = e.control.selected_index if e else page.navigation_bar.selected_index
        
        ecra_inicio.visible = (index == 0)
        ecra_compras.visible = (index == 1)
        ecra_listas_salvas.visible = (index == 2) 
        ecra_historico.visible = (index == 3)     
        
        if index in [0, 2, 3]: 
            carregar_dados()
            
        page.update()

    # Deixe a sua barra de navegação assim novamente:
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.Icons.HOME, label="Início"),
            ft.NavigationBarDestination(icon=ft.icons.Icons.SHOPPING_CART, label="Mercado"),
            ft.NavigationBarDestination(icon=ft.icons.Icons.LIST_ALT, label="Listas"),
            ft.NavigationBarDestination(icon=ft.icons.Icons.CALENDAR_MONTH, label="Meses"),
        ],
        on_change=mudar_tab # Volta a apontar direto para a função original
    )

    

    # --- MONTAGEM DAS TELAS ---
    ecra_inicio.controls.extend([
        painel_resumo,
        painel_grafico, 
        ft.Divider(),
        ft.Row([input_renda, ft.ElevatedButton("Guardar Salário", on_click=salvar_renda_clique)]),
        ft.Divider(),
        ft.Text("Adicionar Nova Despesa", size=18, weight="bold"),
        descricao_input, 
        valor_input, 
        categoria_dropdown,
        ft.Row([forma_pagamento_dropdown, quem_pagou_dropdown]), 
        ft.ElevatedButton("Lançar Gasto", on_click=adicionar_gasto_clique, width=300, bgcolor="blue", color="white"),
        ft.Divider(),
        ft.Text(f"Lançamentos de {mes_ano_atual}", size=18, weight="bold"),
        lista_gastos_atual
    ])

    ecra_compras.controls.extend([
        ft.Text("Fazer Mercado", size=24, weight="bold"),
        ft.Text("Preencha para somar. Depois escolha se quer lançar como gasto ou apenas salvar a lista.", size=14, color="grey"),
        ft.Divider(),
        texto_total_compras,
        botao_finalizar,
        botao_salvar_lista, 
        ft.Divider(),
        ft.Container(content=lista_ui_compras, height=350, expand=True) 
    ])

    ecra_listas_salvas.controls.extend([
        ft.Text("Minhas Listas Salvas", size=24, weight="bold"),
        ft.Text("Abaixo estão as listas de compras que você guardou para não esquecer.", size=14, color="grey"),
        ft.Divider(),
        lista_de_listas_salvas
    ])

    ecra_historico.controls.extend([
        ft.Text("Histórico por Mês", size=24, weight="bold"),
        ft.Text("Clique no mês para ver os detalhes e as listas de mercado lançadas.", size=14, color="grey"),
        ft.Divider(),
        lista_historico_meses
    ])
    
    # AQUI ESTAVA O ERRO DE DUPLICIDADE: Agora só adicionamos à página uma única vez
    page.add(ecra_inicio, ecra_compras, ecra_listas_salvas, ecra_historico)
    carregar_dados()

ft.app(target=main)