import { apiRequest } from "./client";

export interface ResumeSummary {
  id: number;
  page_count: number;
  character_count: number;
  created_at: string;
}

export interface ResumeList {
  items: ResumeSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ResumeDetail extends ResumeSummary {
  extracted_text: string;
}

export type ResumeUploadResult = ResumeDetail;

export function listResumes(
  token: string,
  page = 1,
  pageSize = 20,
  onUnauthorized?: () => void,
): Promise<ResumeList> {
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  return apiRequest<ResumeList>(`/api/v1/resumes?${query}`, {
    token,
    onUnauthorized,
  });
}

export function uploadResume(
  file: File,
  token: string,
  onUnauthorized?: () => void,
): Promise<ResumeUploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<ResumeUploadResult>("/api/v1/resumes", {
    method: "POST",
    token,
    formData,
    onUnauthorized,
  });
}

export function getResume(
  resumeId: number,
  token: string,
  onUnauthorized?: () => void,
): Promise<ResumeDetail> {
  return apiRequest<ResumeDetail>(`/api/v1/resumes/${resumeId}`, {
    token,
    onUnauthorized,
  });
}

export function deleteResume(
  resumeId: number,
  token: string,
  onUnauthorized?: () => void,
): Promise<void> {
  return apiRequest<void>(`/api/v1/resumes/${resumeId}`, {
    method: "DELETE",
    token,
    onUnauthorized,
  });
}
