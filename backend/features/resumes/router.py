import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies.auth import CurrentUser
from app.dependencies.rate_limits import (
    resume_autofit_rate_limit,
    resume_export_rate_limit,
    resume_generate_rate_limit,
    resume_preview_rate_limit,
    rewrite_text_rate_limit,
    template_preview_rate_limit,
)
from app.exceptions.base import ResourceNotFoundException
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.ai.dependencies import get_generation_service
from features.ai.schemas import GenerateResumeResponse, ResumeGenerateRequest
from features.ai.service import GenerationService
from features.files.dependencies import get_file_repository
from features.files.repository import FileRepository
from features.files.schemas import FileResponse as FileAttachmentResponse
from features.profiles.dependencies import CurrentProfile
from features.resumes.dependencies import (
    get_resume_export_service,
    get_resume_service,
    get_resume_template_repository,
)
from features.resumes.export_service import ResumeExportService
from features.resumes.models import Resume
from features.resumes.repository import ResumeTemplateRepository
from features.resumes.schemas import (
    PreviewWithRequest,
    ResumeAutofitResponse,
    ResumeContent,
    ResumeCreateRequest,
    ResumeResponse,
    ResumeTemplateResponse,
    ResumeUpdateRequest,
    ResumeVersionResponse,
    ResumeVersionSummaryResponse,
    RewriteTextRequest,
    RewriteTextResponse,
    TemplateSampleRequest,
)
from features.resumes.service import ResumeService

router = APIRouter(tags=["resumes"])

ResumeServiceDep = Annotated[ResumeService, Depends(get_resume_service)]
ResumeExportServiceDep = Annotated[ResumeExportService, Depends(get_resume_export_service)]
ResumeTemplateRepositoryDep = Annotated[
    ResumeTemplateRepository, Depends(get_resume_template_repository)
]
GenerationServiceDep = Annotated[GenerationService, Depends(get_generation_service)]


def _full_name(first_name: str | None, last_name: str | None) -> str:
    return " ".join(part for part in (first_name, last_name) if part).strip()


async def _to_resume_response(resume: Resume, service: ResumeService) -> ResumeResponse:
    latest = await service.get_latest_version(resume)
    return ResumeResponse(
        id=resume.id,
        title=resume.title,
        template_id=resume.template_id,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        latest_version_number=latest.version_number,
    )


@router.get("/resume-templates", response_model=SuccessResponse[list[ResumeTemplateResponse]])
async def list_resume_templates(
    repository: ResumeTemplateRepositoryDep,
) -> SuccessResponse[list[ResumeTemplateResponse]]:
    templates = await repository.list_active()
    return SuccessResponse(
        message="Resume templates retrieved successfully.",
        data=[ResumeTemplateResponse.model_validate(t) for t in templates],
    )


@router.post(
    "/resume-templates/{template_id}/preview",
    dependencies=[Depends(template_preview_rate_limit)],
)
async def preview_resume_template(
    template_id: uuid.UUID,
    data: TemplateSampleRequest,
    profile: CurrentProfile,
    user: CurrentUser,
    export_service: ResumeExportServiceDep,
) -> Response:
    """Real render of a candidate template filled with the caller's own
    profile -- the template browser's preview, before any resume exists to
    scope a render to (see PreviewWithRequest for the equivalent once one
    does). Authenticated: this triggers a real pdflatex/WeasyPrint compile,
    which is too expensive to expose without auth."""
    png_bytes = await export_service.render_template_sample_image(
        profile, template_id, data.style, user.email, _full_name(user.first_name, user.last_name)
    )
    return Response(
        content=png_bytes, media_type="image/png", headers={"Cache-Control": "no-store"}
    )


