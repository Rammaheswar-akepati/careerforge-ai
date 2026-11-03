import type { RefObject } from "react";

import type { ResumeList } from "../api/resumes";

interface ResumeListSectionProps {
  resumeList: ResumeList | null;
  page: number;
  isLoading: boolean;
  errorMessage: string;
  deleteSuccessMessage: string;
  previewResumeId: number | null;
  activeDeleteResumeId: number | null;
  onViewResume: (resumeId: number, opener: HTMLButtonElement) => void;
  onDeleteResume: (resumeId: number, opener: HTMLButtonElement) => void;
  onPageChange: (page: number) => void;
  onRetry: () => void;
  libraryHeadingRef: RefObject<HTMLHeadingElement | null>;
}

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
});
const numberFormatter = new Intl.NumberFormat();

export function ResumeListSection({
  resumeList,
  page,
  isLoading,
  errorMessage,
  deleteSuccessMessage,
  previewResumeId,
  activeDeleteResumeId,
  onViewResume,
  onDeleteResume,
  onPageChange,
  onRetry,
  libraryHeadingRef,
}: ResumeListSectionProps) {
  return (
    <section className="dashboard-card resume-library" aria-labelledby="library-title">
      <div className="section-heading library-heading">
        <div>
          <p className="eyebrow">YOUR FILES</p>
          <h2 id="library-title" ref={libraryHeadingRef} tabIndex={-1}>
            Resume library
          </h2>
        </div>
        {resumeList && (
          <span className="library-total" aria-label={`${resumeList.total} resumes`}>
            {numberFormatter.format(resumeList.total)}{" "}
            {resumeList.total === 1 ? "resume" : "resumes"}
          </span>
        )}
      </div>

      {deleteSuccessMessage && (
        <p className="form-message success-message resume-delete-success" role="status">
          {deleteSuccessMessage}
        </p>
      )}

      {isLoading ? (
        <p className="library-state" role="status">
          Loading your resumes…
        </p>
      ) : errorMessage ? (
        <div className="library-state library-error">
          <p role="alert">{errorMessage}</p>
          <button className="text-button" type="button" onClick={onRetry}>
            Try again
          </button>
        </div>
      ) : !resumeList || resumeList.items.length === 0 ? (
        <div className="library-state empty-library">
          <span className="empty-library-icon" aria-hidden="true">
            ↗
          </span>
          <h3>Your resume library is empty</h3>
          <p>Upload a PDF above to add your first resume.</p>
        </div>
      ) : (
        <>
          <ul className="resume-list">
            {resumeList.items.map((resume) => (
              <li className="resume-list-item" key={resume.id}>
                <span className="resume-item-icon" aria-hidden="true">
                  PDF
                </span>
                <div className="resume-item-main">
                  <h3>Resume #{resume.id}</h3>
                  <p>Uploaded {dateFormatter.format(new Date(resume.created_at))}</p>
                </div>
                <dl className="resume-item-stats">
                  <div>
                    <dt>Pages</dt>
                    <dd>{numberFormatter.format(resume.page_count)}</dd>
                  </div>
                  <div>
                    <dt>Characters</dt>
                    <dd>{numberFormatter.format(resume.character_count)}</dd>
                  </div>
                </dl>
                <div className="resume-row-actions">
                  <button
                    className="text-button resume-view-button"
                    type="button"
                    onClick={(event) =>
                      onViewResume(resume.id, event.currentTarget)
                    }
                    disabled={
                      previewResumeId !== null || activeDeleteResumeId !== null
                    }
                    aria-label={`View resume ${resume.id}`}
                  >
                    View Resume
                  </button>
                  <button
                    className="text-button resume-delete-row-button"
                    type="button"
                    onClick={(event) =>
                      onDeleteResume(resume.id, event.currentTarget)
                    }
                    disabled={
                      previewResumeId !== null || activeDeleteResumeId !== null
                    }
                    aria-label={`Delete resume ${resume.id}`}
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>

          {resumeList.total_pages > 1 && (
            <nav className="pagination" aria-label="Resume list pages">
              <span>
                Page {resumeList.page} of {resumeList.total_pages}
              </span>
              <div>
                <button
                  className="text-button"
                  type="button"
                  onClick={() => onPageChange(page - 1)}
                  disabled={
                    isLoading || activeDeleteResumeId !== null || page <= 1
                  }
                  aria-label="Previous page"
                >
                  Previous
                </button>
                <button
                  className="text-button"
                  type="button"
                  onClick={() => onPageChange(page + 1)}
                  disabled={
                    isLoading ||
                    activeDeleteResumeId !== null ||
                    page >= resumeList.total_pages
                  }
                  aria-label="Next page"
                >
                  Next
                </button>
              </div>
            </nav>
          )}
        </>
      )}
    </section>
  );
}
