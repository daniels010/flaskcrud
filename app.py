import os
from flask import Flask, jsonify, request, render_template, flash, url_for, redirect
from sqlalchemy.exc import IntegrityError
from models.models import Produto, Cliente, Venda, db
from forms import ClienteForm, ProdutoForm, VendaForm
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_wtf.file import FileAllowed

import csv
from io import StringIO
from flask import Response

app = Flask(__name__)

app.config['WTF_CSRF_ENABLED'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clientes1.db'
app.config['SECRET_KEY'] = 'sua_chave_secreta'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['CSV_FOLDER'] = os.path.join(BASE_DIR, 'static')

#agora eu to setando placeholder dentro da minha pasta /uploads entao nao faz sentido mandar checar isso
#mas vou deixar ai so pra caso eu mude o jeito de pensar tudo isso

#if not os.path.exists(app.config['UPLOAD_FOLDER']):
#    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)

@app.route('/adicionar-clientes', methods=['GET', 'POST'])
def adicionar_cliente():
    form = ClienteForm(data=request.form)  # Usar `request.form` para dados de formulário

    if request.method == 'POST':
        if form.validate():
            new_cliente = Cliente(
                nome=form.nome.data,
                idade=form.idade.data,
                cpf=form.cpf.data,
                email=form.email.data,
                rua=form.rua.data,
                numero=form.numero.data,
                complemento=form.complemento.data,
                bairro=form.bairro.data,
                cidade=form.cidade.data,
                estado=form.estado.data,
                cep=form.cep.data
            )

            db.session.add(new_cliente)
            try:
                db.session.commit()
                flash("Cliente adicionado com sucesso!", "success")
                return render_template('adicionar_clientes.html', form=form)
            except IntegrityError:
                db.session.rollback()
                flash("Erro ao adicionar cliente. CPF ou email já existente.", "danger")
                return render_template('adicionar_clientes.html', form=form)
        else:
            flash("Erro no formulário. Verifique os campos e tente novamente.", "danger")
            return render_template('adicionar_clientes.html', form=form)

    # Renderiza o formulário no GET
    return render_template('adicionar_clientes.html', form=form)


#ESSE AQUI EU TO OBRIGANDO A ADICIONAR A IMAGEM
#ESSE É CERTEZA QUE FUNCIONA
@app.route('/adicionar-produtos', methods=['GET', 'POST'])
def add_produto():
    form = ProdutoForm()

    if request.method == 'POST':
        print("Método POST chamado.")  # Debug
        if form.validate_on_submit():
            print("Formulário validado com sucesso.")  # Debug
            if 'imagem' in request.files:
                imagem = request.files['imagem']
                if imagem.filename != '':
                    nome_imagem = secure_filename(imagem.filename)
                    caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem)

                    # Tenta salvar a imagem no caminho especificado
                    try:
                        imagem.save(caminho_imagem)
                        print(f"Imagem salva em {caminho_imagem}.")  # Debug
                    except Exception as e:
                        print(f"Erro ao salvar a imagem: {e}")
                        flash("Erro ao salvar a imagem. Tente novamente.", "danger")
                        return render_template('adicionar_produtos.html', form=form)

                    # Cria o novo produto com o caminho da imagem
                    new_produto = Produto(
                        nome=form.nome.data,
                        preco=form.preco.data,
                        quantidade=form.quantidade.data,
                        descricao=form.descricao.data,
                        imagem=caminho_imagem
                    )

                    db.session.add(new_produto)
                    try:
                        db.session.commit()
                        flash("Produto adicionado com sucesso!", "success")
                        return render_template('adicionar_produtos.html', form=form)
                    except IntegrityError as e:
                        db.session.rollback()
                        print(f"Erro ao adicionar produto: {e}")  # Debug
                        flash("Erro ao adicionar produto. Verifique os dados e tente novamente.", "danger")
                        return render_template('adicionar_produtos.html', form=form)
                else:
                    flash("Nenhuma imagem foi enviada.", "warning")
                    return render_template('adicionar_produtos.html', form=form)
            else:
                flash("Por favor, envie uma imagem do produto.", "warning")
                return render_template('adicionar_produtos.html', form=form)
        else:
            print("Formulário inválido:", form.errors)  # Debug
            flash("Erro no formulário. Verifique os campos e tente novamente.", "danger")
            return render_template('adicionar_produtos.html', form=form)

    # Para GET, renderiza o template HTML do formulário
    return render_template('adicionar_produtos.html', form=form)


from datetime import datetime

