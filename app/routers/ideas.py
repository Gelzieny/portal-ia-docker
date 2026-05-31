from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.core.deps import require_permission
from app.models.idea import (
    IdeaCommentCreate,
    IdeaCommentModerationDecision,
    IdeaCommentResponse,
    IdeaCurationDecision,
    IdeaCreate,
    IdeaDetailResponse,
    IdeaModerationStatus,
    IdeaReaction,
    IdeaRoadmapUpdate,
    IdeaSimilarResponse,
    IdeaStatus,
    IdeaTopicResponse,
    IdeaUpdate,
    IdeaVersionCreate,
    IdeaVersionResponse,
    IdeaVersionUpdate,
    RoadmapVersionResponse,
)
from app.models.pagination import PaginatedResponse
from app.services import idea_service

router = APIRouter(prefix="/ideas", tags=["ideas"])
roadmap_router = APIRouter(prefix="/roadmap", tags=["roadmap"])
admin_router = APIRouter(prefix="/admin/ideas", tags=["admin-ideas"])


@router.get("/topics", response_model=list[IdeaTopicResponse])
async def list_topics(_: dict = Depends(require_permission("ideas.portal.view"))):
    return await idea_service.list_topics()


@router.get("/versions", response_model=list[IdeaVersionResponse])
async def list_versions(_: dict = Depends(require_permission("roadmap.view"))):
    return await idea_service.list_versions()


@roadmap_router.get("", response_model=list[RoadmapVersionResponse])
async def get_roadmap(current_user: dict = Depends(require_permission("roadmap.view"))):
    return await idea_service.get_public_roadmap(user_id=current_user["id"])


@router.get("", response_model=PaginatedResponse[IdeaDetailResponse])
async def list_public_ideas(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=120),
    topic_id: UUID | None = None,
    idea_status: IdeaStatus | None = Query(default=None),
    sort_by: str = Query(default="trending", pattern="^(trending|latest|most_votes|least_votes|most_comments)$"),
    current_user: dict = Depends(require_permission("ideas.portal.view")),
):
    items, total = await idea_service.list_public_ideas(
        user_id=current_user["id"],
        page=page,
        page_size=page_size,
        search=search,
        topic_id=topic_id,
        status_filter=idea_status.value if idea_status else None,
        sort_by=sort_by,
    )
    return PaginatedResponse[IdeaDetailResponse].build(items, total, page, page_size)


@router.get("/similar", response_model=list[IdeaSimilarResponse])
async def find_similar_ideas(
    title: str = Query(..., min_length=3, max_length=240),
    description: str = Query(default="", max_length=2000),
    topic_ids: list[UUID] = Query(default=[]),
    limit: int = Query(default=5, ge=1, le=10),
    _: dict = Depends(require_permission("ideas.create")),
):
    return await idea_service.find_similar_ideas(
        title=title,
        description=description,
        topic_ids=topic_ids,
        limit=limit,
    )


@router.get("/mine", response_model=PaginatedResponse[IdeaDetailResponse])
async def list_my_ideas(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    moderation_status: IdeaModerationStatus | None = None,
    search: str | None = Query(default=None, max_length=120),
    current_user: dict = Depends(require_permission("ideas.own.manage")),
):
    items, total = await idea_service.list_my_ideas(
        user_id=current_user["id"],
        page=page,
        page_size=page_size,
        moderation_status=moderation_status.value if moderation_status else None,
        search=search,
    )
    return PaginatedResponse[IdeaDetailResponse].build(items, total, page, page_size)


