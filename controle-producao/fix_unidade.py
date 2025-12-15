from app import app, db
from sqlalchemy import text

with app.app_context():
    print("Atualizando tabela de produtos...")
    try:
        # Comando SQL direto para criar a coluna
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE produto ADD COLUMN unidade VARCHAR(10) DEFAULT 'UN'"))
            conn.commit()
        print("Sucesso! Coluna 'unidade' criada.")
    except Exception as e:
        print(f"Aviso (pode ser que já exista): {e}")