@app.route('/realizar-venda', methods=['GET', 'POST'])
def realizar_venda():
    if request.method == 'POST':
        form = VendaForm(data=request.form)

        if form.validate():
            # Verificar se o cliente existe
            cliente = Cliente.query.get(form.cliente_id.data)
            if not cliente:
                flash("Cliente não encontrado.", "danger")
                return redirect(url_for('realizar_venda'))

            # Verificar se o produto existe
            produto = Produto.query.get(form.produto_id.data)
            if not produto:
                flash("Produto não encontrado.", "danger")
                return redirect(url_for('realizar_venda'))

            # Verificar se há estoque suficiente
            if produto.quantidade < form.quantidade_vendida.data:
                flash("Estoque insuficiente.", "danger")
                return redirect(url_for('realizar_venda'))

            # Adiciona a nova venda
            new_venda = Venda(
                cliente_id=form.cliente_id.data,
                produto_id=form.produto_id.data,
                quantidade_vendida=form.quantidade_vendida.data,
                # A data será automaticamente preenchida pela propriedade `default=datetime.utcnow`
            )

            produto.quantidade -= form.quantidade_vendida.data  # Atualiza a quantidade em estoque
            db.session.add(new_venda)
            db.session.commit()

            flash("Venda registrada com sucesso!", "success")
            return redirect(url_for('realizar_venda'))
        else:
            flash("Erro de validação. Verifique os dados e tente novamente.", "danger")

    # Para GET, renderiza o formulário
    data_atual = datetime.utcnow().strftime('%Y-%m-%d')  # Data atual formatada
    return render_template('realizar_venda.html', data_atual=data_atual)



@app.route('/vendas', methods=['GET'])
def get_vendas():
    vendas = Venda.query.all()
    vendas_list = [{
        'id': venda.id,
        'cliente_id': venda.cliente_id,
        'produto_id': venda.produto_id,
        'quantidade_vendida': venda.quantidade_vendida
    } for venda in vendas]
    return jsonify(vendas_list), 200


@app.route('/front/clientes', methods=['GET'])
def get_clientes():
    clientes = Cliente.query.all()
    clientes_list = [{
        'id': cliente.id,
        'nome': cliente.nome,
        'idade': cliente.idade,
        'cpf': cliente.cpf,
        'email': cliente.email,
        'rua': cliente.rua,
        'numero': cliente.numero,
        'complemento': cliente.complemento,
        'bairro': cliente.bairro,
        'cidade': cliente.cidade,
        'estado': cliente.estado,
        'cep': cliente.cep
    } for cliente in clientes]
    return render_template('clientes.html', clientes=clientes_list)


@app.route('/detalhes-cliente/<int:id>', methods=['GET'])
def view_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        flash("Cliente não encontrado.", "error")
        return redirect(url_for('get_clientes'))

    return render_template('detalhes_cliente.html', cliente=cliente)



@app.route('/detalhes-produto/<int:id>', methods=['GET'])
def view_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        flash("Produto não encontrado.", "error")
        return redirect(url_for('get_produtos'))

    # Manipula o caminho da imagem, utilizando um placeholder caso a imagem seja None
    produto_imagem = os.path.basename(produto.imagem) if produto.imagem else 'placeholder/placeholder.png'

    return render_template('detalhes_produto.html', produto=produto, produto_imagem=produto_imagem)




@app.route('/front/produtos', methods=['GET'])
def get_produtos():
    produtos = Produto.query.all()
    produtos_list = [{
        'id': produto.id,
        'nome': produto.nome,
        'preco': produto.preco,
        'quantidade': produto.quantidade,
        'descricao': produto.descricao,
        'imagem': url_for('static', filename=f'uploads/{os.path.basename(produto.imagem)}') if produto.imagem else url_for('static', filename='uploads/placeholder/placeholder.png')  # Use o placeholder se a imagem for None
    } for produto in produtos]
    return render_template('produtos.html', produtos=produtos_list)

#PAGINA DE PUT CLIENTE

@app.route('/clientes/<int:id>', methods=['GET', 'POST'])
def update_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        flash("Cliente não encontrado.", "error")
        return redirect(url_for('/front/clientes'))

    form = ClienteForm(obj=cliente)  # Carrega dados atuais do cliente no formulário

    if request.method == 'POST':
        # Atualiza dados usando os dados enviados no formulário
        form = ClienteForm(data=request.form)

        if form.validate():
            cliente.nome = form.nome.data
            cliente.idade = form.idade.data
            cliente.cpf = form.cpf.data
            cliente.email = form.email.data
            cliente.rua = form.rua.data
            cliente.numero = form.numero.data
            cliente.complemento = form.complemento.data
            cliente.bairro = form.bairro.data
            cliente.cidade = form.cidade.data
            cliente.estado = form.estado.data
            cliente.cep = form.cep.data

            db.session.commit()
            flash("Cliente atualizado com sucesso!", "success")

            #DIVIDA TECNICA

            #return redirect(url_for('some_other_route'))  # GO TO HOME AFT TIMEOUT OU NAO
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Erro no campo {field}: {error}", "error")

    return render_template('editar_cliente.html', form=form, cliente_id=id)


