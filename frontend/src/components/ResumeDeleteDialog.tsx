import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type MouseEvent,
  type SyntheticEvent,
} from "react";

import { ApiError } from "../api/client";

interface ResumeDeleteDialogProps {
  resumeId: number;
  opener: HTMLButtonElement;
  onConfirm: () => Promise<void>;
  onClose: (opener: HTMLButtonElement) => void;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 404) {
    return "This resume is no longer available. Refresh your resume library and try again.";
  }
  if (error instanceof ApiError) {
    return error.message;
  }
  return "We could not delete this resume. Please try again.";
}

export function ResumeDeleteDialog({
  resumeId,
  opener,
  onConfirm,
  onClose,
}: ResumeDeleteDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const onCloseRef = useRef(onClose);
  const isSubmittingRef = useRef(false);
  const isClosingRef = useRef(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  onCloseRef.current = onClose;

  function closeDialog(force = false) {
    if (isClosingRef.current || (isSubmittingRef.current && !force)) {
      return;
    }

    isClosingRef.current = true;
    dialogRef.current?.close();
    if (
      opener.isConnected &&
      !opener.matches(":disabled") &&
      opener.getClientRects().length > 0
    ) {
      opener.focus();
    }
    onCloseRef.current(opener);
  }

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && dialog?.open) {
        event.preventDefault();
        event.stopPropagation();
        closeDialog();
      }
    }

    dialog.addEventListener("keydown", handleEscape);
    if (!dialog.open) {
      dialog.showModal();
    }

    return () => {
      dialog.removeEventListener("keydown", handleEscape);
      if (dialog?.open) {
        dialog.close();
      }
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmittingRef.current) {
      return;
    }

    isSubmittingRef.current = true;
    setIsSubmitting(true);
    setErrorMessage("");

    try {
      await onConfirm();
      closeDialog(true);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      isSubmittingRef.current = false;
      setIsSubmitting(false);
    }
  }

  function handleCancel(event: SyntheticEvent<HTMLDialogElement>) {
    event.preventDefault();
    closeDialog();
  }

  function handleDialogClick(event: MouseEvent<HTMLDialogElement>) {
    if (event.target === event.currentTarget) {
      closeDialog();
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="resume-delete-dialog"
      aria-labelledby="resume-delete-title"
      aria-describedby="resume-delete-description"
      aria-busy={isSubmitting}
      onCancel={handleCancel}
      onClick={handleDialogClick}
    >
      <h2 id="resume-delete-title">Delete resume #{resumeId}?</h2>
      <p id="resume-delete-description">
        This permanently deletes the resume and its extracted text. This action cannot be undone.
      </p>
      {errorMessage && (
        <p className="form-message error-message resume-delete-error" role="alert">
          {errorMessage}
        </p>
      )}
      {isSubmitting && (
        <p className="visually-hidden" role="status">
          Deleting resume #{resumeId}…
        </p>
      )}
      <form className="resume-delete-actions" onSubmit={handleSubmit}>
        <button
          className="text-button"
          type="button"
          onClick={() => closeDialog()}
          disabled={isSubmitting}
          autoFocus
        >
          Cancel
        </button>
        <button
          className="primary-button resume-delete-button"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Deleting…" : "Delete"}
        </button>
      </form>
    </dialog>
  );
}
