import os
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from db.session import get_db

router = APIRouter(prefix="/api")


@router.get("/schema")
def get_schema_summary(db: Session = Depends(get_db)):
    """Get a summary of the current database structure."""
    try:
        inspector = inspect(db.bind)
        
        # Get database name from connection
        database_name = db.bind.url.database or "qdra"
        
        # Use 'public' schema for PostgreSQL
        schema_name = "public"
        
        result = {
            database_name: {
                schema_name: {}
            }
        }
        
        # Get all tables in the schema
        table_names = inspector.get_table_names(schema=schema_name)
        
        for table_name in table_names:
            columns = inspector.get_columns(table_name, schema=schema_name)
            primary_keys = inspector.get_pk_constraint(table_name, schema=schema_name)
            foreign_keys = inspector.get_foreign_keys(table_name, schema=schema_name)
            
            column_list = []
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                is_pk = col_name in primary_keys['constrained_columns']
                
                # Check if this column is a foreign key
                fk_info = ""
                for fk in foreign_keys:
                    if col_name in fk['constrained_columns']:
                        ref_table = fk['referred_table']
                        ref_columns = fk['referred_columns']
                        if ref_columns:
                            fk_info = f" -> FK: {ref_table}.{ref_columns[0]}"
                        else:
                            fk_info = f" -> FK: {ref_table}"
                        break
                
                column_list.append(f"{col_name} -> {col_type} -> PK: {is_pk}{fk_info}")
            
            result[database_name][schema_name][table_name] = column_list
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
