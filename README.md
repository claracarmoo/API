# E-commerce API  

Uma API desenvolvida em **Python com Flask** para operações essenciais de um e-commerce, incluindo gerenciamento de produtos e fluxo de compra com integração de pagamento.  

## Funcionalidades  

- **Adicionar produto** ao catálogo  
- **Remover produto** do catálogo  
- **Detalhar produto** com informações completas  
- **Adicionar produto ao carrinho**  
- **Realizar compra** e processar pagamento  
- **Receber status da compra**, indicando sucesso ou erro  

## Tecnologias Utilizadas  

- **Python**  
- **Flask**  
- **Banco de Dados** (SQLAlchemy)  
- **Sistema de Pagamento** (Stripe) 

## Como Executar  

1. Clone este repositório:  
   ```sh
   git clone https://github.com/seu-usuario/nome-do-repositorio.git
   cd nome-do-repositorio
   ```  
2. Crie um ambiente virtual e instale as dependências:  
   ```sh
   python -m venv venv  
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt  
   ```  
3. Execute a aplicação:  
   ```sh
   flask run
   ```  

## 🔗 Endpoints  

### 📌 Produtos  

- **POST** `/produtos` → Adiciona um novo produto  
- **DELETE** `/produtos/{id}` → Remove um produto  
- **GET** `/produtos/{id}` → Obtém detalhes de um produto  

### 🛍️ Compra  

- **POST** `/carrinho` → Adiciona produto ao carrinho  
- **POST** `/comprar` → Finaliza a compra e processa pagamento  
- **GET** `/status/{id_pedido}` → Retorna status do pedido  

## 📬 Retornos da API  

- **200 OK** → Sucesso na operação  
- **400 Bad Request** → Erro na requisição (ex: dados inválidos)  
- **404 Not Found** → Produto ou pedido não encontrado  
- **500 Internal Server Error** → Erro no servidor  

## 📜 Licença  

Este projeto está sob a licença [MIT](LICENSE).  

---

Se quiser personalizar mais, me avisa!
