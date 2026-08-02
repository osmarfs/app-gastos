import random
import string
import os
import json
import flet as ft
import asyncio
import flet_charts
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


# --- LIGAÇÃO À NUVEM (FIREBASE) ---
if not firebase_admin._apps:
    cred = credentials.Certificate("credenciais.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- ESTILO PREMIUM REUTILIZÁVEL ---
def criar_cartao_premium(conteudo, elevation=4):
    return ft.Card(
        elevation=elevation,  # sombra
        animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT_QUAD),
        #bgcolor=ft.Colors.WHITE,
        content=ft.Container(
            content=conteudo,
            padding=15,
            border_radius=ft.border_radius.all(16),  # AQUI funciona
        )
    )

# 👇 COLE A NOVA FUNÇÃO AQUI 👇
def criar_barra_categoria(nome_categoria, valor_gasto, total_gasto, cor_flet, sub_itens=[]):
    pct = valor_gasto / total_gasto if total_gasto > 0 else 0

    coluna_detalhes = ft.Column(
        controls=[
            ft.Row([
                ft.Text(f"  ↳ {item['nome']}", size=11, color=ft.Colors.GREY_600, expand=True), 
                ft.Text(f"R$ {item['valor']:.2f}", size=11, color=ft.Colors.GREY_600)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN) for item in sub_itens
        ],
        visible=False, spacing=2
    )

    def alternar_detalhes(e):
        coluna_detalhes.visible = not coluna_detalhes.visible
        e.control.page.update()

    barra_principal = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text(f"{nome_categoria} ▾", weight=ft.FontWeight.BOLD, size=13),
                ft.Text(f"R$ {valor_gasto:.2f} ({(pct*100):.0f}%)", color=ft.Colors.GREY_600, size=12)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.ProgressBar(value=pct, color=cor_flet, bgcolor=ft.Colors.GREY_200, height=8, border_radius=10)
        ], spacing=2),
        on_click=alternar_detalhes, ink=True, padding=ft.padding.symmetric(vertical=5)
    )
    return ft.Column([barra_principal, coluna_detalhes], spacing=0)
# 👆 FIM DA NOVA FUNÇÃO 👆

