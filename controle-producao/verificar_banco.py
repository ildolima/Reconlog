from app import app, db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    tabelas = inspector.get_table_names()
    print("\n=== TABELAS ENCONTRADAS ===")
    for tabela in tabelas:
        print(f"- {tabela}")
    
    if 'fornecedor' in tabelas and 'tipo_fornecedor' in tabelas:
        print("\nSUCCESS: Módulo de Compras instalado corretamente!")
    else:
        print("\nERRO: Tabelas de Compras não encontradas.")