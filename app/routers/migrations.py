from fastapi import APIRouter, Depends, HTTPException, status
from app.core.deps import require_roles
from app.services.migration_service import MigrationService

router = APIRouter(prefix="/system", tags=["system"])

@router.post("/migrate", status_code=status.HTTP_200_OK)
async def run_system_migrations(
    admin: dict = Depends(require_roles("admin"))
):
    """
    Executa as migrações de banco de dados pendentes.
    Requer privilégios de administrador.
    """
    result = await MigrationService.run_migrations()
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )
    return result

@router.get("/migrations", status_code=status.HTTP_200_OK)
async def list_migrations(
    admin: dict = Depends(require_roles("admin"))
):
    """
    Lista as migrações executadas e pendentes.
    Requer privilégios de administrador.
    """
    import os
    from app.services.migration_service import MIGRATIONS_DIR
    
    executed = await MigrationService.get_executed_migrations()
    
    files = []
    if os.path.exists(MIGRATIONS_DIR):
        files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql")])
    
    return {
        "executed": executed,
        "pending": [f for f in files if f not in executed],
        "all": files
    }