#EDITANDO O PRODUTO

@app.route('/produtos/<int:id>', methods=['GET', 'POST'])
def update_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        flash("Produto não encontrado.", "error")
        return redirect(url_for('get_produtos'))

    # Inicializa o formulário com os dados do produto
    form = ProdutoForm(obj=produto)

    if request.method == 'POST':
        if form.validate_on_submit():
            # Atualiza os dados do produto com os dados do formulário
            produto.nome = form.nome.data
            produto.preco = form.preco.data
            produto.quantidade = form.quantidade.data
            produto.descricao = form.descricao.data

            # Verifica se uma nova imagem foi carregada
            if 'imagem' in request.files:
                imagem = request.files['imagem']
                if imagem.filename != '':  # Verifica se a imagem foi enviada
                    nome_imagem = secure_filename(imagem.filename)
                    caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem)

                    # Tenta salvar a imagem no caminho especificado
                    try:
                        imagem.save(caminho_imagem)
                        produto.imagem = caminho_imagem  # Atualiza o caminho da imagem no banco de dados
                        print(f"Imagem salva em {caminho_imagem}.")  # Debug
                    except Exception as e:
                        print(f"Erro ao salvar a imagem: {e}")
                        flash("Erro ao salvar a imagem. Tente novamente.", "danger")
                        return render_template('editar_produto.html', form=form, produto=produto)

            # Atualiza o banco de dados com os dados do produto
            try:
                db.session.commit()
                flash("Produto atualizado com sucesso!", "success")
                return redirect(url_for('get_produtos'))  # Redireciona para a página de listagem de produtos
            except IntegrityError as e:
                db.session.rollback()
                print(f"Erro ao atualizar produto: {e}")  # Debug
                flash("Erro ao atualizar produto. Verifique os dados e tente novamente.", "danger")
                return render_template('editar_produto.html', form=form, produto=produto)

        else:
            print("Formulário inválido:", form.errors)  # Debug
            flash("Erro no formulário. Verifique os campos e tente novamente.", "danger")

    # Para GET, renderiza o template HTML do formulário
    return render_template('editar_produto.html', form=form, produto=produto, produto_id=id)


@app.route('/deletar-clientes/<int:id>', methods=['POST'])
def deletar_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        flash("Cliente não encontrado.", "error")
        return redirect(url_for('get_clientes'))  # Redireciona para a lista de clientes

        # Desvincular as vendas do cliente
    vendas = Venda.query.filter_by(cliente_id=id).all()
    for venda in vendas:
        db.session.delete(venda)  # Deleta cada venda associada ao cliente

    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente deletado com sucesso!", "success")

    return redirect(url_for('get_clientes'))

@app.route('/deletar-produto/<int:id>', methods=['POST'])
def deletar_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        flash("Produto não encontrado.", "error")
        return redirect(url_for('get_produtos'))  # Redireciona para a lista de PRODUTOS

    # Desvincular todas as vendas relacionadas ao produto
    vendas_relacionadas = Venda.query.filter_by(produto_id=id).all()
    for venda in vendas_relacionadas:
        db.session.delete(venda)

    # Agora deletar o produto
    db.session.delete(produto)
    db.session.commit()
    flash("Cliente deletado com sucesso!", "success")

    return redirect(url_for('get_produtos'))