@router.get("/resumes", response_model=SuccessResponse[list[ResumeResponse]])
async def list_resumes(
    profile: CurrentProfile,
    service: ResumeServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[ResumeResponse]]:
    items, total = await service.list_resumes(
        profile.id, page=pagination.page, limit=pagination.limit
    )
    return SuccessResponse(
        message="Resumes retrieved successfully.",
        data=[await _to_resume_response(item, service) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "/resumes", response_model=SuccessResponse[ResumeResponse], status_code=status.HTTP_201_CREATED
)
async def create_resume(
    data: ResumeCreateRequest,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeResponse]:
    resume = await service.create_resume(profile.id, data.title, data.template_id)
    return SuccessResponse(
        message="Resume created successfully.", data=await _to_resume_response(resume, service)
    )


@router.post(
    "/resumes/generate",
    response_model=SuccessResponse[GenerateResumeResponse],
    dependencies=[Depends(resume_generate_rate_limit)],
)
async def generate_resume(
    data: ResumeGenerateRequest,
    profile: CurrentProfile,
    user: CurrentUser,
    generation_service: GenerationServiceDep,
    file_repository: Annotated[FileRepository, Depends(get_file_repository)],
) -> SuccessResponse[GenerateResumeResponse]:
    version = await generation_service.generate_resume(
        profile, user.email, _full_name(user.first_name, user.last_name), data
    )

    assert version.rendered_file_id is not None
    rendered_file = await file_repository.get_by_id(version.rendered_file_id)
    if rendered_file is None:
        raise ResourceNotFoundException("Rendered resume file not found.")

    return SuccessResponse(
        message="Resume generated successfully.",
        data=GenerateResumeResponse(
            resume_id=version.resume_id,
            file=FileAttachmentResponse.model_validate(rendered_file),
        ),
    )


@router.get("/resumes/{resume_id}", response_model=SuccessResponse[ResumeResponse])
async def get_resume(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeResponse]:
    resume = await service.get_owned_resume(resume_id, profile.id)
    return SuccessResponse(
        message="Resume retrieved successfully.", data=await _to_resume_response(resume, service)
    )


@router.patch("/resumes/{resume_id}", response_model=SuccessResponse[ResumeResponse])
async def update_resume(
    resume_id: uuid.UUID,
    data: ResumeUpdateRequest,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeResponse]:
    resume = await service.update_resume(
        resume_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Resume updated successfully.", data=await _to_resume_response(resume, service)
    )


@router.delete("/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> None:
    await service.delete_resume(resume_id, profile.id)


@router.get("/resumes/{resume_id}/content", response_model=SuccessResponse[ResumeVersionResponse])
async def get_resume_content(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeVersionResponse]:
    resume = await service.get_owned_resume(resume_id, profile.id)
    version = await service.get_latest_version(resume)
    return SuccessResponse(
        message="Resume content retrieved successfully.",
        data=ResumeVersionResponse.model_validate(version),
    )


@router.put("/resumes/{resume_id}/content", response_model=SuccessResponse[ResumeVersionResponse])
async def update_resume_content(
    resume_id: uuid.UUID,
    data: ResumeContent,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeVersionResponse]:
    resume = await service.get_owned_resume(resume_id, profile.id)
    version = await service.create_new_version(resume, data)
    return SuccessResponse(
        message="New resume version created successfully.",
        data=ResumeVersionResponse.model_validate(version),
    )


@router.patch("/resumes/{resume_id}/content", response_model=SuccessResponse[ResumeVersionResponse])
async def autosave_resume_content(
    resume_id: uuid.UUID,
    data: ResumeContent,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeVersionResponse]:
    """Updates the current version's content in place -- unlike PUT, this
    never creates a new version. Used for autosave, so the working draft
    stays persisted (and therefore exportable) without generating a new
    history entry on every edit."""
    resume = await service.get_owned_resume(resume_id, profile.id)
    version = await service.autosave_content(resume, data)
    return SuccessResponse(
        message="Resume content autosaved successfully.",
        data=ResumeVersionResponse.model_validate(version),
    )


@router.post(
    "/resumes/{resume_id}/rewrite-text",
    response_model=SuccessResponse[RewriteTextResponse],
    dependencies=[Depends(rewrite_text_rate_limit)],
)
async def rewrite_resume_text(
    resume_id: uuid.UUID,
    data: RewriteTextRequest,
    profile: CurrentProfile,
    service: ResumeServiceDep,
    generation_service: GenerationServiceDep,
) -> SuccessResponse[RewriteTextResponse]:
    """On-demand "Rephrase with AI" for one item description or the resume
    summary, from the manual builder. Stateless -- takes and returns plain
    text, doesn't read or write the resume's saved content; the caller
    (builder UI) decides where the result goes and saves it via the normal
    autosave/PUT content endpoints, same as any other manual edit."""
    await service.get_owned_resume(resume_id, profile.id)  # 404s if not owned
    rewritten = await generation_service.rewrite_text(
        data.text, job_description=data.job_description, target_role=data.target_role
    )
    return SuccessResponse(
        message="Rewrite completed." if rewritten else "Rewrite unavailable; kept original text.",
        data=RewriteTextResponse(rewritten_text=rewritten),
    )


@router.get(
    "/resumes/{resume_id}/versions",
    response_model=SuccessResponse[list[ResumeVersionSummaryResponse]],
)
async def list_resume_versions(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResumeServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[ResumeVersionSummaryResponse]]:
    resume = await service.get_owned_resume(resume_id, profile.id)
    items, total = await service.list_versions(
        resume, page=pagination.page, limit=pagination.limit
    )
    return SuccessResponse(
        message="Resume versions retrieved successfully.",
        data=[ResumeVersionSummaryResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.get(
    "/resumes/{resume_id}/versions/{version_id}",
    response_model=SuccessResponse[ResumeVersionResponse],
)
async def get_resume_version(
    resume_id: uuid.UUID,
    version_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeVersionResponse]:
    resume = await service.get_owned_resume(resume_id, profile.id)
    version = await service.get_version(resume, version_id)
    return SuccessResponse(
        message="Resume version retrieved successfully.",
        data=ResumeVersionResponse.model_validate(version),
    )


@router.post(
    "/resumes/{resume_id}/export",
    response_model=SuccessResponse[FileAttachmentResponse],
    dependencies=[Depends(resume_export_rate_limit)],
)
async def export_resume(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    user: CurrentUser,
    service: ResumeServiceDep,
    export_service: ResumeExportServiceDep,
    file_repository: Annotated[FileRepository, Depends(get_file_repository)],
) -> SuccessResponse[FileAttachmentResponse]:
    resume = await service.get_owned_resume(resume_id, profile.id)
    version = await service.get_latest_version(resume)
    updated_version = await export_service.export(
        resume, version, profile, user.email, _full_name(user.first_name, user.last_name)
    )

    assert updated_version.rendered_file_id is not None
    rendered_file = await file_repository.get_by_id(updated_version.rendered_file_id)
    if rendered_file is None:
        raise ResourceNotFoundException("Rendered resume file not found.")

    return SuccessResponse(
        message="Resume exported successfully.",
        data=FileAttachmentResponse.model_validate(rendered_file),
    )


@router.post(
    "/resumes/{resume_id}/autofit",
    response_model=SuccessResponse[ResumeAutofitResponse],
    dependencies=[Depends(resume_autofit_rate_limit)],
)
async def autofit_resume(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    user: CurrentUser,
    service: ResumeServiceDep,
    export_service: ResumeExportServiceDep,
    aggressive: Annotated[bool, Query()] = False,
) -> SuccessResponse[ResumeAutofitResponse]:
    """Tries progressively tighter spacing, then continuous density, to fit
    the resume on one page -- the same lossless search AI generation uses,
    reachable from the manual builder too so 'add a few more projects and
    it still looks right' isn't AI-generation-only. Never deletes content;
    if it's still too much even at the tightest setting, overflowing=True
    tells the caller a human needs to shorten or remove something.

    `aggressive=true` is a separate, explicitly opt-in escalation: after
    the same lossless search, it also condenses and (if still needed)
    deletes the lowest-priority items -- the "extreme fit" action, still
    only ever run when the user asks for it, never automatically."""
    resume = await service.get_owned_resume(resume_id, profile.id)
    version = await service.get_latest_version(resume)
    full_name = _full_name(user.first_name, user.last_name)
    updated_version, overflowing = (
        await export_service.autofit_aggressive(resume, version, profile, user.email, full_name)
        if aggressive
        else await export_service.autofit(resume, version, profile, user.email, full_name)
    )
    return SuccessResponse(
        message="Resume auto-fit successfully.",
        data=ResumeAutofitResponse(
            version=ResumeVersionResponse.model_validate(updated_version),
            overflowing=overflowing,
        ),
    )


@router.get(
    "/resumes/{resume_id}/preview",
    dependencies=[Depends(resume_preview_rate_limit)],
)
async def preview_resume(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    user: CurrentUser,
    service: ResumeServiceDep,
    export_service: ResumeExportServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
) -> Response:
    """Rasterized PNG of one page of the resume as it would actually export
    -- the live builder preview renders this image directly rather than
    re-implementing each template's layout in React, so there's exactly one
    source of truth for what a resume looks like. `page` lets a resume that
    overflows to 2+ pages be previewed page by page (X-Page-Count says how
    many exist) instead of silently cropping to page 1. No response_model:
    this returns raw image bytes, not the JSON envelope every other route
    uses."""
    resume = await service.get_owned_resume(resume_id, profile.id)
    version = await service.get_latest_version(resume)
    png_bytes, page_count = await export_service.render_preview_image(
        resume,
        version,
        profile,
        user.email,
        _full_name(user.first_name, user.last_name),
        page_number=page,
    )
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Cache-Control": "no-store", "X-Page-Count": str(page_count)},
    )


@router.post(
    "/resumes/{resume_id}/preview-with",
    dependencies=[Depends(resume_preview_rate_limit)],
)
async def preview_resume_with(
    resume_id: uuid.UUID,
    data: PreviewWithRequest,
    profile: CurrentProfile,
    user: CurrentUser,
    service: ResumeServiceDep,
    export_service: ResumeExportServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
) -> Response:
    """Renders arbitrary content against a candidate template, without
    saving anything -- the template picker's per-template comparison
    cards. Real backend render (same pipeline as export/preview), not a
    second, approximate client-side reimplementation of each template, so
    picking a template is judged on what it will actually look like."""
    resume = await service.get_owned_resume(resume_id, profile.id)
    png_bytes, page_count = await export_service.render_preview_image_with_content(
        resume,
        data.content,
        data.template_id,
        profile,
        user.email,
        _full_name(user.first_name, user.last_name),
        page_number=page,
    )
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Cache-Control": "no-store", "X-Page-Count": str(page_count)},
    )


@router.get("/resumes/{resume_id}/export-tex")
async def export_resume_tex(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    user: CurrentUser,
    service: ResumeServiceDep,
    export_service: ResumeExportServiceDep,
) -> Response:
    """Raw .tex source, uncompiled -- only meaningful for the LaTeX-engine
    template (ats_safe currently); raises for any HTML-engine template
    (renderer.py's render_tex_source), which the frontend avoids by only
    showing this action when the current template is ats_safe. Lets a user
    verify or independently recompile exactly what this app renders, e.g.
    in Overleaf, rather than trusting the PDF alone."""
    resume = await service.get_owned_resume(resume_id, profile.id)
    version = await service.get_latest_version(resume)
    tex_source = await export_service.export_tex_source(
        resume, version, profile, user.email, _full_name(user.first_name, user.last_name)
    )
    filename = f"{resume.title}.tex".replace("/", "-")
    return Response(
        content=tex_source,
        media_type="text/x-tex",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
