from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, FileField
from wtforms.fields.datetime import DateField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Optional, Regexp

# Formulário de Cliente
class ClienteForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(min=3, max=100)])
    idade = IntegerField('Idade', validators=[DataRequired(), NumberRange(min=0, max=999)])
    cpf = StringField('CPF', validators=[
        DataRequired(),
        Length(min=11, max=14, message="CPF deve ter 11 caracteres ou 14 no formato 'XXX.XXX.XXX-XX'."),
        Regexp(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{11}$', message="Formato de CPF inválido.")
    ])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    rua = StringField('Rua', validators=[DataRequired(), Length(max=100)])
    numero = StringField('Número', validators=[DataRequired(), Length(max=10)])
    complemento = StringField('Complemento', validators=[Optional(), Length(max=50)])
    bairro = StringField('Bairro', validators=[DataRequired(), Length(max=50)])
    cidade = StringField('Cidade', validators=[DataRequired(), Length(max=50)])
    estado = StringField('Estado', validators=[DataRequired(), Length(min=0, max=30)])
    cep = StringField('CEP', validators=[DataRequired(), Length(min=8, max=10)])


# Formulário de Produto
class ProdutoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(min=3)])
    preco = FloatField('Preço', validators=[DataRequired(), NumberRange(min=0.01)])
    quantidade = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=0)])
    descricao = StringField('Descrição', validators=[Optional()])
    imagem = FileField('Imagem', validators=[Optional()])


# Formulário de Venda
class VendaForm(FlaskForm):
    cliente_id = IntegerField('ID do Cliente', validators=[DataRequired()])
    produto_id = IntegerField('ID do Produto', validators=[DataRequired()])
    quantidade_vendida = IntegerField('Quantidade Vendida', validators=[DataRequired(), NumberRange(min=1)])
    data_venda = DateField('Data da Venda', format='%Y-%m-%d', default=datetime.today)