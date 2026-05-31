from fastapi import APIRouter, Depends, Request

from app.core.deps import get_current_user, require_permission
from app.models.permission import (
    FeatureResponse,
    MyPermissionsResponse,
    RolePermissionsMatrixResponse,
    RolePermissionsUpdate,
)
from app.services import permission_service

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("/me", response_model=MyPermissionsResponse)
async def get_my_permissions(current_user: dict = Depends(get_current_user)):
    return await permission_service.get_permissions_for_role(current_user["role"])


@router.get("/features", response_model=list[FeatureResponse])
async def list_features(_: dict = Depends(require_permission("admin.permissions.manage"))):
    return await permission_service.list_features()


@router.get("/roles", response_model=RolePermissionsMatrixResponse)
async def get_role_permissions(_: dict = Depends(require_permission("admin.permissions.manage"))):
    return await permission_service.get_permissions_matrix()


@router.put("/roles/{role}", response_model=RolePermissionsMatrixResponse)
async def update_role_permissions(
    role: str,
    body: RolePermissionsUpdate,
    request: Request,
    current_user: dict = Depends(require_permission("admin.permissions.manage")),
):
    return await permission_service.update_role_permissions(
        role=role,
        permission_keys=body.permissions,
        actor=current_user,
        request=request,
    )


@router.post("/roles/{role}/reset-defaults", response_model=RolePermissionsMatrixResponse)
async def reset_role_permissions(
    role: str,
    request: Request,
    current_user: dict = Depends(require_permission("admin.permissions.manage")),
):
    return await permission_service.reset_role_defaults(
        role=role,
        actor=current_user,
        request=request,
    )