async def main(page: ft.Page):
    # =======================================================
    # 🚀 1. A TELA DE CARREGAMENTO PREMIUM (Bolinhas Android TV)
    # =======================================================
    page.title = "Controle de Gastos Familiar"
    page.window_width = 400
    page.window_height = 800 
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.padding = 20
    
    
        # Código limpo, moderno e compatível com Flet 0.82+
    barra_carregamento = ft.ProgressBar(width=200, color=ft.Colors.BLUE_400, bgcolor=ft.Colors.GREY_200)
    texto_carregando = ft.Text("Sincronizando os dados da família...", size=14, color=ft.Colors.GREY_600)

    tela_loading = ft.Column(
        [barra_carregamento, texto_carregando],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )


    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    page.add(tela_loading)
    page.update()


    
            
    await asyncio.sleep(0.2) # Pausa final para a transição ficar suave
    page.scroll = ft.ScrollMode.AUTO
    await asyncio.sleep(0.1)
    
    try:
        page.window.icon = "icon.png"
    except:
        page.window_icon = "icon.png"
   

    # =======================================================
    # 🔐 2. LENDO A MEMÓRIA DO CELULAR 
    # =======================================================
    usuario_nome = await page.shared_preferences.get("usuario_nome")
    usuario_nasc = await page.shared_preferences.get("usuario_nasc")
    usuario_5_anos = await page.shared_preferences.get("usuario_5_anos")
    usuario_token = await page.shared_preferences.get("usuario_token")
    # =======================================================
    # 📝 3. TELA DE LOGIN (SISTEMA DE CLÃS E FAMÍLIAS)
    # =======================================================
    def gerar_token():
        # Cria um código forte de 5 letras e números
        caracteres = string.ascii_uppercase + string.digits
        return "CLAN-" + ''.join(random.choice(caracteres) for _ in range(5))

    # Campos Gerais (Para todo mundo)
    campo_nome = ft.TextField(label="Seu Nome", width=300, text_align=ft.TextAlign.CENTER, prefix_icon=ft.Icons.PERSON)
    
    def formatar_data(e):
        numeros = "".join(filter(str.isdigit, e.control.value))
        if len(numeros) > 2: numeros = f"{numeros[:2]}/{numeros[2:]}"
        if len(numeros) > 5: numeros = f"{numeros[:5]}/{numeros[5:9]}"
        e.control.value = numeros
        e.control.update()
    
    # 👇 A MÁSCARA RAIZ (Continua a mesma, perfeita!) 👇
    def mascara_data(e):
        numeros = "".join(filter(str.isdigit, e.control.value))
        
        if len(numeros) <= 2:
            resultado = numeros
        elif len(numeros) <= 4:
            resultado = f"{numeros[:2]}/{numeros[2:]}"
        else:
            resultado = f"{numeros[:2]}/{numeros[2:4]}/{numeros[4:8]}"
            
        e.control.value = resultado
        e.control.update()

    # 👇 O CAMPO COM O GATILHO DA VERSÃO 0.82+ 👇
    campo_nascimento = ft.TextField(
        label="Data de Nascimento (DD/MM/AAAA)", 
        width=300, 
        text_align=ft.TextAlign.CENTER, 
        keyboard_type=ft.KeyboardType.DATETIME, 
        on_focus=mascara_data, # <--- O SEGREDO ESTAVA NO SEU PRINT O TEMPO TODO!
        prefix_icon=ft.Icons.CALENDAR_TODAY,
        bgcolor="white", border_radius=10, border_color="#D1D9E6", color="black"
    )
    dropdown_carteira = ft.Dropdown(label="Carteira assinada há mais de 5 anos?", width=300, options=[ft.dropdown.Option("Sim"), ft.dropdown.Option("Não")])

    # Campos do PATRIARCA/MATRIARCA (Criar Clã)
    campo_nome_familia = ft.TextField(label="Nome da Família (Ex: Os Silva)", width=300, text_align=ft.TextAlign.CENTER, prefix_icon=ft.Icons.HOME)
    campo_senha_lider = ft.TextField(label="Crie uma Senha (Só para o Líder)", width=300, password=True, can_reveal_password=True, text_align=ft.TextAlign.CENTER, prefix_icon=ft.Icons.LOCK)

    # Campos do MEMBRO (Entrar com Token)
    campo_token_acesso = ft.TextField(label="Token da Família (Ex: CLAN-12345)", width=300, text_align=ft.TextAlign.CENTER, capitalization=ft.TextCapitalization.CHARACTERS, prefix_icon=ft.Icons.VPN_KEY
    )

    # --- A LÓGICA DE SALVAR E ENTRAR ---
    # --- A LÓGICA DE SALVAR E ENTRAR (AGORA À PROVA DE BALAS!) ---
    async def processar_login(tipo_login):
        nome = campo_nome.value.strip().title() if campo_nome.value else ""
        nasc = campo_nascimento.value.strip() if campo_nascimento.value else ""
        tem_5_anos = dropdown_carteira.value == "Sim"

        # 👇 O MEGAFONE UNIVERSAL DO FLET 👇
        def avisar(mensagem, cor="red"):
            page.snack_bar = ft.SnackBar(ft.Text(mensagem, color="white", weight="bold"), bgcolor=cor)
            page.snack_bar.open = True
            page.update()

        if not nome or not nasc or not dropdown_carteira.value:
            avisar("Preencha seus dados básicos!")
            return

        token_final = ""

        try:
            if tipo_login == "criar":
                if not campo_nome_familia.value or not campo_senha_lider.value:
                    avisar("Preencha os dados da família!")
                    return
                
                token_final = gerar_token()
                # 👇 AGORA A FAMÍLIA NASCE COM A LISTA DE MEMBROS 👇
                db.collection("familias").document(token_final).set({
                    "nome_familia": campo_nome_familia.value,
                    "patriarca": nome,
                    "senha_lider": campo_senha_lider.value,
                    "membros": {nome: "lider"}, # O Líder já entra como VIP
                    "data_criacao": firestore.SERVER_TIMESTAMP
                })
                avisar(f"Clã criado! O seu Token é {token_final}", "green")

            elif tipo_login == "entrar":
                if not campo_token_acesso.value:
                    avisar("Digite o Token da sua família!")
                    return
                
                token_digitado = campo_token_acesso.value.strip().upper()
                doc_familia = db.collection("familias").document(token_digitado).get()
                
                if not doc_familia.exists:
                    avisar("Token inválido! Nenhuma família encontrada.")
                    return
                
                # 👇 A CATRACA DE SEGURANÇA 👇
                dados_familia = doc_familia.to_dict()
                mapa_membros = dados_familia.get("membros", {})
                
                if mapa_membros.get(nome) == "bloqueado":
                    avisar("🚫 Acesso Revogado! O Líder baniu sua conta.")
                    return
                
                # Se passou e é novo, adiciona o nome dele na lista da família
                if nome not in mapa_membros:
                    db.collection("familias").document(token_digitado).set({
                        "membros": {nome: "ativo"}
                    }, merge=True)
                
                token_final = token_digitado
                nome_familia = dados_familia.get("nome_familia", "Família")
                avisar(f"Bem-vindo ao clã {nome_familia}!", "green")

            # Salva no cofre blindado do celular
            await page.shared_preferences.set("usuario_nome", str(nome))
            await page.shared_preferences.set("usuario_nasc", str(nasc))
            await page.shared_preferences.set("usuario_5_anos", str(tem_5_anos))
            await page.shared_preferences.set("usuario_token", str(token_final))
            
            # LIMPA A TELA PARA ABRIR O APP
            page.controls.clear()
            page.vertical_alignment = ft.MainAxisAlignment.START
            
            # 🚨 O TENTATIVA DE ABRIR O APP (Com detector de crash!)
            try:
                montar_interface_principal(nome, nasc, tem_5_anos, token_final)
                page.update()
            except Exception as erro_interface:
                page.controls.append(
                    ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE, color="red", size=80),
                        ft.Text("O APP CRASHOU AO ABRIR!", color="red", weight="bold", size=24),
                        ft.Text(f"Motivo: {erro_interface}", color="black", size=16)
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
                page.update()
                
        except Exception as erro_geral:
            avisar(f"Erro na nuvem: {erro_geral}")

    # --- O VISUAL DAS TELAS QUE SE ALTERNAM ---
    menu_escolha = ft.Column([
        ft.Icon(ft.Icons.FAMILY_RESTROOM, size=80, color="blue"),
        ft.Text("Bem-vindo ao Finanças em Família", size=22, weight="bold", text_align=ft.TextAlign.CENTER),
        ft.Divider(color="transparent"),
        ft.ElevatedButton("Fundar um Clã (Sou o Líder)", width=300, height=50, bgcolor="blue", color="white", on_click=lambda _: alternar_telas(tela_criar)),
        ft.ElevatedButton("Já tenho um Token (Sou Membro)", width=300, height=50, bgcolor=ft.Colors.GREY_300, color="black", on_click=lambda _: alternar_telas(tela_membro))
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # =======================================================
    # 📦 A FUNÇÃO MÁGICA QUE CRIA O DESIGN DO CARD
    # =======================================================
    def criar_card_login_centralizado(conteudo_form, acao_login, acao_voltar, titulo_form, subtitulo_form=""):
        coluna_form = ft.Column([
            ft.Icon(ft.Icons.FAMILY_RESTROOM, size=80, color="blue"),
            ft.Text(f"Bem-vindo ao Finanças", size=22, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.Text(subtitulo_form, size=14, color="grey", text_align=ft.TextAlign.CENTER),
            ft.Divider(color="transparent", height=10),
            
            # Encapsula o formulário como um card com padding e sombra
            ft.Container(
                content=ft.Column(conteudo_form, spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=25,
                width=350,
                border_radius=15,
                bgcolor=ft.Colors.WHITE,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.1, "black"))
            ),
            
            ft.Divider(color="transparent", height=10),
            # Botão de Login largo e verde com cantos arredondados
            ft.ElevatedButton(titulo_form, width=300, height=50, bgcolor="green", color="white", 
                             on_click=acao_login, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
            ft.TextButton("Voltar", on_click=acao_voltar)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        return coluna_form

    # 👇 OS FIOS CONDUTORES ASSÍNCRONOS (O SEGREDO PARA SALVAR) 👇
    async def acao_clique_criar(e):
        await processar_login("criar")

    async def acao_clique_entrar(e):
        await processar_login("entrar")

    # =======================================================
    # 🎨 MONTANDO AS 3 TELAS COM A FUNÇÃO ACIMA
    # =======================================================
    menu_escolha = ft.Column([
        ft.Icon(ft.Icons.FAMILY_RESTROOM, size=80, color="blue"),
        ft.Text("Bem-vindo ao Finanças em Família", size=22, weight="bold", text_align=ft.TextAlign.CENTER),
        ft.Divider(color="transparent"),
        ft.ElevatedButton("Fundar um Clã (Sou o Líder)", width=300, height=50, bgcolor="blue", color="white", on_click=lambda _: alternar_telas(tela_criar)),
        ft.ElevatedButton("Já tenho um Token (Sou Membro)", width=300, height=50, bgcolor=ft.Colors.GREY_300, color="black", on_click=lambda _: alternar_telas(tela_membro))
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # Cria a tela de Fundar Clã chamando a função mágica!
    tela_criar = criar_card_login_centralizado(
        [campo_nome_familia, campo_senha_lider, ft.Divider(), campo_nome, campo_nascimento, dropdown_carteira],
        acao_clique_criar, 
        lambda _: alternar_telas(menu_escolha),
        "👑 Fundar Nova Família",
        "Crie sua família e gere um Token para os outros."
    )
    tela_criar.visible = False

    # Cria a tela de Entrar no Clã chamando a função mágica!
    tela_membro = criar_card_login_centralizado(
        [campo_token_acesso, ft.Divider(), campo_nome, campo_nascimento, dropdown_carteira],
        acao_clique_entrar, 
        lambda _: alternar_telas(menu_escolha),
        "🤝 Entrar na Família",
        "Insira o Token fornecido pelo líder."
    )
    tela_membro.visible = False

    def alternar_telas(tela_ativa):
        menu_escolha.visible = False
        tela_criar.visible = False
        tela_membro.visible = False
        tela_ativa.visible = True
        page.update()

    # 4. A MÁGICA DA CENTRALIZAÇÃO ABSOLUTA
    tela_login = ft.Container(
        content=ft.Column(
            [menu_escolha, tela_criar, tela_membro], 
            alignment=ft.MainAxisAlignment.CENTER, 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True # A Coluna preenche a altura inteira do Container
        ),
        expand=True, # O Container preenche a página inteira
        alignment=ft.Alignment.CENTER # Alinha o conteúdo no centro do eixo X e Y
    )

    # ========================================================
    # APLICATIVO PRINCIPAL
    # ========================================================
    # Adicione o token_familia aqui! 👇
    def montar_interface_principal(nome_usuario, nascimento, tem_5_anos, usuario_token):
        
        async def sair_do_app(e):
            # ... resto do código continua igual ...

            await page.shared_preferences.remove("usuario_nome")
            await page.shared_preferences.remove("usuario_nasc")
            await page.shared_preferences.remove("usuario_5_anos")
                
            page.controls.clear()
            page.vertical_alignment = ft.MainAxisAlignment.CENTER
            page.add(tela_login)
            page.update()
            
        mes_ano_atual = datetime.date.today().strftime("%m/%Y")

        def calcular_pis():
            if not tem_5_anos: return "Sem direito ao PIS (Menos de 5 anos de carteira)."
            try:
                mes = nascimento.split("/")[1]
                meses = {"01":"Fevereiro", "02":"Março", "03":"Abril", "04":"Abril", "05":"Maio", "06":"Maio", 
                         "07":"Junho", "08":"Junho", "09":"Julho", "10":"Julho", "11":"Agosto", "12":"Agosto"}
                return f"Tem direito! Previsão: {meses.get(mes, 'Mês não encontrado')}."
            except:
                return "Erro ao calcular PIS. Verifique a data."

        mensagem_pis = calcular_pis()
        texto_boas_vindas = ft.Text(f"Olá, {nome_usuario}!", size=24, weight="bold", color="blue")
        
        # 👇 O CRACHÁ DO CLÃ (Com selectable=True para poder copiar!) 👇
        badge_token = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.KEY, color=ft.Colors.ORANGE_700, size=16),
                ft.Text(f"Token do Clã: {usuario_token}", weight="bold", color=ft.Colors.ORANGE_700, selectable=True),
            ], tight=True),
            bgcolor=ft.Colors.ORANGE_50,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border_radius=20,
            tooltip="Segure para copiar e convidar a família!"
        )

        # 👇 1. DESCOBRE SE QUEM LOGOU É O PATRIARCA 👇
        doc_cla = db.collection("familias").document(usuario_token).get()
        dados_cla = doc_cla.to_dict() if doc_cla.exists else {}
        eh_lider = dados_cla.get("patriarca") == nome_usuario

        # 👇 2. O PAINEL DE CONTROLE SECRETO 👇
        def abrir_painel_lider(e):
            doc_atual = db.collection("familias").document(usuario_token).get()
            membros_atuais = doc_atual.to_dict().get("membros", {})
            
            lista_ui = ft.Column(spacing=10)
            
            for m_nome, m_status in membros_atuais.items():
                if m_nome == nome_usuario: continue # O líder não pode se bloquear kkkk
                
                esta_bloqueado = m_status == "bloqueado"
                cor_status = ft.Colors.RED if esta_bloqueado else ft.Colors.GREEN
                txt_status = "Bloqueado" if esta_bloqueado else "Ativo"
                icone_btn = ft.Icons.LOCK_OPEN if esta_bloqueado else ft.Icons.BLOCK
                cor_btn = ft.Colors.GREEN if esta_bloqueado else ft.Colors.RED
                
                # A Mágica do Banimento (Troca o status na nuvem)
                def alterar_status(e, nome_alvo=m_nome, status_atual=m_status):
                    novo_status = "ativo" if status_atual == "bloqueado" else "bloqueado"
                    db.collection("familias").document(usuario_token).set({
                        "membros": {nome_alvo: novo_status}
                    }, merge=True)
                    popup_lider.open = False
                    page.snack_bar = ft.SnackBar(ft.Text(f"Status de {nome_alvo} alterado para {novo_status.upper()}!"), bgcolor="blue")
                    page.snack_bar.open = True
                    page.update()

                lista_ui.controls.append(
                    ft.Row([
                        ft.Column([ft.Text(m_nome, weight="bold"), ft.Text(txt_status, color=cor_status, size=12)]),
                        ft.IconButton(icon=icone_btn, icon_color=cor_btn, on_click=alterar_status)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )

            if not lista_ui.controls:
                lista_ui.controls.append(ft.Text("Nenhum membro na família ainda.", color="grey"))

            popup_lider.content = lista_ui
            popup_lider.open = True
            page.update()

        popup_lider = ft.AlertDialog(title=ft.Text("👑 Membros do Clã"), content=ft.Column(), actions=[ft.TextButton("Fechar", on_click=lambda e: fechar_popup_lider(e))])
        def fechar_popup_lider(e):
            popup_lider.open = False
            page.update()
            
        page.overlay.append(popup_lider)

        # O Botão que só aparece se for o Líder!
        botao_admin = ft.IconButton(icon=ft.Icons.ADMIN_PANEL_SETTINGS, icon_color="blue", tooltip="Gerenciar Clã", on_click=abrir_painel_lider, visible=eh_lider)
        
        # Agrupamos as boas-vindas e o crachá juntos
        # Agrupamos as boas-vindas, o crachá e o Botão do Líder!
        cabecalho_usuario = ft.Column([
            texto_boas_vindas, 
            ft.Row([badge_token, botao_admin], spacing=5) # <--- Botão entrou aqui!
        ], spacing=2)
        texto_renda_total = ft.Text("R$ 0,00", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
        coluna_detalhes_renda = ft.Column(spacing=2) 
        texto_total_a_pagar = ft.Text("R$ 0,00", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700)
        texto_saldo_real = ft.Text("R$ 0,00", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
        texto_alerta_financeiro = ft.Text("", color=ft.Colors.RED_700, weight=ft.FontWeight.BOLD)
        # --- 🧾 NOVO PAINEL DE RESUMO FINANCEIRO PREMIUM ---
        # Definimos os sub-componentes primeiro para facilitar a montagem
        texto_sobra_mes_anterior = ft.Text("", size=11, color=ft.Colors.GREY_600)
        
        # Sub-cartão de Renda Familiar
        ui_renda_familia = criar_cartao_premium(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, color=ft.Colors.GREEN, size=28),
                    ft.Text("Renda Familiar", weight="bold", size=17),
                    ft.IconButton(icon=ft.icons.Icons.EXIT_TO_APP, icon_color="red", on_click=sair_do_app, scale=1.1)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                texto_renda_total,
                coluna_detalhes_renda, # Isso já tem a lógica de líquido, continua igual
            ], spacing=8)
        )
        cartao_total_a_pagar = criar_cartao_premium(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.Icons.CHECKLIST, color=ft.Colors.ORANGE_800, size=26),
                    ft.Text("Total a Pagar", weight="bold", size=13, expand=True),
                ], spacing=4, alignment=ft.MainAxisAlignment.START, height=50),
                texto_total_a_pagar # Valor calculado anteriormente
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.START),
            elevation=2 
        )
        cartao_saldo_real = criar_cartao_premium(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WALLET_OUTLINED, color=ft.Colors.BLUE, size=20),
                    ft.Text("Livre após contas", weight="bold", size=15),
                ], spacing=0, margin=8, alignment=ft.MainAxisAlignment.START),
                
                # 👇 Agrupamos o valor e a sobra aqui 👇
                ft.Column([
                    texto_saldo_real,
                    texto_sobra_mes_anterior # O texto pequeno entra aqui!
                ], spacing=0)
                
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.START),
            elevation=2 
        )

        painel_resumo = ft.Column([
            ft.Text("Resumo Financeiro", weight="bold", size=22),
            ui_renda_familia, 
            ft.Divider(color=ft.Colors.GREY_300, height=10), 
            ft.Row([
                cartao_total_a_pagar, 
                cartao_saldo_real
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=10) 
        ], spacing=0, margin=8)

        # Cartões de "Total a Pagar" e "Saldo Real Disponível" lado a lado (Row)
        



        linha_cartao_financeiros = ft.Row([
            ft.Container(content=cartao_total_a_pagar, expand=True, bgcolor=ft.Colors.GREY_100),
            ft.Container(content=cartao_saldo_real, expand=True, bgcolor=ft.Colors.GREY_100)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

        linha_cartao_financeiros = ft.Container(
            content=linha_cartao_financeiros,
            padding=10,
            border_radius=10,
            bgcolor=ft.Colors.GREY_100
        )

        # Montagem do Painel de Resumo Final (Agora guarda só a Renda)
        painel_resumo = ft.Column([
            ft.Text("Resumo Financeiro", weight="bold", size=22),
            ui_renda_familia 
        ], spacing=10)

        # --- ⚠️ ALERTA FINANCEIRO PREMIUM (Banner Rosa Clarinho) ---
        cartao_alerta_financeiro = ft.Container(
            border_radius=ft.border_radius.all(12),
            padding=ft.padding.only(left=15, right=15, top=8, bottom=8),
            bgcolor=ft.Colors.RED_50, # Fundo rosa claro igual da referência
            content=ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER_OUTLINED, color=ft.Colors.RED_900), 
                texto_alerta_financeiro # Texto redado anteriormente
            ], spacing=10),
            visible=False # Nasce invisível
        )

        def alternar_tema(e):
            page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
            botao_tema.icon = ft.icons.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.icons.Icons.LIGHT_MODE
            page.update()

        botao_tema = ft.IconButton(
            icon=ft.icons.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.icons.Icons.LIGHT_MODE,
            on_click=alternar_tema, tooltip="Mudar Tema"
        )

        # ==========================================================
        # 🟢 PASSO 2: O CONSULTOR DE PIS 
        # ==========================================================
        cartao_pis = criar_cartao_premium(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.Icons.SAVINGS, color=ft.Colors.ORANGE, size=30),
                    ft.Text("Consultor de PIS/Abono", weight="bold", size=18),
                ], alignment=ft.MainAxisAlignment.START, spacing=10),
                ft.Text(mensagem_pis, size=15, color=ft.Colors.GREEN if tem_5_anos else ft.Colors.RED_900),
            ], spacing=10)
        )

        # ==========================================================
        # 🟢 PASSO 4: PAINEL DE RESUMO FINAL E ALERTA
        # ==========================================================
        painel_resumo = ft.Column([
            ft.Text("Resumo Financeiro", weight="bold", size=22),
            ui_renda_familia 
            # Arrancamos o ft.Divider e o ft.Row que estavam aqui criando os clones!
        ], spacing=10)

        cartao_alerta_financeiro = ft.Container(
            border_radius=ft.border_radius.all(12),
            padding=ft.padding.only(left=15, right=15, top=8, bottom=8),
            bgcolor=ft.Colors.RED_50, 
            content=ft.Row([
                ft.Icon(ft.icons.Icons.WARNING_AMBER_OUTLINED, color=ft.Colors.RED_900), 
                texto_alerta_financeiro 
            ], spacing=10),
            visible=False 
        )

        cores_categorias = {"Alimentação / Supermercado": "blue", "Habitação (Renda, Água, Luz)": "red", "Transporte": "green", "Lazer": "purple", "Outros": "orange"}
        legenda_grafico = ft.Column(spacing=10) 
        painel_grafico = ft.Card(content=ft.Container(content=legenda_grafico, padding=15), visible=False)

        def formatar_data_vencimento(e):
            numeros = "".join(filter(str.isdigit, e.control.value))
            texto_formatado = numeros
            if len(numeros) > 2:
                texto_formatado = f"{numeros[:2]}/{numeros[2:]}"
            if len(numeros) > 4:
                texto_formatado = f"{numeros[:2]}/{numeros[2:4]}/{numeros[4:8]}"
            e.control.value = texto_formatado
            e.control.update()

       # --- CAMPOS PREMIUM (Com texto sempre preto para não sumir no Dark Mode!) ---
        input_renda = ft.TextField(label="Atualizar meu Salário (R$)", expand=True, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, bgcolor=ft.Colors.WHITE, border_color="#D1D9E6", color="black")
        
        descricao_input = ft.TextField(label="Insira uma descrição", border_radius=10, bgcolor=ft.Colors.WHITE, border_color="#D1D9E6", prefix_icon=ft.Icons.EDIT_OUTLINED, color="black")
        valor_input = ft.TextField(label="Valor Gasto (R$)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, bgcolor=ft.Colors.WHITE, border_color="#D1D9E6", prefix_icon=ft.Icons.ATTACH_MONEY, color="black")
        
        # Dropdowns com cor travada
        categoria_dropdown = ft.Dropdown(
            label="Categoria", border_radius=10, bgcolor=ft.Colors.WHITE, border_color="#D1D9E6", expand=True, color="black",
            options=[ft.dropdown.Option(c) for c in cores_categorias.keys()] + [ft.dropdown.Option("Cartão de Crédito")]
        )
        linha_cat = ft.Row([ft.Icon(ft.Icons.LOCAL_OFFER_OUTLINED, color=ft.Colors.GREY_500), categoria_dropdown])
        
        # 1. A FUNÇÃO NASCE PRIMEIRO
        def verificar_forma_pagamento(e):
            if e.control.value == "Cartão de Crédito":
                linha_cartao.visible = True
            else:
                linha_cartao.visible = False
                dropdown_qual_cartao.value = "Não se aplica" 
            e.control.page.update()

        # 2. O DROPDOWN DO CARTÃO NASCE INVISÍVEL
        dropdown_qual_cartao = ft.Dropdown(
            label="Qual Cartão?", value="Não se aplica", border_radius=10, 
            bgcolor="white", border_color="#D1D9E6", expand=True, color="black",
            options=[
                ft.dropdown.Option("Não se aplica"), ft.dropdown.Option("Brasil Card"), ft.dropdown.Option("Banco Inter"), 
                ft.dropdown.Option("Nubank"), ft.dropdown.Option("Santander"), ft.dropdown.Option("Itaú"), 
                ft.dropdown.Option("Bradesco"), ft.dropdown.Option("Caixa Econômica"), ft.dropdown.Option("Outro")
            ]
        )

        linha_cartao = ft.Row(
            [ft.Icon(ft.Icons.CREDIT_CARD, color="grey"), dropdown_qual_cartao],
            visible=False 
        )

        # 3. O DROPDOWN PRINCIPAL (Com o evento certo para a v0.82+)
        forma_pagamento_dropdown = ft.Dropdown(
            label="Forma de Pagamento", border_radius=10, 
            bgcolor="white", border_color="#D1D9E6", expand=True, color="black",
            options=[ft.dropdown.Option("Pix"), ft.dropdown.Option("Cartão de Crédito"), ft.dropdown.Option("Dinheiro")],
            on_select=verificar_forma_pagamento # <--- A MÁGICA DA VERSÃO 0.82 AQUI!
        )
        linha_forma = ft.Row([ft.Icon(ft.Icons.PAYMENT_OUTLINED, color="grey"), forma_pagamento_dropdown])

        # 2. O Dropdown do Cartão 
        dropdown_qual_cartao = ft.Dropdown(
            label="Qual Cartão?", value="Não se aplica", border_radius=10, bgcolor=ft.Colors.WHITE, border_color="#D1D9E6", expand=True, color="black",
            options=[
                ft.dropdown.Option("Não se aplica"), ft.dropdown.Option("Brasil Card"), ft.dropdown.Option("Banco Inter"), 
                ft.dropdown.Option("Nubank"), ft.dropdown.Option("Santander"), ft.dropdown.Option("Itaú"), 
                ft.dropdown.Option("Bradesco"), ft.dropdown.Option("Caixa Econômica"), ft.dropdown.Option("Outro")
            ]
        )
        
        # 3. A linha que guarda o cartão NASCE INVISÍVEL!
        linha_cartao = ft.Row(
            [ft.Icon(ft.Icons.CREDIT_CARD, color=ft.Colors.GREY_500), dropdown_qual_cartao],
            visible=False # <--- O SEGREDO DO VISUAL LIMPO!
        )
        
        # Parcelas e Vencimentos com cor travada
        input_parcelas = ft.TextField(label="Qtd Parcelas", value="1", expand=True, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, bgcolor=ft.Colors.WHITE, border_color="#D1D9E6", prefix_icon=ft.Icons.LAYERS, color="black")
        input_vencimento = ft.TextField(label="Vencimento", expand=True, prefix_icon=ft.Icons.CALENDAR_MONTH_ROUNDED, keyboard_type=ft.KeyboardType.NUMBER, on_change=formatar_data_vencimento, max_length=10, counter="", border_radius=10, bgcolor=ft.Colors.WHITE, border_color="#D1D9E6", color="black")
        linha_opcionais = ft.Row([input_parcelas, input_vencimento], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        

        # 👇 AS DUAS CHAVINHAS (Agora organizadas uma embaixo da outra!) 👇
        
        checkbox_mes_passado = ft.Switch(label="⏳ Mês Passado?", value=False, active_color=ft.Colors.TEAL_400)
        checkbox_recorrente = ft.Switch(label="🔄 Conta Fixa?", value=False, active_color=ft.Colors.BLUE_400)
        
        # Colocamos elas lado a lado (como o texto tá curto, agora cabe e fica lindo!)
        linha_botoes = ft.Row([checkbox_mes_passado, checkbox_recorrente], alignment=ft.MainAxisAlignment.SPACE_AROUND)
        
        # O seu Container chique envolvendo as chaves!
        linha_switch = ft.Container(
            content=linha_botoes,
            padding=10,
            border_radius=10,
            bgcolor=ft.Colors.GREY_100
        )

        lista_gastos_atual = ft.Column()
        lista_historico_meses = ft.Column()
        lista_de_listas_salvas = ft.Column() 

        ecra_inicio = ft.Column(visible=True)
        ecra_compras = ft.Column(visible=False)
        ecra_listas_salvas = ft.Column(visible=False)
        ecra_historico = ft.Column(visible=False)
        ecra_financeiro = ft.Column(visible=False)

        def apagar_gasto(doc_id):
            db.collection("gastos").document(doc_id).delete()
            page.snack_bar = ft.SnackBar(ft.Text("Registro eliminado!"))
            page.snack_bar.open = True
            carregar_dados()
            page.update()

        def apagar_lista(doc_id):
            db.collection("listas_compras").document(doc_id).delete()
            page.snack_bar = ft.SnackBar(ft.Text("Lista apagada!"))
            page.snack_bar.open = True
            carregar_dados()
            page.update()

        def lancar_lista_como_gasto(doc_id, lista_dados):
            hoje = datetime.date.today()
    
            # 🔥 A NOSSA TRAVA DE INTELIGÊNCIA ENTRA AQUI 🔥
            if forma_pagamento_dropdown.value == "Cartão de Crédito" or dropdown_banco.value == "Banco Inter": 
                status_correto = "pendente"
            else:
                status_correto = "pago" 

            # Quando for montar os dados para o Firebase, também use o .value:
            dados_novo_gasto = {
                # ...
                "forma_pagamento": forma_pagamento_dropdown.value if forma_pagamento_dropdown.value else "Não informado",
                "status": status_correto,
    }
            db.collection("gastos").add({
                "descricao": "Compra de Mercado (Lista Salva)", "valor": lista_dados.get("total_previsto", 0),
                "categoria": "Alimentação / Supermercado", "forma_pagamento": "Não informado",
                "quem_pagou": nome_usuario, "data": hoje.strftime("%d/%m/%Y"), "mes_ano": hoje.strftime("%m/%Y"),
                "data_registro": firestore.SERVER_TIMESTAMP, "itens_detalhados": lista_dados.get("itens", [])
            })
            db.collection("listas_compras").document(doc_id).delete()
            page.snack_bar = ft.SnackBar(ft.Text("🛒 Lista lançada nas despesas com sucesso!"))
            page.snack_bar.open = True
            carregar_dados()
            page.update()

        # ====================================================================
        # 🎨 TELA DE HISTÓRICO VISUAL (COM FILTRO DE CARTÕES!) 🎨
        # ====================================================================
        def ver_detalhes_mes(mes_selecionado):
            lista_historico_meses.controls.clear()
            id_mes_busca = mes_selecionado.replace("/", "_")
            
            # 1. Puxa a Renda daquele mês específico
            doc_renda_velha = db.collection("resumo").document(id_mes_busca).get()
            renda_epoca = doc_renda_velha.to_dict().get("renda", 0.0) if doc_renda_velha.exists else 0.0
            
            if renda_epoca == 0.0:
                renda_atual_temp = 0.0
                docs_rendas_temp = db.collection("rendas").stream()
                for doc_r in docs_rendas_temp:
                    renda_atual_temp += doc_r.to_dict().get("valor", 0.0)
                renda_epoca = renda_atual_temp

            # 🧠 INTELIGÊNCIA DOS CARTÕES: Preparando os dados
            totais_cartoes = {}
            dados_do_mes = []

            # Varre o banco de dados UMA VEZ e guarda na memória para o filtro ficar rápido
            docs = db.collection("gastos").where("mes_ano", "==", mes_selecionado).stream()
            for doc in docs:
                d = doc.to_dict()
                d['id'] = doc.id
                dados_do_mes.append(d)
                
                # Soma os valores para criar o "Total da Fatura" de cada cartão
                cartao = d.get('cartao_usado', '')
                if cartao and cartao != "Não se aplica":
                    v = float(str(d.get('valor', 0)).replace(',', '.'))
                    totais_cartoes[cartao] = totais_cartoes.get(cartao, 0.0) + v

            # O container onde as compras vão aparecer
            coluna_itens_filtrados = ft.Column()

            # 🎯 FUNÇÃO DE FILTRAGEM: Desenha a lista dependendo do que você escolheu
            def renderizar_lista(filtro="Todos"):
                coluna_itens_filtrados.controls.clear()
                
                for d in dados_do_mes:
                    cartao_usado = d.get('cartao_usado', '')
                    
                    # Se o filtro não for "Todos" e o cartão não bater, pula esse gasto!
                    if filtro != "Todos" and cartao_usado != filtro:
                        continue
                        
                    # --- MONTAGEM DO CARTÃO (Já com a correção de quebrar linha!) ---
                    v = float(str(d.get('valor', 0)).replace(',', '.'))
                    status = d.get('status', 'pendente')
                    data_reg = d.get('data', 'Sem data')
                    desc = d.get('descricao', 'Sem nome')
                    venc = d.get('data_vencimento', '')
                    forma_pagamento = d.get('forma_pagamento', '')
                    data_pagamento = d.get('data_pagamento', '') 
                    
                    banco_pag = d.get('banco_pagamento', '')
                    metodo_pag = d.get('forma_pagamento_real', forma_pagamento) 
                    
                    if status == "pago":
                        info_data = f" em {data_pagamento}" if data_pagamento else ""
                        if banco_pag: txt_forma = f"via {metodo_pag} ({banco_pag})"
                        elif cartao_usado and cartao_usado != "Não se aplica": txt_forma = f"via {metodo_pag} ({cartao_usado})"
                        else: txt_forma = f"via {metodo_pag}"
                            
                        status_ui = ft.Text(f"✅ Pago{info_data}", color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD, size=13, text_align=ft.TextAlign.RIGHT)
                        info_pagamento_ui = ft.Text(f"💳 {txt_forma}", color=ft.Colors.GREEN_700, size=11, weight=ft.FontWeight.BOLD)
                        cor_valor = ft.Colors.GREY_500
                    else: 
                        status_ui = ft.Text("⏳ Pendente", color=ft.Colors.ORANGE_400, weight=ft.FontWeight.BOLD, size=13)
                        info_pagamento_ui = ft.Container()
                        cor_valor = ft.Colors.RED_400

                    venc_ui = ft.Text(f"📅 Vence em: {venc}" if venc else "", color=ft.Colors.BLUE_300, size=12, weight="bold")

                    coluna_info = ft.Column([
                        ft.Row([
                            ft.Text(f"[{data_reg}] {desc}", weight=ft.FontWeight.BOLD, size=15, expand=True), # Expand=True salva a tela!
                            status_ui
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START),
                        
                        info_pagamento_ui, 
                        ft.Text(f"R$ {v:.2f}", color=cor_valor, size=14, weight=ft.FontWeight.BOLD),
                        venc_ui if venc else ft.Container()
                    ], spacing=3)

                    if "itens_detalhados" in d and len(d["itens_detalhados"]) > 0:
                        # Adicionamos o (R$ ...) puxando o item.get('preco') que já estava salvo na nuvem!
                        str_itens = " • " + "\n • ".join([f"{item['qtd']}x {item['nome']} (R$ {item.get('preco', 0):.2f})" for item in d["itens_detalhados"]])
                        coluna_info.controls.append(ft.Text(f"Itens do Mercado:\n{str_itens}", size=11, color=ft.Colors.GREY_700))

                    coluna_itens_filtrados.controls.append(criar_cartao_premium(coluna_info, elevation=2))
                
                page.update()

            # --- CABEÇALHO DA TELA DE MESES ---
            resumo_faturas_ui = ft.Column(spacing=2)
            opcoes_filtro = [ft.dropdown.Option("Todos")]
            
            # Se achou algum cartão usado no mês, cria o Mini-Dashboard!
            if totais_cartoes:
                resumo_faturas_ui.controls.append(ft.Text("📊 Faturas de Cartão (Neste Mês):", weight="bold", size=14))
                for c_nome, c_total in totais_cartoes.items():
                    resumo_faturas_ui.controls.append(ft.Text(f"💳 {c_nome}: R$ {c_total:.2f}", color=ft.Colors.BLUE_700, weight="bold"))
                    opcoes_filtro.append(ft.dropdown.Option(c_nome))
            else:
                resumo_faturas_ui.controls.append(ft.Text("Nenhuma fatura de cartão para este mês.", color=ft.Colors.GREY))

            dropdown_filtro = ft.Dropdown(
                label="Filtrar lançamentos por cartão...",
                options=opcoes_filtro,
                value="Todos",
                border_radius=10,
                on_text_change=lambda e: renderizar_lista(e.control.value) # Chama o filtro ao mudar!
            )

            cabecalho_mes = ft.Column([
                ft.Row([ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: carregar_dados()), ft.Text(f"Lançamentos de {mes_selecionado}", size=20, weight="bold")]),
                ft.Text(f"Renda base na época: R$ {renda_epoca:.2f}", color=ft.Colors.BLUE_400, weight="bold"), 
                ft.Divider(),
                criar_cartao_premium(resumo_faturas_ui, elevation=1), # Caixinha Premium pro Resumo
                dropdown_filtro,
                ft.Divider(),
                coluna_itens_filtrados # A lista renderizada entra aqui no final!
            ])

            lista_historico_meses.controls.append(cabecalho_mes)
            
            # Chama a função para desenhar a lista completa ("Todos") na primeira vez que abre a tela
            renderizar_lista("Todos")

        def calcular_parcelas_pagas(mes_ano_inicio):
            try:
                mes_ini, ano_ini = map(int, mes_ano_inicio.split('/'))
                hoje = datetime.date.today()
                return max(0, ((hoje.year - ano_ini) * 12 + (hoje.month - mes_ini)) + 1)
            except: return 0

        dropdown_banco = ft.Dropdown(
            label="Qual Banco?",
            options=[
                ft.dropdown.Option("Banco Inter"), 
                ft.dropdown.Option("Nubank"), 
                ft.dropdown.Option("Caixa Econômica"), 
                ft.dropdown.Option("Banco do Brasil"), 
                ft.dropdown.Option("Itaú"), 
                ft.dropdown.Option("Santander"),     # <--- AQUI TAMBÉM
                ft.dropdown.Option("Bradesco"),
                ft.dropdown.Option("Outro")
            ]
        )
        dropdown_metodo_novo = ft.Dropdown(
            label="Forma de Pagamento",
            options=[
                ft.dropdown.Option("Pix"), ft.dropdown.Option("Boleto/Código de Barras"), 
                ft.dropdown.Option("Cartão de Crédito"), ft.dropdown.Option("Débito Automático")
            ]
        )
        
        id_gasto_atual = [None] 

        def confirmar_pagamento(e):
            if not dropdown_banco.value or not dropdown_metodo_novo.value: return
            
            doc_id = id_gasto_atual[0]
            from datetime import datetime
            hoje_str = datetime.now().strftime("%d/%m/%Y")
            
            # 1. Puxa os dados da conta antes de pagar ela
            doc_ref = db.collection("gastos").document(doc_id)
            doc_atual = doc_ref.get().to_dict()
            
            # 2. Atualiza a conta ATUAL para paga!
            doc_ref.update({
                "status": "pago",
                "banco_pagamento": dropdown_banco.value,
                "forma_pagamento_real": dropdown_metodo_novo.value,
                "data_pagamento": hoje_str
            })
            
            # 🔥 3. A LÓGICA DO OSMAR: CLONAGEM AUTOMÁTICA 🔥
            if doc_atual.get("recorrente") == True:
                # Calcula o mês que vem
                m_atual, a_atual = map(int, doc_atual["mes_ano"].split('/'))
                m_prox = m_atual + 1
                a_prox = a_atual
                if m_prox > 12:
                    m_prox = 1
                    a_prox += 1
                mes_ano_futuro = f"{m_prox:02d}/{a_prox}"
                
                # Calcula a data de vencimento do mês que vem (se tiver)
                venc_futuro = ""
                venc_atual = doc_atual.get("data_vencimento", "")
                if venc_atual:
                    try:
                        d_v, m_v, a_v = map(int, venc_atual.split('/'))
                        m_v += 1
                        if m_v > 12:
                            m_v = 1; a_v += 1
                        venc_futuro = f"{d_v:02d}/{m_v:02d}/{a_v}"
                    except: pass
                
                # Joga a conta clonada pro futuro, já como PENDENTE!
                db.collection("gastos").add({
                    "token_familia": doc_atual.get("token_familia"),
                    "descricao": doc_atual.get("descricao"),
                    "valor": doc_atual.get("valor"),
                    "categoria": doc_atual.get("categoria"),
                    "forma_pagamento": doc_atual.get("forma_pagamento"),
                    "cartao_usado": doc_atual.get("cartao_usado"),
                    "quem_pagou": doc_atual.get("quem_pagou"),
                    "data": hoje_str, # Data que o clone nasceu
                    "mes_ano": mes_ano_futuro, # 👈 Viagem no tempo!
                    "data_registro": firestore.SERVER_TIMESTAMP,
                    "status": "pendente",
                    "data_vencimento": venc_futuro,
                    "recorrente": True # Passa o DNA da recorrência pra frente!
                })
            
            popup_pagamento.open = False
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ Conta paga! E se for fixa, o mês que vem já tá gerado!"))
            page.snack_bar.open = True
            page.update()
            carregar_dados()

        def fechar_popup(e):
            popup_pagamento.open = False
            page.update()

        popup_pagamento = ft.AlertDialog(
            title=ft.Text("Confirmar Pagamento"),
            content=ft.Column([
                ft.Text("De onde o dinheiro saiu?"),
                dropdown_banco,
                dropdown_metodo_novo
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_popup),
                ft.ElevatedButton("Confirmar Pagamento", on_click=confirmar_pagamento, bgcolor="green", color="white")
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(popup_pagamento)

        def abrir_popup_pagamento(doc_id):
            id_gasto_atual[0] = doc_id
            dropdown_banco.value = None
            dropdown_metodo_novo.value = None
            popup_pagamento.open = True
            page.update()
        
        # =======================================================
        # ✏️ SISTEMA DE EDIÇÃO DE GASTOS (O "U" DO CRUD)
        # =======================================================
        id_gasto_editar = [None] # Guarda o ID da conta que estamos mexendo

        edit_desc = ft.TextField(label="Descrição", border_radius=10, color="black", bgcolor="white")
        edit_valor = ft.TextField(label="Valor (R$)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, color="black", bgcolor="white")

        def fechar_popup_editar(e):
            popup_editar.open = False
            page.update()

        def salvar_edicao(e):
            if not edit_desc.value or not edit_valor.value: return
            try:
                novo_valor = float(edit_valor.value.replace(',', '.'))
                # Atualiza SÓ o que foi editado lá no Firebase
                db.collection("gastos").document(id_gasto_editar[0]).update({
                    "descricao": edit_desc.value.strip(),
                    "valor": novo_valor
                })
                popup_editar.open = False
                page.snack_bar = ft.SnackBar(ft.Text("✅ Gasto atualizado com sucesso!"), bgcolor="green")
                page.snack_bar.open = True
                carregar_dados() # Recarrega a tela para mostrar o valor novo
                page.update()
            except Exception as erro:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao editar: {erro}"), bgcolor="red")
                page.snack_bar.open = True
                page.update()

        popup_editar = ft.AlertDialog(
            title=ft.Text("✏️ Editar Gasto"),
            content=ft.Column([
                ft.Text("Corrija os dados abaixo:", color="grey"),
                edit_desc, 
                edit_valor
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_popup_editar),
                ft.ElevatedButton("Salvar Alterações", on_click=salvar_edicao, bgcolor="blue", color="white")
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(popup_editar)

        # O Gatilho que preenche os dados e abre a tela
        def abrir_edicao(doc_id, desc_atual, valor_atual):
            id_gasto_editar[0] = doc_id
            edit_desc.value = desc_atual
            edit_valor.value = str(valor_atual).replace('.', ',') # Volta a vírgula pro BR ler
            popup_editar.open = True
            page.update()

        # --- FUNÇÃO PRINCIPAL CARREGAR DADOS ---
        def carregar_dados():
            lista_gastos_atual.controls.clear()
            lista_historico_meses.controls.clear()
            lista_de_listas_salvas.controls.clear() 
            lista_consignados_ui.controls.clear()
            lista_metas_ui.controls.clear()

            docs_metas = db.collection("metas").where("token_familia", "==", usuario_token).stream()
            for doc in docs_metas:
                d_meta = doc.to_dict()
                doc_id = doc.id
                m_nome = d_meta.get("nome", "Sonho")
                m_total = float(d_meta.get("valor_total", 1.0))
                m_guardado = float(d_meta.get("valor_guardado", 0.0))
                m_alvo = d_meta.get("data_alvo", "Sem prazo")
                
                historico_depositos = d_meta.get("historico", [])
                pct = m_guardado / m_total if m_total > 0 else 0
                pct_exibicao = max(0.0, min(1.0, pct)) 
                
                texto_progresso = f"Guardado: R$ {m_guardado:.2f} de R$ {m_total:.2f} ({pct*100:.1f}%)"
                campo_deposito = ft.TextField(label="R$", width=90, height=45, text_size=12, keyboard_type=ft.KeyboardType.NUMBER)
                
                def criar_evento_deposito(id_doc, guardado_atual, campo_input, hist_atual):
                    def acao_depositar(e):
                        if not campo_input.value: return
                        try:
                            v_deposito = float(campo_input.value.replace(',', '.'))
                            hoje_str = datetime.date.today().strftime("%d/%m/%Y")
                            novo_registro = {"data": hoje_str, "valor": v_deposito}
                            hist_atual.append(novo_registro)

                            db.collection("metas").document(id_doc).update({
                                "valor_guardado": guardado_atual + v_deposito,
                                "historico": hist_atual
                            })
                            carregar_dados()
                            page.update()
                        except: pass
                    return acao_depositar

                botao_deposito = ft.IconButton(icon=ft.icons.Icons.ADD_CIRCLE, icon_color="green", tooltip="Depositar", on_click=criar_evento_deposito(doc_id, m_guardado, campo_deposito, historico_depositos))

                def criar_evento_apagar(id_doc):
                    def acao_apagar(e):
                        db.collection("metas").document(id_doc).delete()
                        page.snack_bar = ft.SnackBar(ft.Text("🗑️ Sonho excluído com sucesso!"))
                        page.snack_bar.open = True
                        carregar_dados() 
                        page.update()
                    return acao_apagar

                botao_apagar_meta = ft.IconButton(icon=ft.icons.Icons.DELETE, icon_color="red", tooltip="Excluir Sonho", on_click=criar_evento_apagar(doc_id))
                
                ui_historico = ft.Column(spacing=2)
                if historico_depositos:
                    ui_historico.controls.append(ft.Text("Extrato de Depósitos:", size=12, weight="bold"))
                    for reg in historico_depositos:
                        ui_historico.controls.append(ft.Text(f"📥 R$ {reg['valor']:.2f} guardados no dia {reg['data']}", size=11, color="grey"))
                
                # Substitua o cartao_meta antigo por este:
                cartao_meta = criar_cartao_premium(
                    ft.Column([
                        ft.Row([
                            ft.Text(texto_progresso, size=13, color="blue", weight="bold"),
                            ft.Row([ft.Text(f"Prazo: {m_alvo}", color="orange", weight="bold", size=12), botao_apagar_meta], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.ProgressBar(value=pct_exibicao, color="green", bgcolor="#e0e0e0", height=12),
                        ft.Row([campo_deposito, botao_deposito], alignment=ft.MainAxisAlignment.END),
                        ft.Divider(color="transparent", height=5), ui_historico
                    ], spacing=8), 
                    elevation=3
                )
                lista_metas_ui.controls.append(cartao_meta)
            
            total_despesas_mes_atual = 0.0
            gastos_por_categoria = {} 
            docs_consig = db.collection("consignados").where("token_familia", "==", usuario_token).stream()
            total_desconto_consig = 0.0
            descontos_por_usuario = {}
            
            for doc in docs_consig:
                dados_c = doc.to_dict()
                doc_id = doc.id
                valor_parcela_consig = dados_c.get("valor_parcela", 0.0)
                total_p = dados_c.get("total_parcelas", 0)
                inicio_p = dados_c.get("mes_ano_inicio", "")
                dono_consig = dados_c.get("dono", "Desconhecido")
                pagas = calcular_parcelas_pagas(inicio_p)

                try:
                    total_p = dados_c.get("total_parcelas") or dados_c.get("parcelas") or 0
                    total_p = int(total_p)
                    mes_ini, ano_ini = map(int, inicio_p.split('/'))
                    hoje = datetime.date.today()
                    meses_passados = (hoje.year - ano_ini) * 12 + (hoje.month - mes_ini)
                    
                    if hoje.day < 20: pagas = meses_passados
                    else: pagas = meses_passados + 1 
                    
                    pagas = max(0, min(pagas, total_p))
                    faltam = total_p - pagas
                    
                    # --- 🛑 NOVO: A TRAVA DO FUTURO ---
                    inicia_no_futuro = False
                    # Se o mês de início for maior que o mês atual (meses_passados < 0)
                    # OU se for o mês atual mas ainda não chegou o dia 20:
                    if meses_passados < 0 or (meses_passados == 0 and hoje.day < 20):
                        inicia_no_futuro = True

                except Exception as e:
                    total_p = 0
                    faltam = 0
                    inicia_no_futuro = False

                # --- 🧠 LÓGICA DE EXIBIÇÃO INTELIGENTE ---
                if total_p > 0 and faltam <= 0:
                    status_txt = "Quitado! 🎉"
                    cor_status = ft.Colors.GREEN
                elif inicia_no_futuro:
                    # Se começa no futuro, avisa na tela, mas NÃO SOMA o desconto no salário!
                    status_txt = f"Começa em: {inicio_p} ⏳"
                    cor_status = ft.Colors.BLUE
                elif total_p > 0:
                    status_txt = f"Pagas: {pagas} | Faltam: {faltam}"
                    cor_status = ft.Colors.ORANGE
                    # Só debita do salário se já estiver ativo!
                    total_desconto_consig += valor_parcela_consig
                    descontos_por_usuario[dono_consig] = descontos_por_usuario.get(dono_consig, 0.0) + valor_parcela_consig
                else:
                    status_txt = "Configuração incompleta"
                    cor_status = ft.Colors.RED

                # Substitua o item_consig antigo por este:
                item_consig = criar_cartao_premium(
                    ft.Row([
                        ft.Column([ft.Text(f"👤 {dono_consig}", weight=ft.FontWeight.BOLD), ft.Text(f"Parcela: R$ {valor_parcela_consig:.2f}"), ft.Text(status_txt, color=cor_status)], expand=True),
                        ft.IconButton(icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, id=doc_id: apagar_consignado(id))
                    ]), elevation=2
                )
                lista_consignados_ui.controls.append(item_consig)

            if total_desconto_consig > 0:
                texto_alerta_financeiro.value = f"Atenção: R$ {total_desconto_consig:.2f} comprometidos com empréstimos."
                cartao_alerta_financeiro.visible = True
            else: cartao_alerta_financeiro.visible = False

            docs_rendas = db.collection("rendas").where("token_familia", "==", usuario_token).stream()
            renda_total_familiar = 0.0
            total_pendente_geral = 0.0 
            total_pago_geral = 0.0 # <--- AQUI NASCE A VARIÁVEL DE GASTOS PAGOS
            textos_detalhe = []

            # ... (dentro de carregar_dados)
            for doc in docs_rendas:
                dono_renda = doc.id
                valor_renda = doc.to_dict().get("valor", 0.0)
                desconto_dele = descontos_por_usuario.get(dono_renda, 0.0)

                # --- 🔥 A MATEMÁTICA DO LÍQUIDO AQUI ---
                liquido = valor_renda - desconto_dele
                
                # A renda familiar AGORA É O LÍQUIDO (já descontando o consignado)!
                renda_total_familiar += liquido
                
                if desconto_dele > 0:
                    texto = f"👤 {dono_renda}: R$ {valor_renda:.2f} | Consig: -R$ {desconto_dele:.2f} ➡️ Líquido: R$ {liquido:.2f}"
                else:
                    texto = f"👤 {dono_renda}: R$ {valor_renda:.2f}"
                    
                textos_detalhe.append(ft.Text(texto, size=13, color=ft.Colors.GREY_700))

            texto_renda_total.value = f"R$ {renda_total_familiar:.2f}"
            coluna_detalhes_renda.controls = textos_detalhe

            todos_docs = db.collection("gastos").where("token_familia", "==", usuario_token).order_by("data_registro", direction=firestore.Query.DESCENDING).stream()
            gastos_por_mes = {}
            detalhes_por_categoria = {} # <--- ADICIONE ESTA LINHA!

            hoje_data = datetime.date.today()
            dia_hoje = hoje_data.day
            mes_hoje = hoje_data.month
            ano_hoje = hoje_data.year
            mes_anterior = mes_hoje - 1 if mes_hoje > 1 else 12
            ano_anterior = ano_hoje if mes_hoje > 1 else ano_hoje - 1
            str_mes_passado = f"{mes_anterior:02d}/{ano_anterior}"

            for doc in todos_docs:
                dado = doc.to_dict()
                doc_id = doc.id
                v_num = float(str(dado.get('valor', 0)).replace(',', '.'))
                mes_ano_reg = dado.get("mes_ano", "Desconhecido")
                status = dado.get("status", "pendente")
                
                if status == "pendente":
                    if mes_ano_reg == mes_ano_atual or (mes_ano_reg == str_mes_passado and dia_hoje <= 10):
                        total_pendente_geral += v_num
                elif status == "pago" or status == "Pago":
                    # Somamos o dinheiro que JÁ SAIU DO BOLSO neste mês!
                    if mes_ano_reg == mes_ano_atual:
                        total_pago_geral += v_num

                gastos_por_mes[mes_ano_reg] = gastos_por_mes.get(mes_ano_reg, 0.0) + v_num

                # ==========================================
                # 🧠 O RADAR INTELIGENTE (MODO INBOX ZERO)
                # ==========================================
                mostrar_na_home = False
                texto_vencimento = ""

                # Regra 1: SOMA no gráfico se for deste mês, mas NÃO MOSTRA O CARTÃO automaticamente!
                if mes_ano_reg == mes_ano_atual:
                    total_despesas_mes_atual += v_num
                    cat = dado.get("categoria", "Outros")
                    gastos_por_categoria[cat] = gastos_por_categoria.get(cat, 0.0) + v_num
                    
                    if cat not in detalhes_por_categoria:
                        detalhes_por_categoria[cat] = []
                    
                    desc = dado.get("descricao", "Sem Nome")
                    cartao = dado.get("cartao_usado", "")
                    banco = dado.get("banco_pagamento", "")
                    info_extra = cartao if cartao and cartao != "Não se aplica" else banco
                    nome_exibicao = f"{desc} ({info_extra})" if info_extra else desc
                    detalhes_por_categoria[cat].append({"nome": nome_exibicao, "valor": v_num})

                # Regra 2: SÓ MOSTRA NA TELA INICIAL SE ESTIVER PENDENTE! 
                if status == "pendente":
                    mostrar_na_home = True 
                    
                    # Se for de outro mês, bota o aviso vermelho pra você saber!
                    if mes_ano_reg != mes_ano_atual:
                        texto_vencimento = f" ⚠️ (Mês: {mes_ano_reg})"

                # ==========================================      
                # OBS: Se não for deste mês e já estiver "pago", o mostrar_na_home continua False 
                # e a conta vai sumir da tela inicial e ficar guardada só na aba "Meses"!
                # ==========================================
                if mostrar_na_home:
                    vencimento_str = dado.get("data_vencimento", "")
                    alerta_vencimento = ""
                    cor_alerta = ft.Colors.GREY_700

                    if status == "pendente" and vencimento_str:
                        try:
                            dia_v, mes_v, ano_v = map(int, vencimento_str.split('/'))
                            data_venc = datetime.date(ano_v, mes_v, dia_v)
                            dias_restantes = (data_venc - hoje_data).days
                            if dias_restantes > 5:
                                alerta_vencimento = f"📅 Vence em {dias_restantes} dias"
                                cor_alerta = ft.Colors.BLUE
                            elif 0 < dias_restantes <= 5:
                                alerta_vencimento = f"⚠️ ATENÇÃO: Vence em {dias_restantes} dias!"
                                cor_alerta = ft.Colors.ORANGE_900
                            elif dias_restantes == 0:
                                alerta_vencimento = f"🚨 VENCE HOJE!"
                                cor_alerta = ft.Colors.RED
                            else:
                                alerta_vencimento = f"💀 ATRASADO HÁ {abs(dias_restantes)} DIAS!"
                                cor_alerta = ft.Colors.RED_900
                        except: pass

                    coluna_texto_cartao = ft.Column([
                        ft.Text(f"[{dado.get('data')}] {dado.get('descricao')}{texto_vencimento}", weight=ft.FontWeight.BOLD),
                        ft.Text(f"Lançado por: {dado.get('quem_pagou', '')} | R$ {v_num:.2f}", size=12),
                    ], spacing=2, expand=True)

                    if alerta_vencimento:
                        coluna_texto_cartao.controls.append(ft.Text(alerta_vencimento, color=cor_alerta, weight=ft.FontWeight.BOLD, size=13))

                    if status == "pago":
                        banco_usado = dado.get("banco_pagamento", "")
                        metodo_usado = dado.get("forma_pagamento_real", "")
                        data_pag = dado.get("data_pagamento", "") 
                        
                        texto_data = f" em {data_pag}" if data_pag else ""
                        texto_banco = f" ({banco_usado})" if banco_usado else ""
                        
                        # 1. A direita fica curtinha e direta!
                        controles_acao = ft.Text(f"✅ Pago{texto_data}", color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD, size=13, text_align=ft.TextAlign.RIGHT)
                        
                        # 2. Injetamos a informação do banco na coluna da esquerda (que sabe quebrar linha!)
                        coluna_texto_cartao.controls.append(
                            ft.Text(f"💳 via {metodo_usado}{texto_banco}", color=ft.Colors.GREEN_700, size=11, weight=ft.FontWeight.BOLD)
                        )
                    else:
                        # 👇 Pegamos a descrição real direto do dicionário aqui! 👇
                        desc_real = dado.get("descricao", "")
                        
                        controles_acao = ft.Row([
                            ft.IconButton(icon=ft.Icons.CHECK_CIRCLE_OUTLINE, icon_color="green", tooltip="Pagar Conta", on_click=lambda e, id=doc_id: abrir_popup_pagamento(id)),
                            
                            # Agora passamos o desc_real para o botão! ✏️
                            ft.IconButton(icon=ft.Icons.EDIT_OUTLINED, icon_color="blue", tooltip="Editar", on_click=lambda e, id=doc_id, d=desc_real, v=v_num: abrir_edicao(id, d, v)),
                            
                            ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", tooltip="Excluir", on_click=lambda e, id=doc_id: apagar_gasto(id))
                        ])
                    
                    # --- 🖃 CARIMBO DO HISTÓRICO GRAVADO AQUI (PAGAMENTO RÁPIDO) 🖃 ---
                    def criar_evento_pagar(id_doc):
                        def acao_pagar(e):
                            from datetime import datetime
                            hoje_str = datetime.now().strftime("%d/%m/%Y")
                            db.collection("gastos").document(id_doc).update({
                                "status": "pago",
                                "data_pagamento": hoje_str # <--- SALVA A DATA EXATA!
                            })
                            page.snack_bar = ft.SnackBar(ft.Text(f"✅ Conta paga com sucesso a {hoje_str}!"))
                            page.snack_bar.open = True
                            carregar_dados()
                            page.update()
                        return acao_pagar
                        # -----------------------------------------------------------------

                    cartao = ft.Card(content=ft.Container(content=ft.Row([
                        coluna_texto_cartao, 
                        controles_acao
                    ]), padding=10))
                    lista_gastos_atual.controls.append(cartao)

            # =========================================================
            # 🧠 INFORMAÇÃO DO MÊS PASSADO (APENAS VISUAL, SEM SOMAR)
            # =========================================================
            id_m_ant = str_mes_passado.replace("/", "_")
            doc_r_ant = db.collection("resumo").document(id_m_ant).get()
            renda_mes_passado = doc_r_ant.to_dict().get("renda", 0.0) if doc_r_ant.exists else 0.0
            
            if renda_mes_passado == 0.0:
                renda_mes_passado = renda_total_familiar 
                
            gasto_mes_passado = gastos_por_mes.get(str_mes_passado, 0.0)
            saldo_anterior = renda_mes_passado - gasto_mes_passado
            
            # Atualiza apenas a string menor!
            if saldo_anterior >= 0:
                texto_sobra_mes_anterior.value = f"Mês anterior: +R$ {saldo_anterior:.2f}"
                texto_sobra_mes_anterior.color = ft.Colors.GREEN_700
            else:
                texto_sobra_mes_anterior.value = f"Dívida anterior: -R$ {abs(saldo_anterior):.2f}"
                texto_sobra_mes_anterior.color = ft.Colors.RED_700

            # =========================================================
            # 🧮 A MATEMÁTICA VOLTA A SER PURA E À PROVA DE BALAS!
            # =========================================================
            # A renda_total_familiar já está líquida. O saldo é ela menos os gastos (pagos e pendentes)
            saldo = renda_total_familiar - total_pendente_geral - total_pago_geral
            
            texto_renda_total.value = f"R$ {renda_total_familiar:.2f}"
            texto_total_a_pagar.value = f"R$ {total_pendente_geral:.2f}" 
            texto_saldo_real.value = f"R$ {saldo:.2f}"
            texto_saldo_real.color = ft.Colors.GREEN if saldo >= 0 else ft.Colors.RED

            legenda_grafico.controls.clear()
            if total_despesas_mes_atual > 0:
                legenda_grafico.controls.append(ft.Text("Onde seu dinheiro foi:", weight="bold", size=16))
                
                # 👇 AGORA USAMOS A FUNÇÃO NOVA AQUI 👇
                for cat, valor_cat in gastos_por_categoria.items():
                    cor = cores_categorias.get(cat, "grey")
                    lista_detalhes = detalhes_por_categoria.get(cat, []) # Pega os sub-itens
                    
                    barra_interativa = criar_barra_categoria(cat, valor_cat, total_despesas_mes_atual, cor, lista_detalhes)
                    legenda_grafico.controls.append(barra_interativa)
            
            # 👇 SUBSTITUA O QUE ESTIVER ABAIXO DO SEU 'FOR' POR ISTO AQUI 👇
                legenda_grafico.visible = True
            else: 
                legenda_grafico.visible = False

            # =========================================================
            # 📦 O GRANDE CAIXOTÃO AGRUPADO (CARTÕES + GRÁFICO)
            # =========================================================
            painel_grafico.content = ft.Container(
                padding=20,
                border_radius=20,
                bgcolor="#F6F8FD", # O mesmo fundo azul clarinho chique!
                border=ft.border.all(1, "#E5E9F2"),
                content=ft.Column([
                    linha_cartao_financeiros, # 1. Os dois cartõezinhos entram no topo
                    ft.Divider(height=15, color="transparent"), # 2. Espaço pra respirar
                    legenda_grafico # 3. As barrinhas entram embaixo juntinhas!
                ], spacing=0)
            )
            
            # Tira a sombra do painel antigo e força ele a ficar sempre visível
            painel_grafico.elevation = 0 
            painel_grafico.visible = True 

            # =========================================================
            # 🎨 NOVA ABA DE MESES VISUAL (ESTILO PREMIUM)
            # =========================================================
            for mes, soma_mes in gastos_por_mes.items():
                id_m = mes.replace("/", "_")
                d_r = db.collection("resumo").document(id_m).get()
                r_m = d_r.to_dict().get("renda", 0.0) if d_r.exists else 0.0
                
                # Se não houver renda salva para o mês antigo, usamos a atual como base
                if r_m == 0: r_m = renda_total_familiar 
                
                saldo_m = r_m - soma_mes
                
                # Lógica de Cores e Ícones baseada na saúde financeira
                esta_positivo = saldo_m >= 0
                cor_tema = ft.Colors.GREEN_ACCENT_700 if esta_positivo else ft.Colors.RED_ACCENT_400
                cor_fundo_barra = ft.Colors.GREEN_50 if esta_positivo else ft.Colors.RED_50
                icone_status = ft.Icons.CHECK_CIRCLE_ROUNDED if esta_positivo else ft.Icons.REPORT_GMAILERRORRED_ROUNDED
                
                # Cálculo do progresso (Gasto em relação à Renda)
                # Se gastou mais que a renda, a barra fica cheia (1.0)
                progresso_valor = min(1.0, soma_mes / r_m) if r_m > 0 else 1.0

                # Montagem do Card com Stack para o Ícone Flutuante
                card_mes_premium = ft.Container(
                    content=ft.Stack([
                        # 1. O Corpo do Cartão
                        ft.Container(
                            padding=20,
                            border_radius=20,
                            bgcolor=ft.Colors.WHITE,
                            border=ft.border.all(1, ft.Colors.GREY_100),
                            content=ft.Column([
                                ft.Text(f"Mês: {mes}", size=18, weight="bold", color=ft.Colors.BLUE_GREY_900),
                                ft.Row([
                                    ft.Text(f"Gasto: R$ {soma_mes:.2f}", color=ft.Colors.GREY_700, size=13, weight="w500"),
                                    ft.Text("|", color=ft.Colors.GREY_300),
                                    ft.Text(f"Saldo: R$ {saldo_m:.2f}", color=cor_tema, size=13, weight="bold"),
                                ], spacing=10),
                                ft.Divider(height=10, color="transparent"),
                                # A Barra de Progresso Estilizada
                                ft.ProgressBar(
                                    value=progresso_valor,
                                    color=cor_tema,
                                    bgcolor=cor_fundo_barra,
                                    height=10,
                                    border_radius=10
                                )
                            ], spacing=5),
                        ),
                        # 2. O Ícone de Status Flutuante (na borda direita)
                        ft.Container(
                            content=ft.Icon(icone_status, color=cor_tema, size=30),
                            alignment=ft.Alignment.CENTER,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=25,
                            width=45,
                            height=45,
                            right=10,
                            top=35, # Ajuste conforme a altura do card
                            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, "black"))
                        )
                    ]),
                    # O clique para ver detalhes continua aqui!
                    on_click=lambda e, m=mes: ver_detalhes_mes(m),
                    margin=ft.margin.only(bottom=10)
                )
                
                lista_historico_meses.controls.append(card_mes_premium)

                # =========================================================
            # 📈 MÓDULO PREMIUM: GRÁFICO DE EVOLUÇÃO AZUL
            # =========================================================
            if gastos_por_mes:
                # 1. Coloca os meses na ordem certa do tempo
                def sort_key(mes_str):
                    if "/" in mes_str:
                        m, a = mes_str.split('/')
                        return int(a) * 12 + int(m)
                    return 0
                
                # Pega só os últimos 6 meses para o celular não ficar apertado
                meses_ordenados = sorted(gastos_por_mes.keys(), key=sort_key)[-6:] 
                
                pontos_grafico = []
                labels_eixo_x = []
                max_gasto = 0
                
                # 2. Desenha cada ponto no gráfico
                for i, mes in enumerate(meses_ordenados):
                    valor = gastos_por_mes[mes]
                    if valor > max_gasto: max_gasto = valor
                    
                    pontos_grafico.append(flet_charts.LineChartDataPoint(i, valor))
                    
                    # Pega só o número do mês (Ex: "03" tirado de "03/2026")
                    txt_mes = mes.split("/")[0] 
                    labels_eixo_x.append(
                        flet_charts.ChartAxisLabel(value=i, label=ft.Text(txt_mes, size=12, weight="bold", color=ft.Colors.GREY_500))
                    )

                # 3. A Linha Curvada Azul!
                linha_gastos = flet_charts.LineChartData(
                    points=pontos_grafico,
                    stroke_width=4,
                    color=ft.Colors.BLUE_500,  # Azul Premium
                    curved=True,               # Efeito de onda suave!
                    rounded_stroke_cap=True,
                    point=True,                # Mostra as bolinhas em cada mês
                )

                # 4. Monta a caixa do gráfico
                grafico = flet_charts.LineChart(
                    data_series=[linha_gastos],
                    border=ft.border.all(0, ft.Colors.TRANSPARENT),
                    left_axis=flet_charts.ChartAxis(label_size=0), # Esconde o eixo Y para ficar limpo
                    bottom_axis=flet_charts.ChartAxis(labels=labels_eixo_x, label_size=25),
                    min_y=0,
                    max_y=max_gasto * 1.2 if max_gasto > 0 else 100, # Dá um respiro pro teto
                    expand=True,
                )

                cartao_evolucao.content = criar_cartao_premium(
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.SHOW_CHART, color=ft.Colors.BLUE),
                            ft.Text("Evolução Mensal (Gastos)", weight="bold", size=16)
                        ]),
                        ft.Container(content=grafico, height=150, padding=10) # Altura travada pro visual
                    ]), elevation=2
                )
                cartao_evolucao.visible = True
            else:
                cartao_evolucao.visible = False


            docs_listas = db.collection("listas_compras").where("token_familia", "==", usuario_token).order_by("data_criacao", direction=firestore.Query.DESCENDING).stream()
            for doc in docs_listas:
                d = doc.to_dict()
                doc_id = doc.id
                itens_str = "".join([f"\n  • {i['qtd']}x {i['nome']} (R$ {i.get('preco', 0):.2f})" for i in d.get("itens", [])])
  
                # =========================================================
                # 🛍️ DESIGN PREMIUM COM LISTAGEM DE ITENS (CORRIGIDO)
                # =========================================================
                # 1. Pegamos os dados detalhados que salvamos no Firebase
                itens_lista = d.get('itens_detalhados', [])
                
                # 2. A "Fábrica" de itens: Criamos uma coluna vazia e enchemos com Rows
                # 1. Transformamos os dados em uma tabela visual organizada
                itens_lista = d.get('itens_detalhados') or d.get('itens') or []
                coluna_itens_tabela = ft.Column(spacing=10)
                
                if isinstance(itens_lista, list):
                    for item in itens_lista:
                        if item.get('qtd', 0) > 0:
                            coluna_itens_tabela.controls.append(
                                ft.Row([
                                    ft.Text(item['nome'], weight="w500", size=15, expand=True),
                                    ft.Text(f"{item['qtd']}x", color=ft.Colors.GREY_500),
                                    ft.Text(f"R$ {item.get('preco', 0):.2f}", color=ft.Colors.GREEN_700, weight="bold"),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                            )
                
                # 2. Montagem do Card com as peças nos lugares CERTOS
                cartao_lista = ft.Container(
                    padding=25,
                    border_radius=30,
                    bgcolor=ft.Colors.WHITE,
                    shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.1, "black")),
                    margin=ft.margin.only(bottom=20),
                    content=ft.Column([
                        # TOPO (Lugar 1)
                        ft.Row([
                            ft.Row([
                                ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, color=ft.Colors.BLUE_600),
                                ft.Text(f"{d.get('data_texto', 'Sem Data')}", size=20, weight="bold"),
                            ], spacing=10),
                            ft.IconButton(icon=ft.Icons.DELETE_OUTLINE_ROUNDED, icon_color="red", on_click=lambda e, id=doc_id: apagar_lista(id))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Text(f"Total previsto: R$ {d.get('total_previsto', 0):.2f}", color=ft.Colors.BLUE_700, weight="bold"),
                        ft.Divider(height=20),

                        # CONTEÚDO (Lugar 2 - Onde os itens aparecem ORGANIZADOS)
                        ft.Container(content=coluna_itens_tabela, padding=ft.padding.only(bottom=20)),

                        # BASE (Lugar 3 - O Botão no final de tudo)
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color="white"),
                                ft.Text("Já Comprei", color="white", weight="bold", size=18),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            bgcolor=ft.Colors.GREEN_600,
                            padding=15,
                            border_radius=15,
                            on_click=lambda e, id=doc_id, dados=d: lancar_lista_como_gasto(id, dados),
                        )
                    ])
                )

                # 4. Adiciona o cartão pronto na tela
                lista_de_listas_salvas.controls.append(cartao_lista)

            page.update()

        def salvar_renda_clique(e):
            if not input_renda.value: return
            try:
                valor_novo = float(input_renda.value.replace(',', '.'))
                db.collection("rendas").document(nome_usuario).set({"valor": valor_novo})
                input_renda.value = ""
                page.snack_bar = ft.SnackBar(ft.Text(f"Salário de {nome_usuario} atualizado!"))
                page.snack_bar.open = True
                carregar_dados()
                page.update()
            except ValueError:
                page.snack_bar = ft.SnackBar(ft.Text("Erro: Digite um valor válido."))
                page.snack_bar.open = True
                page.update()

        # ====================================================================
        # 🚀 O MOTOR DE SALVAR DADOS (ONDE A MÁQUINA DO TEMPO ACONTECE) 🚀
        # ====================================================================
        def adicionar_gasto_clique(e):
            if not descricao_input.value or not valor_input.value: return
            try:
                v_total = float(valor_input.value.replace(',', '.'))
                
                # Pega as parcelas (Se der erro de digitação, assume 1)
                try: qtd_parcelas = int(input_parcelas.value)
                except: qtd_parcelas = 1
                if qtd_parcelas < 1: qtd_parcelas = 1
                
                # A mágica da divisão:
                v_parcela = v_total / qtd_parcelas
                
                hoje = datetime.datetime.now()
                mes_base = hoje.month
                ano_base = hoje.year

                # Regra 1: Mês passado
                if checkbox_mes_passado.value == True:
                    mes_base -= 1
                    if mes_base < 1:
                        mes_base = 12; ano_base -= 1

                forma_pag_selecionada = forma_pagamento_dropdown.value
                
                # Regra 2: Máquina do Tempo do Cartão de Crédito
                if forma_pag_selecionada == "Cartão de Crédito" and checkbox_mes_passado.value == False:
                    mes_base += 1
                    if mes_base > 12:
                        mes_base = 1; ano_base += 1

                # 🔥 A TRAVA DE STATUS 🔥
                status_correto = "pendente" if forma_pag_selecionada == "Cartão de Crédito" else "pago"
                if qtd_parcelas > 1: status_correto = "pendente" # Parcela futura sempre nasce pendente!

                # =======================================================
                # 🚀 O LOOP DE CLONAGEM PARA O FUTURO 🚀
                # =======================================================
                for i in range(qtd_parcelas):
                    mes_alvo = mes_base + i
                    ano_alvo = ano_base
                    
                    # Se o mês passar de 12 (Dezembro), ele vira o ano sozinho!
                    while mes_alvo > 12:
                        mes_alvo -= 12
                        ano_alvo += 1
                        
                    mes_ano_salvar = f"{mes_alvo:02d}/{ano_alvo}"
                    
                    # Coloca a etiqueta (1/5) no nome se for parcelado
                    desc_salvar = descricao_input.value
                    if qtd_parcelas > 1:
                        desc_salvar = f"{descricao_input.value} ({i+1}/{qtd_parcelas})"

                    db.collection("gastos").add({
                        "token_familia": usuario_token,
                        "descricao": desc_salvar, 
                        "valor": v_parcela, 
                        "categoria": categoria_dropdown.value,
                        "forma_pagamento": forma_pag_selecionada if forma_pag_selecionada else "Não informado",
                        "cartao_usado": dropdown_qual_cartao.value if dropdown_qual_cartao.value else "Não se aplica",
                        "quem_pagou": nome_usuario, 
                        "data": hoje.strftime("%d/%m/%Y"), 
                        "mes_ano": mes_ano_salvar, # O mês que viajou no tempo!
                        "data_registro": firestore.SERVER_TIMESTAMP,
                        "status": status_correto,
                        "data_vencimento": input_vencimento.value ,
                        "recorrente": checkbox_recorrente.value
                    })
                
                # Limpa os campos após salvar o combo
                input_vencimento.value = ""; descricao_input.value = ""; valor_input.value = ""
                input_parcelas.value = "1" # Reseta para à vista
                categoria_dropdown.value = None; forma_pagamento_dropdown.value = None; dropdown_qual_cartao.value = "Não se aplica"
                checkbox_mes_passado.value = False
                
                page.snack_bar = ft.SnackBar(ft.Text(f"✅ Lançamento em {qtd_parcelas}x salvo com sucesso!"))
                page.snack_bar.open = True
                
                carregar_dados()
            except Exception as err: 
                print(f"Erro ao salvar: {err}")

            
        
        # =========================================================
        # 🧠 MEMÓRIA DE PREÇOS DO MERCADO (AGORA NO LUGAR CERTO!)
        # =========================================================
        doc_precos = db.collection("mercado").document("precos_base").get()
        precos_conhecidos = doc_precos.to_dict() if doc_precos.exists else {}

        nomes_produtos = [
            "Arroz", "Feijão", "Macarrão", "Óleo", "Açúcar", "Sal", "Café", "Farinha de Trigo", "Farinha de Mandioca", "Cuscuz / Flocão",
            "Leite", "Manteiga / Margarina", "Queijo", "Presunto / Mortadela", "Pão", "Achocolatado", "Mucilon", "Aveia", "Neston", "Biscoito / Bolacha",
            "Carne Bovina", "Frango", "Ovos", "Linguiça / Salsicha", "Frutas", "Verduras / Folhas", "Alho", "Cebola", "Batata", "Tomate",
            "Refrigerante", "Polpa de Frutas", "Suco", "Molho de Tomate", "Maionese / Ketchup", "Sabão em Pó", "Sabão em Pedra", "Detergente",
            "Amaciante", "Água Sanitária", "Desinfetante", "Limpador Multiuso", "Esponja", "Saco de Lixo", "Papel Higiênico", "Sabonete",
            "Creme Dental", "Shampoo", "Condicionador", "Desodorante", "Absorvente"
        ]
        
        itens_mercado = []
        for n in nomes_produtos:
            preco_salvo = precos_conhecidos.get(n, 0.0) 
            itens_mercado.append({"nome": n, "qtd": 0, "preco": preco_salvo})

        # 🔥 AS VARIÁVEIS LIVRES E VISÍVEIS PARA O APP INTEIRO! 🔥
        lista_ui_compras = ft.Column(scroll=ft.ScrollMode.AUTO)
        texto_total_compras = ft.Text("Total: R$ 0.00", size=22, weight="bold", color="green")

        def recalcular_total_compras():
            texto_total_compras.value = f"Total: R$ {sum(i['qtd'] * i['preco'] for i in itens_mercado):.2f}"
            page.update()

        def criar_linha_item(item):
            campo_qtd = ft.TextField(label="Qtd", width=65, height=45, text_size=12, keyboard_type=ft.KeyboardType.NUMBER, border_radius=8, color="black")
            valor_preco_str = f"{item['preco']:.2f}" if item['preco'] > 0 else ""
            campo_preco = ft.TextField(label="R$ Unit", value=valor_preco_str, width=80, height=45, text_size=12, keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
            
            def atualizar_valores(e):
                try: item["qtd"] = int(campo_qtd.value) if campo_qtd.value else 0
                except: item["qtd"] = 0
                try: item["preco"] = float(campo_preco.value.replace(',', '.')) if campo_preco.value else 0.0
                except: item["preco"] = 0.0
                recalcular_total_compras()

            campo_qtd.on_change = atualizar_valores
            campo_preco.on_change = atualizar_valores

            return criar_cartao_premium(
                ft.Row([
                    ft.Text(item["nome"], weight=ft.FontWeight.BOLD, expand=True), 
                    campo_qtd, 
                    campo_preco
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=5),
                elevation=1
            )

        for item in itens_mercado: 
            lista_ui_compras.controls.append(criar_linha_item(item))

        def resetar_formulario_compras():
            # Zera APENAS a quantidade (qtd). O preço continua na memória!
            for i in itens_mercado: 
                i["qtd"] = 0 
                
            lista_ui_compras.controls.clear()
            for i in itens_mercado: 
                lista_ui_compras.controls.append(criar_linha_item(i))
                
            recalcular_total_compras()
            page.update() # Força a tela a atualizar na mesma hora

        # ... (E logo aqui embaixo continua o seu def salvar_lista_sem_lancar(e):) ...

        def salvar_lista_sem_lancar(e):
            itens_salvar = [{"nome": i["nome"], "qtd": i["qtd"], "preco": i["preco"]} for i in itens_mercado if i["qtd"] > 0]
            if not itens_salvar:
                page.snack_bar = ft.SnackBar(ft.Text("Preencha as quantidades!"))
                page.snack_bar.open = True
                page.update()
                return
                
            # --- 🧠 O APP APRENDE OS NOVOS PREÇOS AQUI ---
            novos_precos = {}
            for i in itens_mercado:
                if i["preco"] > 0:
                    novos_precos[i["nome"]] = i["preco"]
            
            if novos_precos:
                # O merge=True faz com que ele só atualize os preços novos, sem apagar os outros itens do banco!
                db.collection("mercado").document("precos_base").set(novos_precos, merge=True)
            # ----------------------------------------------

            db.collection("listas_compras").add({
                "data_texto": datetime.date.today().strftime("%d/%m/%Y"), "data_criacao": firestore.SERVER_TIMESTAMP,
                "itens": itens_salvar, "total_previsto": sum(i["qtd"] * i["preco"] for i in itens_salvar)
            })
            resetar_formulario_compras()
            page.snack_bar = ft.SnackBar(ft.Text("Sua lista foi salva na aba 'Listas' e os preços atualizados!"))
            page.snack_bar.open = True
            carregar_dados()
            page.navigation_bar.selected_index = 2 
            mudar_tab(None)

        botao_salvar_lista = ft.ElevatedButton("Salvar Lista Para Comprar Depois", on_click=salvar_lista_sem_lancar, bgcolor="blue", color="white", width=300)

        texto_alerta_financeiro = ft.Text("", color=ft.Colors.RED_700, weight=ft.FontWeight.BOLD, expand=True) # <-- expand aqui!
        cartao_alerta_financeiro = ft.Card(content=ft.Container(content=ft.Row([ft.Icon(ft.icons.Icons.WARNING_AMBER, color=ft.Colors.RED_700), texto_alerta_financeiro]), padding=10, bgcolor=ft.Colors.RED_50), visible=False)
        def formatar_mes_ano_meta(e):
            numeros = "".join(filter(str.isdigit, e.control.value))
            e.control.value = f"{numeros[:2]}/{numeros[2:6]}" if len(numeros) > 2 else numeros
            e.control.update()
            
        input_data_meta = ft.TextField(label="Prazo (MM/AAAA)", width=150, on_change=formatar_mes_ano_meta, max_length=7)

        def formatar_mes_ano_consig(e):
            numeros = "".join(filter(str.isdigit, e.control.value))
            e.control.value = f"{numeros[:2]}/{numeros[2:6]}" if len(numeros) > 2 else numeros
            e.control.update()

        input_valor_consig = ft.TextField(label="Valor Parcela (R$)", expand=True, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, prefix_icon=ft.Icons.ATTACH_MONEY)
        input_total_consig = ft.TextField(label="Total Parcelas", expand=True, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, prefix_icon=ft.Icons.FORMAT_LIST_NUMBERED)
        input_data_consig = ft.TextField(label="Início (MM/AAAA)", expand=True, on_change=formatar_mes_ano_consig, border_radius=10, prefix_icon=ft.Icons.CALENDAR_MONTH)
        lista_consignados_ui = ft.Column()

        def apagar_consignado(doc_id):
            db.collection("consignados").document(doc_id).delete()
            carregar_dados()
            page.snack_bar = ft.SnackBar(ft.Text("Empréstimo excluído da nuvem!"))
            page.snack_bar.open = True
            page.update()

        def salvar_consignado(e):
            if not input_valor_consig.value or not input_total_consig.value or not input_data_consig.value: return
            try:
                db.collection("consignados").add({
                    "valor_parcela": float(input_valor_consig.value.replace(',', '.')), "total_parcelas": int(input_total_consig.value),
                    "mes_ano_inicio": input_data_consig.value, "dono": nome_usuario 
                })
                input_valor_consig.value = ""; input_total_consig.value = ""; input_data_consig.value = ""
                carregar_dados()
                page.snack_bar = ft.SnackBar(ft.Text("Consignado salvo na nuvem!"))
                page.snack_bar.open = True
                page.update()
            except: pass
        # 👇 COLE ISTO ANTES DO mudar_tab 👇
        cartao_evolucao = ft.Container(visible=False)

        def mudar_tab(e):
            index = e.control.selected_index if e else page.navigation_bar.selected_index
            ecra_inicio.visible = (index == 0)
            ecra_compras.visible = (index == 1)
            ecra_listas_salvas.visible = (index == 2) 
            ecra_historico.visible = (index == 3)   
            ecra_financeiro.visible = (index == 4)  
            
            # Apenas atualiza a tela na hora, sem chamar o banco de dados!
            page.update()

        # Lá embaixo na definição do page.navigation_bar
        page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.icons.Icons.HOME_OUTLINED, label="Início"),
                ft.NavigationBarDestination(icon=ft.icons.Icons.SHOPPING_CART_OUTLINED, label="Mercado"),
                ft.NavigationBarDestination(icon=ft.icons.Icons.LIST_ALT_OUTLINED, label="Listas"),
                ft.NavigationBarDestination(icon=ft.icons.Icons.CALENDAR_MONTH_OUTLINED, label="Meses"),
                ft.NavigationBarDestination(icon=ft.icons.Icons.ACCOUNT_BALANCE_OUTLINED, label="Finanças"),
            ], on_change=mudar_tab 
        )

        # =======================================================
        # 🎨 MONTAGEM FINAL DA TELA INICIAL (DESIGN PREMIUM)
        # =======================================================
        
        # 1. Empacotando o Salário
        botao_guardar_salario = ft.ElevatedButton("Guardar Salário", on_click=salvar_renda_clique, height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), bgcolor="#F0F4FA", color=ft.Colors.BLUE_700))
        linha_salario = ft.Row([input_renda, botao_guardar_salario], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # 2. O novo botão de Lançar
        botao_lancar_gasto = ft.ElevatedButton("Lançar Gasto", on_click=adicionar_gasto_clique, bgcolor=ft.Colors.BLUE_500, color=ft.Colors.WHITE, height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))


        # =======================================================
        # 📦 O FORMULÁRIO RETRÁTIL (EFEITO SANFONA)
        # =======================================================
        
        # 1. Agrupamos todos os campos numa Coluna que NASCE ESCONDIDA
        coluna_campos_despesa = ft.Column([
            ft.Divider(height=10, color="transparent"), # Espaço quando abre
            descricao_input, 
            valor_input, 
            linha_cat,           
            linha_forma,         
            linha_cartao,        
            linha_opcionais,
            linha_switch,
            ft.Divider(height=10, color="transparent"),
            ft.Row([ft.Container(content=botao_lancar_gasto, expand=True)])
        ], spacing=12, visible=False)

        # 2. Criamos o ícone da setinha que vai girar
        icone_seta_despesa = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, color=ft.Colors.BLUE_GREY_900)

        # 3. A Função que faz o botão de abrir e fechar funcionar
        def alternar_formulario_despesa(e):
            coluna_campos_despesa.visible = not coluna_campos_despesa.visible
            # Se tiver visível, seta pra cima. Se não, seta pra baixo.
            icone_seta_despesa.name = ft.Icons.KEYBOARD_ARROW_UP if coluna_campos_despesa.visible else ft.Icons.KEYBOARD_ARROW_DOWN
            page.update()

        formulario_despesas_premium = ft.Container(
            padding=20,
            border_radius=15,
            bgcolor="#F6F8FD", 
            border=ft.border.all(1, "#E5E9F2"),
            margin=ft.margin.only(bottom=20),
            content=ft.Column([
                
                # --- CABEÇALHO CLICÁVEL ---
                ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color=ft.Colors.DEEP_PURPLE_400, size=30),
                            ft.Text("Adicionar Nova Despesa", size=18, weight="bold", color=ft.Colors.BLUE_GREY_900)
                        ], spacing=10),
                        icone_seta_despesa # A setinha aqui na ponta direita!
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    on_click=alternar_formulario_despesa,
                    ink=True, # Cria aquele efeito de "onda" ao clicar
                    padding=ft.padding.symmetric(vertical=5)
                ),
                
                # --- OS CAMPOS ESCONDIDOS ---
                coluna_campos_despesa
                
            ], spacing=0) 
        )
        
        # =======================================================
        # 📜 PAINEL DE LANÇAMENTOS RETRÁTIL
        # =======================================================
        
        # 1. Faz a lista nascer escondida (como você pediu!)
        lista_gastos_atual.visible = False 
        
        # 2. O ícone da setinha apontando para baixo
        icone_seta_lancamentos = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, color=ft.Colors.BLUE_GREY_900)

        # 3. A função que abre e fecha a lista
        def alternar_lista_lancamentos(e):
            lista_gastos_atual.visible = not lista_gastos_atual.visible
            icone_seta_lancamentos.name = ft.Icons.KEYBOARD_ARROW_UP if lista_gastos_atual.visible else ft.Icons.KEYBOARD_ARROW_DOWN
            page.update()

        # 4. O Caixotão Premium dos Lançamentos
        painel_lancamentos = ft.Container(
            padding=20,
            border_radius=15,
            bgcolor="#F6F8FD", # Mesmo fundo azulzinho chique!
            border=ft.border.all(1, "#E5E9F2"),
            margin=ft.margin.only(bottom=20),
            content=ft.Column([
                # --- CABEÇALHO CLICÁVEL ---
                ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Icon(ft.Icons.FORMAT_LIST_BULLETED_ROUNDED, color=ft.Colors.DEEP_PURPLE_400, size=30),
                            ft.Text(f"Lançamentos de {mes_ano_atual}", size=18, weight="bold", color=ft.Colors.BLUE_GREY_900)
                        ], spacing=10),
                        icone_seta_lancamentos
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    on_click=alternar_lista_lancamentos,
                    ink=True,
                    padding=ft.padding.symmetric(vertical=5)
                ),
                
                # --- A LISTA QUE APARECE E SOME ---
                lista_gastos_atual
                
            ], spacing=0)
        )

        # 4. Jogando as caixas prontas na tela
        ecra_inicio.controls.extend([
            # 👇 Trocamos aqui para mostrar o bloco com o Token junto com o botão de tema! 👇
            ft.Row([cabecalho_usuario, botao_tema], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START), 
            cartao_pis, cartao_alerta_financeiro, painel_resumo, painel_grafico, ft.Divider(),
            # ... resto do código
            
            linha_salario, # Entra a linha do salário
            ft.Divider(height=20, color="transparent"),
            
            formulario_despesas_premium, # Entra a caixa azul com os campos
        

            painel_lancamentos, # <--- O NOVO PAINEL DE LANÇAMENTOS AQUI!
            
        
            lista_gastos_atual
        ])

        lista_metas_ui = ft.Column(spacing=10)
        input_nome_meta = ft.TextField(label="Qual o seu sonho?", expand=True, hint_text="Ex: Console Trimui", border_radius=10, prefix_icon=ft.Icons.STAR_BORDER)
        input_valor_meta = ft.TextField(label="Valor Total (R$)", expand=True, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, prefix_icon=ft.Icons.ATTACH_MONEY)
        input_data_meta = ft.TextField(label="Prazo (MM/AAAA)", expand=True, on_change=formatar_mes_ano_meta, max_length=7, border_radius=10, prefix_icon=ft.Icons.CALENDAR_MONTH)
        
        
        
        def criar_meta_clique(e):
            if not input_nome_meta.value or not input_valor_meta.value or not input_data_meta.value:
                page.snack_bar = ft.SnackBar(ft.Text("⚠️ Preencha o nome, valor e o prazo do seu sonho!"))
                page.snack_bar.open = True
                page.update()
                return

            try:
                valor_total = float(input_valor_meta.value.replace(',', '.'))
                db.collection("metas").add({
                    "nome": input_nome_meta.value.strip(),
                    "valor_total": valor_total,
                    "valor_guardado": 0.0,
                    "data_alvo": input_data_meta.value.strip(),
                    "dono": nome_usuario,
                    "data_criacao": firestore.SERVER_TIMESTAMP
                })
                
                input_nome_meta.value = ""
                input_valor_meta.value = ""
                input_data_meta.value = ""
                
                page.snack_bar = ft.SnackBar(ft.Text("✅ Sonho registrado! Hora de começar a poupar!"))
                page.snack_bar.open = True
                carregar_dados()
                page.update()
            except Exception as err:
                print(f"Erro ao salvar meta: {err}")

        botao_aba_emprestimos = ft.ElevatedButton("Empréstimos", icon=ft.icons.Icons.ACCOUNT_BALANCE_WALLET, bgcolor="blue", color="white", expand=True)
        botao_aba_metas = ft.ElevatedButton("Metas & Sonhos", icon=ft.icons.Icons.STAR, bgcolor=ft.Colors.GREY_300, color="black", expand=True)

        form_emprestimo_premium = criar_cartao_premium(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ACCOUNT_BALANCE, color=ft.Colors.BLUE),
                    ft.Text("Registrar Novo Empréstimo", weight=ft.FontWeight.BOLD, size=16)
                ]),
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                input_valor_consig, 
                input_total_consig,
                input_data_consig, # Um embaixo
                ft.ElevatedButton("Gravar na Nuvem", on_click=salvar_consignado, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, width=400, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
            ], spacing=15),
            elevation=2
        )

        conteudo_emprestimos = ft.Column([
            ft.Divider(color="transparent", height=10),
            form_emprestimo_premium, # <--- Olha o formulário chic aqui!
            ft.Divider(color="transparent", height=10),
            ft.Text("Empréstimos Ativos", size=18, weight="bold"), 
            lista_consignados_ui
        ], scroll=ft.ScrollMode.AUTO, visible=True)

        form_metas_premium = criar_cartao_premium(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ROCKET_LAUNCH, color=ft.Colors.ORANGE),
                    ft.Text("Criar Novo Sonho", weight=ft.FontWeight.BOLD, size=16)
                ]),
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                input_nome_meta, # Nome ocupa a linha toda
                input_valor_meta, 
                input_data_meta,
                ft.ElevatedButton("Começar a Guardar", on_click=criar_meta_clique, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, width=400, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
            ], spacing=15),
            elevation=2
        )

        conteudo_metas = ft.Column([
            ft.Divider(color="transparent", height=10),
            form_metas_premium, # <--- Formulário de sonhos chic!
            ft.Divider(color="transparent", height=10),
            ft.Text("Nossos Cofrinhos", size=18, weight="bold"),
            lista_metas_ui
        ], scroll=ft.ScrollMode.AUTO, visible=False)

        # Usamos ft.Colors.ON_SURFACE (que é preto no claro, e branco no escuro!)
        # E ft.Colors.SURFACE_VARIANT (que é cinza claro no claro, e cinza escuro no escuro!)
        
        botao_aba_emprestimos = ft.ElevatedButton("Empréstimos", icon=ft.Icons.ACCOUNT_BALANCE_WALLET, bgcolor="blue", color="white", expand=True, data="aba_emprestimos")
        botao_aba_metas = ft.ElevatedButton("Metas & Sonhos", icon=ft.Icons.STAR, bgcolor=ft.Colors.ON_SURFACE_VARIANT, color=ft.Colors.ON_SURFACE, expand=True, data="aba_metas")

        def alternar_sub_abas(e):
            if e.control.data == "aba_emprestimos":
                conteudo_emprestimos.visible = True
                conteudo_metas.visible = False
                botao_aba_emprestimos.bgcolor = "blue"
                botao_aba_emprestimos.color = "white"
                botao_aba_metas.bgcolor = ft.Colors.ON_SURFACE_VARIANT
                botao_aba_metas.color = ft.Colors.ON_SURFACE
            elif e.control.data == "aba_metas":
                conteudo_emprestimos.visible = False
                conteudo_metas.visible = True
                botao_aba_emprestimos.bgcolor = ft.Colors.ON_SURFACE_VARIANT
                botao_aba_emprestimos.color = ft.Colors.ON_SURFACE
                botao_aba_metas.bgcolor = "blue"
                botao_aba_metas.color = "white"
            page.update()

        botao_aba_emprestimos.on_click = alternar_sub_abas
        botao_aba_metas.on_click = alternar_sub_abas

        linha_botoes = ft.Row([botao_aba_emprestimos, botao_aba_metas], alignment=ft.MainAxisAlignment.CENTER)

        ecra_financeiro.controls.extend([
            ft.Text("Central de Planejamento", size=24, weight="bold"),
            ft.Text("Organize o passado (Dívidas) e guarde para o futuro (Sonhos).", size=14, color=ft.Colors.GREY),
            ft.Divider(),
            
            # 👇 O NOSSO GRÁFICO PREMIUM ENTRA AQUI 👇
            cartao_evolucao,
            ft.Divider(color="transparent", height=5), # Dá um espacinho
            
            linha_botoes,
            conteudo_emprestimos,
            conteudo_metas
        ])

        ecra_compras.controls.extend([
            ft.Text("Fazer Mercado", size=24, weight="bold"),
            ft.Text("Preencha para somar. Depois clique em salvar.", size=14, color="grey"),
            ft.Divider(), texto_total_compras, botao_salvar_lista, ft.Divider(),
            ft.Container(content=lista_ui_compras, height=350, expand=True) 
        ])

        ecra_listas_salvas.controls.extend([
            ft.Text("Minhas Listas Salvas", size=24, weight="bold"),
            ft.Text("Abaixo estão as listas de compras. Clique em 'Já Comprei' no supermercado.", size=14, color="grey"),
            ft.Divider(), lista_de_listas_salvas
        ])

        ecra_historico.controls.extend([
            ft.Text("Histórico por Mês", size=24, weight="bold"),
            ft.Text("Clique no mês para ver os detalhes.", size=14, color="grey"),
            ft.Divider(), lista_historico_meses
        ])
        
        page.add(ecra_inicio, ecra_compras, ecra_listas_salvas, ecra_historico, ecra_financeiro)
        carregar_dados()

        # ====================================================================
        # 📡 MÓDULO REAL-TIME FLET 0.82+: O RADAR DE NOTIFICAÇÕES
        # ====================================================================
        primeira_leitura_firebase = [True]

        def atualizar_tela_com_aviso(mensagem):
            if mensagem == "novo_gasto":
                carregar_dados() # Os números já vimos que atualizam!
                
                # Criamos a notificação
                aviso = ft.SnackBar(
                    content=ft.Row([
                        ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE, color="white"),
                        ft.Text("Atenção: Os gastos foram atualizados!", color="white", weight="bold")
                    ]),
                    bgcolor=ft.Colors.BLUE_900,
                    behavior=ft.SnackBarBehavior.FLOATING, 
                    margin=20,
                    duration=4000 
                )
                
                # INJEÇÃO DIRETA NA TELA:
                page.overlay.append(aviso)
                aviso.open = True
                page.update()

        # 2. LIGANDO O RÁDIO: O Flet fica ouvindo nessa "frequência"
        page.pubsub.subscribe(atualizar_tela_com_aviso)

        # 3. O OLHEIRO DO FIREBASE (Trabalha em segundo plano)
        def radar_firebase_ativado(col_snapshot, changes, read_time):
            # A gente ignora a primeira vez que o app abre, senão ele apita à toa
            if primeira_leitura_firebase[0]:
                primeira_leitura_firebase[0] = False
                return 
            
            # Se passou da primeira leitura, significa que uma conta NOVA entrou ou foi paga!
            # Manda o sinal pro rádio:
            page.pubsub.send_all("novo_gasto")

        # 4. LIGANDO O OLHEIRO NAS SUAS DESPESAS
        db.collection("gastos").on_snapshot(radar_firebase_ativado)
        page.on_connect = lambda _: carregar_dados() 
        
        # 🟢 A MÁGICA FINAL: APAGA O CARREGAMENTO E MOSTRA O APP!
        page.controls.clear()
        page.vertical_alignment = ft.MainAxisAlignment.START # Volta o alinhamento ao normal
        page.horizontal_alignment = ft.CrossAxisAlignment.START
        page.add(ecra_inicio, ecra_compras, ecra_listas_salvas, ecra_historico, ecra_financeiro)
        page.update()

    # =======================================================
    # LÓGICA DE LOGIN INICIAL (COM CÃO DE GUARDA)
    # =======================================================
    if usuario_nome and usuario_nasc and usuario_5_anos is not None and usuario_token:
        # Bate no Firebase antes de abrir a porta!
        doc_fam = db.collection("familias").document(usuario_token).get()
        status = doc_fam.to_dict().get("membros", {}).get(usuario_nome, "ativo") if doc_fam.exists else "ativo"
        
        if status == "bloqueado":
            # 🚫 EXPULSO! Limpa o cofre e joga pro login
            page.shared_preferences.remove("usuario_token")
            page.controls.clear()
            page.scroll = None 
            page.vertical_alignment = ft.MainAxisAlignment.CENTER
            page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            page.add(tela_login)
            page.snack_bar = ft.SnackBar(ft.Text("🚫 Acesso Revogado pelo Líder!", color="white", weight="bold"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
        else:
            # 🟢 TUDO CERTO! Pode entrar.
            montar_interface_principal(usuario_nome, usuario_nasc, usuario_5_anos, usuario_token)
    else:
        page.controls.clear()
        page.scroll = None 
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.add(tela_login)
        page.update()

ft.app(target=main, assets_dir="assets")

