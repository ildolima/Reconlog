from app import app, db
from sqlalchemy import text

with app.app_context():
    print("Atualizando tabela de Pedidos...")
    try:
        with db.engine.connect() as conn:
            # Adiciona colunas novas se não existirem
            # Nota: O comando ADD COLUMN falha silenciosamente se já existir em alguns drivers, 
            # mas vamos tentar um por um por segurança.
            try: conn.execute(text("ALTER TABLE pedido_compra ADD COLUMN solicitacao_origem_id INT"))
            except: pass
            
            try: conn.execute(text("ALTER TABLE pedido_compra ADD COLUMN aprovado_por_id INT"))
            except: pass
            
            try: conn.execute(text("ALTER TABLE pedido_compra ADD COLUMN data_aprovacao DATETIME"))
            except: pass
            
            try: conn.execute(text("ALTER TABLE pedido_compra ADD COLUMN observacoes TEXT"))
            except: pass

            conn.commit()
        print("Sucesso! Tabela PedidoCompra atualizada para suportar aprovações.")
    except Exception as e:
        print(f"Erro (ignore se for 'duplicate column'): {e}")