@router.post("", response_model=IdeaDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_idea(
    body: IdeaCreate,
    current_user: dict = Depends(require_permission("ideas.create")),
):
    return await idea_service.create_idea(body=body, user_id=current_user["id"])


@router.get("/{idea_id}", response_model=IdeaDetailResponse)
async def get_idea(
    idea_id: UUID,
    current_user: dict = Depends(require_permission("ideas.portal.view")),
):
    return await idea_service.get_idea_detail(idea_id, current_user["id"])


@router.put("/{idea_id}", response_model=IdeaDetailResponse)
async def update_idea(
    idea_id: UUID,
    body: IdeaUpdate,
    current_user: dict = Depends(require_permission("ideas.own.manage")),
):
    return await idea_service.update_idea(idea_id=idea_id, body=body, user_id=current_user["id"])


@router.delete("/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idea(
    idea_id: UUID,
    current_user: dict = Depends(require_permission("ideas.own.manage")),
):
    await idea_service.delete_idea(idea_id=idea_id, user_id=current_user["id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{idea_id}/deletion-request", response_model=IdeaDetailResponse)
async def request_idea_deletion(
    idea_id: UUID,
    body: IdeaCurationDecision,
    request: Request,
    current_user: dict = Depends(require_permission("ideas.own.manage")),
):
    return await idea_service.request_idea_deletion(
        idea_id=idea_id,
        user_id=current_user["id"],
        reason=body.reason or "",
        request=request,
    )


@router.post("/{idea_id}/vote", response_model=IdeaDetailResponse)
async def add_vote(
    idea_id: UUID,
    current_user: dict = Depends(require_permission("ideas.vote")),
):
    return await idea_service.add_vote(idea_id=idea_id, user_id=current_user["id"])


@router.delete("/{idea_id}/vote", response_model=IdeaDetailResponse)
async def remove_vote(
    idea_id: UUID,
    current_user: dict = Depends(require_permission("ideas.vote")),
):
    return await idea_service.remove_vote(idea_id=idea_id, user_id=current_user["id"])


@router.get("/{idea_id}/comments", response_model=list[IdeaCommentResponse])
async def list_comments(
    idea_id: UUID,
    current_user: dict = Depends(require_permission("ideas.portal.view")),
):
    return await idea_service.list_comments(idea_id=idea_id, user_id=current_user["id"])


@router.post("/{idea_id}/comments", response_model=IdeaCommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    idea_id: UUID,
    body: IdeaCommentCreate,
    current_user: dict = Depends(require_permission("ideas.comment")),
):
    return await idea_service.create_comment(idea_id=idea_id, body=body, user_id=current_user["id"])


@router.post("/{idea_id}/comments/{comment_id}/reply", response_model=IdeaCommentResponse, status_code=status.HTTP_201_CREATED)
async def create_reply(
    idea_id: UUID,
    comment_id: UUID,
    body: IdeaCommentCreate,
    current_user: dict = Depends(require_permission("ideas.comment")),
):
    return await idea_service.create_reply(idea_id=idea_id, parent_id=comment_id, body=body, user_id=current_user["id"])


@router.post("/comments/{comment_id}/reactions", status_code=status.HTTP_200_OK)
async def set_comment_reaction(
    comment_id: UUID,
    reaction: IdeaReaction,
    current_user: dict = Depends(require_permission("ideas.comment.react")),
):
    return await idea_service.set_comment_reaction(comment_id=comment_id, reaction=reaction, user_id=current_user["id"])


@router.delete("/comments/{comment_id}/reactions/{reaction}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_comment_reaction(
    comment_id: UUID,
    reaction: IdeaReaction,
    current_user: dict = Depends(require_permission("ideas.comment.react")),
):
    await idea_service.remove_comment_reaction(comment_id=comment_id, reaction=reaction, user_id=current_user["id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_router.get("", response_model=PaginatedResponse[IdeaDetailResponse])
async def admin_list_ideas(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    moderation_status: IdeaModerationStatus | None = None,
    search: str | None = Query(default=None, max_length=120),
    _: dict = Depends(require_permission("ideas.curation.manage")),
):
    items, total = await idea_service.list_admin_ideas(
        page=page,
        page_size=page_size,
        moderation_status=moderation_status.value if moderation_status else None,
        search=search,
    )
    return PaginatedResponse[IdeaDetailResponse].build(items, total, page, page_size)


@admin_router.post("/{idea_id}/approve", response_model=IdeaDetailResponse)
async def admin_approve_idea(
    idea_id: UUID,
    body: IdeaCurationDecision,
    request: Request,
    current_user: dict = Depends(require_permission("ideas.curation.manage")),
):
    return await idea_service.approve_idea(
        idea_id=idea_id,
        reviewer_id=current_user["id"],
        reason=body.reason,
        request=request,
    )


@admin_router.post("/{idea_id}/reject", response_model=IdeaDetailResponse)
async def admin_reject_idea(
    idea_id: UUID,
    body: IdeaCurationDecision,
    request: Request,
    current_user: dict = Depends(require_permission("ideas.curation.manage")),
):
    return await idea_service.reject_idea(
        idea_id=idea_id,
        reviewer_id=current_user["id"],
        reason=body.reason or "",
        request=request,
    )


@admin_router.post("/{idea_id}/remove-policy-violation", response_model=IdeaDetailResponse)
async def admin_remove_policy_violation(
    idea_id: UUID,
    body: IdeaCurationDecision,
    request: Request,
    current_user: dict = Depends(require_permission("ideas.curation.manage")),
):
    return await idea_service.remove_policy_violation(
        idea_id=idea_id,
        reviewer_id=current_user["id"],
        reason=body.reason or "",
        request=request,
    )


@admin_router.post("/{idea_id}/deletion-request/approve", response_model=IdeaDetailResponse)
async def admin_approve_deletion_request(
    idea_id: UUID,
    body: IdeaCurationDecision,
    request: Request,
    current_user: dict = Depends(require_permission("ideas.curation.manage")),
):
    return await idea_service.approve_deletion_request(
        idea_id=idea_id,
        reviewer_id=current_user["id"],
        reason=body.reason,
        request=request,
    )


@admin_router.post("/{idea_id}/deletion-request/deny", response_model=IdeaDetailResponse)
async def admin_deny_deletion_request(
    idea_id: UUID,
    body: IdeaCurationDecision,
    request: Request,
    current_user: dict = Depends(require_permission("ideas.curation.manage")),
):
    return await idea_service.deny_deletion_request(
        idea_id=idea_id,
        reviewer_id=current_user["id"],
        reason=body.reason or "",
        request=request,
    )


@admin_router.post("/comments/{comment_id}/hide", response_model=IdeaCommentResponse)
async def admin_hide_comment(
    comment_id: UUID,
    body: IdeaCommentModerationDecision,
    request: Request,
    current_user: dict = Depends(require_permission("ideas.curation.manage")),
):
    return await idea_service.moderate_comment(
        comment_id=comment_id,
        moderator_id=current_user["id"],
        hide=True,
        reason=body.reason,
        request=request,
    )


@admin_router.get("/{idea_id}/comments", response_model=list[IdeaCommentResponse])
async def admin_list_comments(
    idea_id: UUID,
    current_user: dict = Depends(require_permission("ideas.curation.manage")),
):
    return await idea_service.list_admin_comments(idea_id=idea_id, user_id=current_user["id"])


@admin_router.post("/comments/{comment_id}/restore", response_model=IdeaCommentResponse)
async def admin_restore_comment(
    comment_id: UUID,
    body: IdeaCommentModerationDecision,
    request: Request,
    current_user: dict = Depends(require_permission("ideas.curation.manage")),
):
    return await idea_service.moderate_comment(
        comment_id=comment_id,
        moderator_id=current_user["id"],
        hide=False,
        reason=body.reason,
        request=request,
    )


@admin_router.put("/{idea_id}/roadmap", response_model=IdeaDetailResponse)
async def admin_update_idea_roadmap(
    idea_id: UUID,
    body: IdeaRoadmapUpdate,
    request: Request,
    current_user: dict = Depends(require_permission("ideas.roadmap.manage")),
):
    return await idea_service.update_idea_roadmap(
        idea_id=idea_id,
        body=body,
        reviewer_id=current_user["id"],
        request=request,
    )


@admin_router.get("/versions", response_model=list[IdeaVersionResponse])
async def admin_list_versions(_: dict = Depends(require_permission("admin.idea_versions.manage"))):
    return await idea_service.list_versions(include_inactive=True)


@admin_router.post("/versions", response_model=IdeaVersionResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_version(
    body: IdeaVersionCreate,
    request: Request,
    current_user: dict = Depends(require_permission("admin.idea_versions.manage")),
):
    return await idea_service.create_version(body=body, user_id=current_user["id"], request=request)


@admin_router.put("/versions/{version_id}", response_model=IdeaVersionResponse)
async def admin_update_version(
    version_id: UUID,
    body: IdeaVersionUpdate,
    request: Request,
    current_user: dict = Depends(require_permission("admin.idea_versions.manage")),
):
    return await idea_service.update_version(version_id=version_id, body=body, user_id=current_user["id"], request=request)


@admin_router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_version(
    version_id: UUID,
    request: Request,
    current_user: dict = Depends(require_permission("admin.idea_versions.manage")),
):
    await idea_service.delete_or_deactivate_version(version_id=version_id, user_id=current_user["id"], request=request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
