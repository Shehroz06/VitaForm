import type {
  AutofitResult,
  ExportedResumeFile,
  GenerateResumeResponse,
  Resume,
  ResumeContent,
  ResumeCreatePayload,
  ResumeGeneratePayload,
  ResumeStyle,
  ResumeTemplate,
  ResumeUpdatePayload,
  ResumeVersion,
  ResumeVersionSummary,
  RewriteTextPayload,
  RewriteTextResult,
} from "@/features/resumes/types";
import { apiClient } from "@/services/api-client";

export const resumeTemplateService = {
  list: () => apiClient.get<ResumeTemplate[]>("/resume-templates"),
  // Real backend render of the given template filled with the caller's own
  // profile -- used by the pre-resume-creation template browser, which has
  // no resume yet to scope a preview to (see resumeService.previewWith for
  // the equivalent once a resume exists).
  previewSample: (templateId: string, style: ResumeStyle) =>
    apiClient.postBlob(`/resume-templates/${templateId}/preview`, { style }),
};

export const resumeService = {
  list: () => apiClient.get<Resume[]>("/resumes"),
  create: (payload: ResumeCreatePayload) => apiClient.post<Resume>("/resumes", payload),
  generate: (payload: ResumeGeneratePayload) =>
    apiClient.post<GenerateResumeResponse>("/resumes/generate", payload),
  get: (id: string) => apiClient.get<Resume>(`/resumes/${id}`),
  update: (id: string, payload: Partial<ResumeUpdatePayload>) =>
    apiClient.patch<Resume>(`/resumes/${id}`, payload),
  remove: (id: string) => apiClient.delete<void>(`/resumes/${id}`),
  getContent: (id: string) => apiClient.get<ResumeVersion>(`/resumes/${id}/content`),
  updateContent: (id: string, content: ResumeContent) =>
    apiClient.put<ResumeVersion>(`/resumes/${id}/content`, content),
  // Updates the current version's content in place -- no new version_number,
  // unlike updateContent. Used for autosave.
  autosaveContent: (id: string, content: ResumeContent) =>
    apiClient.patch<ResumeVersion>(`/resumes/${id}/content`, content),
  listVersions: (id: string) => apiClient.get<ResumeVersionSummary[]>(`/resumes/${id}/versions`),
  getVersion: (id: string, versionId: string) =>
    apiClient.get<ResumeVersion>(`/resumes/${id}/versions/${versionId}`),
  export: (id: string) => apiClient.post<ExportedResumeFile>(`/resumes/${id}/export`),
  // Tightens spacing/density to fit one page losslessly (never deletes
  // content) -- the manual-builder counterpart to the fit step AI
  // generation already runs on its own.
  autofit: (id: string) => apiClient.post<AutofitResult>(`/resumes/${id}/autofit`),
  // The opt-in "extreme fit" escalation: same lossless spacing/density
  // search, then (only if still needed) condenses descriptions or drops
  // the lowest-priority items -- never run automatically, only when the
  // user explicitly asks for it.
  autofitAggressive: (id: string) =>
    apiClient.post<AutofitResult>(`/resumes/${id}/autofit?aggressive=true`),
  // Rasterized PNG of one page of the real render (see backend's
  // GET /resumes/{id}/preview) -- the builder's live preview shows this
  // image directly instead of a separate React re-implementation of each
  // template, so there's exactly one source of truth for what a resume
  // looks like. `page` (1-indexed) fetches page 2, 3, ... for resumes that
  // overflow one page; every response's pageCount says how many exist.
  getPreview: (id: string, page = 1) =>
    apiClient.getBlob(`/resumes/${id}/preview?page=${page}`),
  // Raw, uncompiled .tex source -- only valid for the ats_safe (LaTeX)
  // template; the caller only shows this action when that's the current
  // template. Lets a user verify or recompile independently (e.g. Overleaf).
  exportTex: (id: string, filename: string) =>
    apiClient.downloadFile(`/resumes/${id}/export-tex`, filename),
  // Real backend render of arbitrary (not-yet-saved) content against a
  // candidate template -- nothing is persisted. Powers the template
  // picker's per-template comparison cards with the actual render instead
  // of a client-side approximation.
  previewWith: (id: string, content: ResumeContent, templateId: string) =>
    apiClient.postBlob(`/resumes/${id}/preview-with`, { content, template_id: templateId }),
  // Best-effort, fact-checked AI rephrase for one description or the
  // summary -- stateless (doesn't touch the resume's saved content); the
  // caller decides where the returned text goes and saves it normally.
  rewriteText: (id: string, payload: RewriteTextPayload) =>
    apiClient.post<RewriteTextResult>(`/resumes/${id}/rewrite-text`, payload),
};