@app.route('/relatorio-vendas', methods=['GET'])
def relatorio_vendas():
    vendas = db.session.query(Venda, Cliente, Produto).join(Cliente).join(Produto).all()

    vendas_por_cliente = {}
    vendas_por_produto = {}

    # Agrupando as vendas por cliente
    for venda, cliente, produto in vendas:
        # Vendas por cliente
        if cliente.id not in vendas_por_cliente:
            vendas_por_cliente[cliente.id] = {'nome': cliente.nome, 'vendas': {}}

        if produto.id not in vendas_por_cliente[cliente.id]['vendas']:
            vendas_por_cliente[cliente.id]['vendas'][produto.id] = {'produto_nome': produto.nome,
                                                                    'quantidade_vendida': 0}

        vendas_por_cliente[cliente.id]['vendas'][produto.id]['quantidade_vendida'] += venda.quantidade_vendida

        # Vendas por produto
        if produto.id not in vendas_por_produto:
            vendas_por_produto[produto.id] = {'nome': produto.nome, 'vendas': {}}

        if cliente.id not in vendas_por_produto[produto.id]['vendas']:
            vendas_por_produto[produto.id]['vendas'][cliente.id] = {'cliente_nome': cliente.nome,
                                                                    'quantidade_vendida': 0}

        vendas_por_produto[produto.id]['vendas'][cliente.id]['quantidade_vendida'] += venda.quantidade_vendida

    return render_template('relatorio_vendas.html', vendas_por_cliente=vendas_por_cliente,
                           vendas_por_produto=vendas_por_produto)



@app.route('/gerar-csv', methods=['GET'])
def gerar_csv():
    # Consultar as vendas por data
    vendas = db.session.query(Venda).join(Cliente).join(Produto).all()

    # Organizar as vendas diárias e acumuladas
    vendas_diarias = {}
    vendas_acumuladas = {}

    for venda in vendas:
        data_venda = venda.data_venda.date()  # Apenas a data (sem o horário)
        quantidade = venda.quantidade_vendida
        produto_nome = venda.produto.nome
        cliente_nome = venda.cliente.nome

        # Vendas diárias
        if data_venda not in vendas_diarias:
            vendas_diarias[data_venda] = []
        vendas_diarias[data_venda].append(
            {'cliente_nome': cliente_nome, 'produto_nome': produto_nome, 'quantidade': quantidade})

        # Vendas acumuladas
        if data_venda not in vendas_acumuladas:
            vendas_acumuladas[data_venda] = 0
        vendas_acumuladas[data_venda] += quantidade

    # Criar o CSV com as vendas diárias
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Data', 'Cliente', 'Produto', 'Quantidade'])
    for data_venda, vendas in vendas_diarias.items():
        for venda in vendas:
            writer.writerow([data_venda, venda['cliente_nome'], venda['produto_nome'], venda['quantidade']])

    # Rewind para leitura
    output.seek(0)

    # Definir o cabeçalho para download
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=vendas_diarias.csv"})

@app.route('/')
def home():
    return render_template('home.html')





ALLOWED_EXTENSIONS = {'csv'}

# Função para verificar se a extensão é válida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-csv', methods=['GET', 'POST'])
def upload_csv():
    if request.method == 'POST':
        # Verifique se o arquivo foi enviado
        if 'csv_file' not in request.files:
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(request.url)

        file = request.files['csv_file']

        # Se o usuário não escolher um arquivo
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(request.url)

        # Verifique se o arquivo tem uma extensão válida para CSV
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['CSV_FOLDER'], filename)  # Usando 'CSV_FOLDER' configurado

            # Salve o arquivo
            file.save(file_path)

            # Aqui você pode adicionar lógica para processar o CSV (ex: leitura dos dados)
            flash('Arquivo CSV enviado com sucesso!', 'success')
            return redirect(url_for('home'))  # Redireciona para a página inicial (ou onde achar necessário)

        else:
            flash('Arquivo inválido. Por favor, envie um arquivo CSV.', 'error')
            return redirect(request.url)

    return render_template('upload_csv.html')




import csv
import matplotlib.pyplot as plt
import pandas as pd

def gerar_grafico_vendas(csv_file):
    # Ler o arquivo CSV
    vendas = pd.read_csv(csv_file)

    # Agrupar as vendas por data e produto
    vendas['Data'] = pd.to_datetime(vendas['Data'], format='%Y-%m-%d')
    vendas_diarias = vendas.groupby('Data')['Quantidade'].sum()

    # Gerar o gráfico de vendas diárias
    plt.figure(figsize=(10, 6))
    vendas_diarias.plot(kind='bar', color='skyblue')
    plt.title('Vendas Diárias')
    plt.xlabel('Data')
    plt.ylabel('Quantidade Vendida')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Exibir o gráfico
    plt.show()

    # Gerar o gráfico acumulado
    vendas['Acumulada'] = vendas_diarias.cumsum()

    plt.figure(figsize=(10, 6))
    vendas['Acumulada'].plot(kind='line', color='orange', marker='o')
    plt.title('Vendas Acumuladas')
    plt.xlabel('Data')
    plt.ylabel('Quantidade Acumulada')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Exibir o gráfico
    plt.show()











if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
