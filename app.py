# estou importando a classe flask do "arquivo" flask
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
# instanciando a classe Flask 
app =  Flask(__name__)
app.config ['SECRET_KEY'] = "minha chave_123"
#configuração onde fica o nosso banco. Passar um caminho de arquivo para ele 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Evita warnings

login_manager = LoginManager()
# Inicializando o banco de dados
db = SQLAlchemy(app)
login_manager.init_app(app) # recebe a aplicação
login_manager.login_view = 'login' #passando a rota onde o login manager ira funcionar

#Modelagem serve como molde, as informações são armazenadas em linha e colunas. A linha é o registro e a coluna é é a informação armazenadas
class User(db.Model, UserMixin):
    id = db.Column (db.Integer, primary_key=True)
    username = db.Column(db.String(15), nullable=False, unique=True)
    password  = db.Column(db.String(15), nullable=False)
    cart = db.relationship('CartItem', backref='user', lazy = True ) # db.relationship cria a relação com outra classe / backref serve para associar um item no carrinho / lazy diz que toda vez q recupera um usuario, n quero recuperar todos os itens que ele tem cadastrado diretamente

    
class Product (db.Model):
   id = db.Column (db.Integer, primary_key=True) #primary key diz que todo produto tem um id diferente 
   name = db.Column (db.String(120), nullable=False) #nullable faz com que o nome do produto seja obrigatorio
   price = db.Column (db.Float, nullable=False)
   description = db.Column (db.Text, nullable=True) #o uso de text faz com que n precise de um limite de caracteres

class CartItem(db.Model): 
     id = db.Column (db.Integer, primary_key=True)
     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)# referente ao usuario que esta tentando adicionar o item nesse carrinho
     product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable = False) #ForeignKey faz referencia a uma variavel primaria de outra tabela. 
     

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
#Criação de login e autenticação de usuario
@app.route('/login', methods=["POST"])
def login():
    data = request.json
    
    user = User.query.filter_by(username=data.get("username")).first() # retorna todos os usuarios que tem determinado usarname, o retorno sera uma lista
    
    if user and data.get("password") == user.password:
            login_user(user)
            return jsonify({"message": "logged in successfuly"})
    return jsonify({"message": "Unauthorized. Invalid credentials"}), 401
   
@app.route('/logout', methods=["POST"])
@login_required #diz que preciso estar autenticado para sair
def logout():
    logout_user()
    return jsonify({"message": "logout successfuly"})
# Criar as tabelas no banco de dados
@app.route('/api/products/add', methods=["POST"]) 
@login_required
def add_product():
    data = request.json
    if 'name' in data and 'price' in data:
        product = Product(name=data["name"], price=data["price"],description=data.get("description", "")) #ambas as formas de puxar o dado que o cliente pediu estão certas, mas a forma de data["parametro"] caso não exista ele dá um erro, e utilizando o get, ele vai dizer a segunda opção que lhe foi passado, nesse caso, as aspas vazias 
        db.session.add(product) #estou adcionando o meu objeto product ao banco de dados 
        db.session.commit() #confirmando a alteração
        return jsonify({"message":"Product added successfully"}) #jsonify faz com que a mensagem não apareça como html, mas sim em formato json
    return jsonify({"message":"Invalid product data"}), 400 
    
@app.route ('/api/products/delete/<int:product_id>', methods=["DELETE"])
@login_required
def delete_product(product_id):
    product=Product.query.get(product_id) #query serve para pesquisar o produto no banco de dados
    if product: #estou dizendo que se o produto for diferente de nulo, ou seja se ele existir. mas o "if product:" tambem serve e tem o mesmo objetivo
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message":"Product deleted successfully"})
    return jsonify({"message":"Product not found"}), 404

@app.route('/api/products/<int:product_id>', methods=["GET"])
def get_products_details(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price
        })
    return jsonify({"message": "Product not found"}), 404

@app.route('/api/products/update/<int:product_id>', methods=["PUT"])
@login_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}),404
    
    data = request.json  
    if 'name' in data:
        product.name = data['name']
    
    if 'price' in data:
        product.price = data['price']
    
    if 'description' in data:
        product.description = data['description']
 
    db.session.commit()   
    return jsonify({"message": "Product updated successfuly"})

@app.route('/api/products', methods=['GET'])
def get_product ():
    products = Product.query.all()
    print(products)
    product_list = []
    for product in products:
        product_data = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price 
        }
        product_list.append(product_data)

    return jsonify(product_list)

#Checkout 
@app.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    user = User.query.get(int(current_user.id))#verifiando se o usuario esta logado. Se o usuario não for encontrado, essa linha sera como nulo
    product = Product.query.get(product_id)
   
    if user and product:
        cart_item = CartItem(user_id=user.id, product_id = product.id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify ({'message': 'Item added to the cart successfully'}) 
    return jsonify ({'message': 'Faild to add item to the cart'}), 400

@app.route('/api/cart/remove/<int:product_id>', methods =['DELETE'])
@login_required 
def remove_from_cart(product_id):
    cart_item= CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify ({'message': 'Item removed successfuly'})
    return jsonify ({'message': ' Failed to remove item'}),400

@app.route('/api/cart', methods=['GET'])
@login_required
def view_cart():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart #recupera o carrinho do usuario. retorna uma lista de itens 
    cart_content = []
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        cart_content.append({
            "id": cart_item.id,
            "user_id": cart_item.user_id,
            "product_id": cart_item.product_id,
            "product_name": product.name
        })
    return jsonify(cart_content)

@app.route('/api/cart/checkout', methods=['POST'])
@login_required
def checkout():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart
    for cart_item in cart_items:
        db.session.delete(cart_item)
    db.session.commit()
    return jsonify ({'message': 'Checkout successfully. Cart has been cleared'})

# para que a API se torne disponivel para aplicações
if __name__ == "__main__":  #vem acompanhado por uma condição
  app.run(debug=True, port=5001) #estamos ativando o modo depuração 