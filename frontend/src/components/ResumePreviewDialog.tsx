import { useEffect, useRef, useState, type MouseEvent } from "react";

import { ApiError } from "../api/client";
import { getResume, type ResumeDetail } from "../api/resumes";

interface ResumePreviewDialogProps {
  resumeId: number;
  opener: HTMLButtonElement;
  token: string;
  onUnauthorized: () => void;
  onClose: (opener: HTMLButtonElement) => void;
}

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "We could not load this resume. Please try again.";
}

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
});
const numberFormatter = new Intl.NumberFormat();

export function ResumePreviewDialog({
  resumeId,
  opener,
  token,
  onUnauthorized,
  onClose,
}: ResumePreviewDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const requestRef = useRef<Promise<ResumeDetail> | null>(null);
  const onCloseRef = useRef(onClose);
  const isClosingRef = useRef(false);
  const [resume, setResume] = useState<ResumeDetail | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [retryVersion, setRetryVersion] = useState(0);

  onCloseRef.current = onClose;

  function closeDialog() {
    if (isClosingRef.current) {
      return;
    }

    isClosingRef.current = true;
    dialogRef.current?.close();
    onCloseRef.current(opener);
  }

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }

    function handleCancel(event: Event) {
      event.preventDefault();
      closeDialog();
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && dialogRef.current?.open) {
        event.preventDefault();
        closeDialog();
      }
    }

    dialog.addEventListener("cancel", handleCancel);
    dialog.addEventListener("keydown", handleEscape);
    if (!dialog.open) {
      dialog.showModal();
    }

    return () => {
      dialog.removeEventListener("cancel", handleCancel);
      dialog.removeEventListener("keydown", handleEscape);
      if (dialog?.open) {
        dialog.close();
      }
    };
  }, []);

  useEffect(() => {
    let isCurrentRequest = true;
    setResume(null);
    setErrorMessage("");
    setIsLoading(true);

    const request = requestRef.current ?? getResume(resumeId, token, onUnauthorized);
    requestRef.current = request;

    request
      .then((result) => {
        if (isCurrentRequest) {
          setResume(result);
        }
      })
      .catch((error: unknown) => {
        if (isCurrentRequest) {
          setErrorMessage(getErrorMessage(error));
        }
      })
      .finally(() => {
        if (isCurrentRequest) {
          setIsLoading(false);
        }
      });

    return () => {
      isCurrentRequest = false;
    };
  }, [onUnauthorized, resumeId, retryVersion, token]);

  function retry() {
    requestRef.current = null;
    setRetryVersion((version) => version + 1);
  }

  function handleDialogClick(event: MouseEvent<HTMLDialogElement>) {
    if (event.target === event.currentTarget) {
      closeDialog();
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="resume-preview-dialog"
      aria-labelledby="resume-preview-title"
      onClick={handleDialogClick}
    >
      <div className="preview-dialog-header">
        <div>
          <p className="eyebrow">RESUME PREVIEW</p>
          <h2 id="resume-preview-title">Resume #{resumeId}</h2>
        </div>
        <button
          className="preview-close-button"
          type="button"
          onClick={closeDialog}
          aria-label="Close resume preview"
          autoFocus
        >
          <span aria-hidden="true">×</span>
        </button>
      </div>

      {isLoading ? (
        <p className="preview-state" role="status">
          Loading resume details…
        </p>
      ) : errorMessage ? (
        <div className="preview-state preview-error">
          <p role="alert">{errorMessage}</p>
          <button className="text-button" type="button" onClick={retry}>
            Try again
          </button>
        </div>
      ) : resume && resume.id === resumeId ? (
        <>
          <dl className="preview-metadata">
            <div>
              <dt>Uploaded</dt>
              <dd>{dateFormatter.format(new Date(resume.created_at))}</dd>
            </div>
            <div>
              <dt>Pages</dt>
              <dd>{numberFormatter.format(resume.page_count)}</dd>
            </div>
            <div>
              <dt>Characters</dt>
              <dd>{numberFormatter.format(resume.character_count)}</dd>
            </div>
          </dl>
          <section className="preview-text-section" aria-label="Extracted resume text">
            <h3>Extracted text</h3>
            <pre className="preview-text">{resume.extracted_text}</pre>
          </section>
        </>
      ) : null}
    </dialog>
  );
}
