from sqlmodel import SQLModel
from app.auth.database import engine

# Import all model modules to ensure their tables are registered with SQLModel.metadata
# This ensures that all tables defined across different modules are created.
from app.auth import (
    models as auth_models_module,
)  # Alias to avoid potential name clashes if not used
from app.students import models as student_models_module  # Alias

# Import integrations models to ensure they are registered
from app.integrations import model as integration_models_module

# Import admin models
from app.admin import models as admin_models_module

# If you have an integrations module with its own SQLModels, import it too:
# from app.integrations import models as integration_models_module

# The act of importing the modules where SQLModels are defined is usually enough
# for them to be registered with SQLModel.metadata.
# The aliased imports above ensure the modules are loaded.

print("Attempting to create database tables...")
print(f"Registered tables: {list(SQLModel.metadata.tables.keys())}")

# This will create tables for all models imported directly or indirectly
# and registered with SQLModel.metadata by the time this line is executed.
SQLModel.metadata.create_all(engine)
print("Database tables should be created (if they didn't already exist).")
print(
    "Ensure all SQLModel definitions were imported prior to this script execution for full effect."
)
