from flask import Flask, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import stripe  # Biblioteca do Stripe

# Configuração inicial
app = Flask(__name__)
app.config['SECRET_KEY'] = "sk_test_51R34kgPVX1I0v5qWfu8slN8HDNYzUKs8biV0wLsUBjvLo2K7cxLcPb56e7L3HvSaodAinQspYoQIlpds76oTxM60001yNzPYlC"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização do banco e login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configuração do Stripe
stripe.api_key = "sk_test_51R34kgPVX1I0v5qWfu8slN8HDNYzUKs8biV0wLsUBjvLo2K7cxLcPb56e7L3HvSaodAinQspYoQIlpds76oTxM60001yNzPYlC"

# Modelos do Banco de Dados
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), nullable=False, unique=True)
    password = db.Column(db.String(15), nullable=False)
    cart = db.relationship('CartItem', backref='user', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="Pendente")  # "Pendente", "Pago", "Cancelado"
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rotas de Autenticação
@app.route('/login', methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get("username")).first()
    if user and data.get("password") == user.password:
        login_user(user)
        return jsonify({"message": "Login realizado com sucesso!"})
    return jsonify({"message": "Credenciais inválidas."}), 401

@app.route('/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout realizado com sucesso!"})

# Rotas de Produto
@app.route('/api/products/add', methods=["POST"])
@login_required
def add_product():
    data = request.json
    if 'name' in data and 'price' in data:
        product = Product(name=data["name"], price=data["price"], description=data.get("description", ""))
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Produto adicionado com sucesso!"})
    return jsonify({"message": "Dados inválidos!"}), 400

@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{ "id": p.id, "name": p.name, "price": p.price, "description": p.description } for p in products])

# Rotas de Carrinho
@app.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if product:
        cart_item = CartItem(user_id=current_user.id, product_id=product.id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({'message': 'Item adicionado ao carrinho com sucesso!'})
    return jsonify({'message': 'Produto não encontrado!'}), 404

@app.route('/api/cart', methods=['GET'])
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    cart_content = [{"id": c.id, "product_id": c.product_id} for c in cart_items]
    return jsonify(cart_content)

@app.route('/api/cart/checkout', methods=['POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return jsonify({'message': 'Carrinho vazio!'}), 400

    total_price = sum(Product.query.get(item.product_id).price for item in cart_items)

    # Criar pedido no banco antes do pagamento
    new_order = Order(user_id=current_user.id, total_price=total_price, status="Pendente")
    db.session.add(new_order)
    db.session.commit()

    # Adicionar os itens ao pedido
    for item in cart_items:
        order_item = OrderItem(order_id=new_order.id, product_id=item.product_id, quantity=1)
        db.session.add(order_item)
    db.session.commit()

    # Criar sessão do Stripe com o order_id na URL
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'brl',
                'product_data': {'name': Product.query.get(item.product_id).name},
                'unit_amount': int(Product.query.get(item.product_id).price * 100),
            },
            'quantity': 1,
        } for item in cart_items],
        mode='payment',
        success_url=f'http://localhost:5001/success?order_id={new_order.id}',
        cancel_url=f'http://localhost:5001/cancel?order_id={new_order.id}',
    )

    return jsonify({'checkout_url': session.url})

@app.route('/success', methods=['GET'])
def payment_success():
    order_id = request.args.get('order_id')
    order = Order.query.get(order_id)

    if order:
        order.status = "Pago"
        db.session.commit()

        # 🔥 Limpar o carrinho do usuário após a compra
        CartItem.query.filter_by(user_id=order.user_id).delete()
        db.session.commit()

        return jsonify({'message': 'Pagamento realizado com sucesso! Pedido registrado e carrinho esvaziado.'})
    
    return jsonify({'message': 'Pedido não encontrado!'}), 404



@app.route('/cancel', methods=['GET'])
def payment_cancel():
    order_id = request.args.get('order_id')
    order = Order.query.get(order_id)

    if order:
        order.status = "Cancelado"
        db.session.commit()
        return jsonify({'message': 'Pagamento cancelado e pedido atualizado!'})
    
    return jsonify({'message': 'Pedido não encontrado!'}), 404


# Criar tabelas no banco de dados
with app.app_context():
    db.create_all()

# Rodar a aplicação
if __name__ == "__main__":
    app.run(debug=True, port=5001)
