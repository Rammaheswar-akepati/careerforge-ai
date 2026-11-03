import { useCallback, useEffect, useRef, useState } from "react";

import {
  deleteResume,
  listResumes,
  uploadResume,
  type ResumeList,
} from "../api/resumes";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ResumeListSection } from "./ResumeListSection";
import { ResumeDeleteDialog } from "./ResumeDeleteDialog";
import { ResumePreviewDialog } from "./ResumePreviewDialog";
import { ResumeUploadForm } from "./ResumeUploadForm";

const PAGE_SIZE = 10;

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "We could not load your resumes. Please try again.";
}

export function ResumeDashboard() {
  const { accessToken, user, logout } = useAuth();
  const [resumeList, setResumeList] = useState<ResumeList | null>(null);
  const [page, setPage] = useState(1);
  const [refreshVersion, setRefreshVersion] = useState(0);
  const [preview, setPreview] = useState<{
    resumeId: number;
    opener: HTMLButtonElement;
  } | null>(null);
  const [deleteSelection, setDeleteSelection] = useState<{
    resumeId: number;
    opener: HTMLButtonElement;
  } | null>(null);
  const [deleteSuccessMessage, setDeleteSuccessMessage] = useState("");
  const focusFrameRef = useRef<number | null>(null);
  const libraryHeadingRef = useRef<HTMLHeadingElement>(null);
  const isDeletingRef = useRef(false);
  const deletionSucceededRef = useRef(false);
  const [isLoading, setIsLoading] = useState(true);
  const [listError, setListError] = useState("");

  useEffect(() => {
    let isCurrentRequest = true;

    if (!accessToken) {
      setListError("Your session has ended. Please sign in again.");
      setIsLoading(false);
      return () => {
        isCurrentRequest = false;
      };
    }

    setIsLoading(true);
    setListError("");

    listResumes(accessToken, page, PAGE_SIZE, logout)
      .then((result) => {
        if (isCurrentRequest) {
          setResumeList(result);
        }
      })
      .catch((error: unknown) => {
        if (isCurrentRequest) {
          setListError(getErrorMessage(error));
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
  }, [accessToken, logout, page, refreshVersion]);

  const handleUpload = useCallback(
    async (file: File) => {
      if (!accessToken) {
        throw new ApiError("Your session has ended. Please sign in again.", 401);
      }

      await uploadResume(file, accessToken, logout);
      setPage(1);
      setRefreshVersion((version) => version + 1);
    },
    [accessToken, logout],
  );

  const retryLoading = useCallback(() => {
    setRefreshVersion((version) => version + 1);
  }, []);

  async function confirmResumeDeletion() {
    if (!deleteSelection || isDeletingRef.current) {
      return;
    }
    if (!accessToken) {
      throw new ApiError("Your session has ended. Please sign in again.", 401);
    }

    isDeletingRef.current = true;
    setDeleteSuccessMessage("");
    deletionSucceededRef.current = false;

    try {
      await deleteResume(deleteSelection.resumeId, accessToken, logout);
      deletionSucceededRef.current = true;
      setDeleteSuccessMessage(`Resume #${deleteSelection.resumeId} was deleted.`);

      if (page > 1 && resumeList?.items.length === 1) {
        setPage((currentPage) => currentPage - 1);
      } else {
        setRefreshVersion((version) => version + 1);
      }
    } finally {
      isDeletingRef.current = false;
    }
  }

  useEffect(
    () => () => {
      if (focusFrameRef.current !== null) {
        cancelAnimationFrame(focusFrameRef.current);
      }
    },
    [],
  );

  function handleViewResume(resumeId: number, opener: HTMLButtonElement) {
    if (focusFrameRef.current !== null) {
      cancelAnimationFrame(focusFrameRef.current);
      focusFrameRef.current = null;
    }
    setDeleteSelection(null);
    setPreview({ resumeId, opener });
  }

  function handleDeleteResume(resumeId: number, opener: HTMLButtonElement) {
    if (isDeletingRef.current || deleteSelection) {
      return;
    }
    if (focusFrameRef.current !== null) {
      cancelAnimationFrame(focusFrameRef.current);
      focusFrameRef.current = null;
    }
    setPreview(null);
    setDeleteSuccessMessage("");
    setDeleteSelection({ resumeId, opener });
  }

  function handleDeleteDialogClose(opener: HTMLButtonElement) {
    setDeleteSelection(null);
    if (focusFrameRef.current !== null) {
      cancelAnimationFrame(focusFrameRef.current);
    }

    const deletionSucceeded = deletionSucceededRef.current;
    deletionSucceededRef.current = false;
    focusFrameRef.current = requestAnimationFrame(() => {
      focusFrameRef.current = null;
      if (deletionSucceeded) {
        libraryHeadingRef.current?.focus();
      } else if (
        opener.isConnected &&
        !opener.matches(":disabled") &&
        opener.getClientRects().length > 0
      ) {
        opener.focus();
      } else {
        libraryHeadingRef.current?.focus();
      }
    });
  }

  function handlePreviewClose(opener: HTMLButtonElement) {
    setPreview(null);
    focusFrameRef.current = requestAnimationFrame(() => {
      focusFrameRef.current = null;
      if (
        opener.isConnected &&
        !opener.matches(":disabled") &&
        opener.getClientRects().length > 0
      ) {
        opener.focus();
      }
    });
  }

  return (
    <main className="welcome-page dashboard-page">
      <header className="welcome-header">
        <div className="brand" aria-label="CareerForge AI">
          <span className="brand-mark" aria-hidden="true">
            CF
          </span>
          <span>CareerForge AI</span>
        </div>
        <button className="text-button" type="button" onClick={logout}>
          Sign out
        </button>
      </header>

      <section className="dashboard-content" aria-labelledby="dashboard-title">
        <div className="dashboard-heading">
          <div>
            <p className="eyebrow">RESUME WORKSPACE</p>
            <h1 id="dashboard-title">Welcome, {user?.full_name}</h1>
            <p className="welcome-description">
              Keep your career story organized and ready for what comes next.
            </p>
          </div>
          <div className="resume-count-card" aria-live="polite">
            <span className="resume-count-label">UPLOADED RESUMES</span>
            <strong>{resumeList?.total ?? (isLoading ? "—" : 0)}</strong>
          </div>
        </div>

        <ResumeUploadForm onUpload={handleUpload} />
        <ResumeListSection
          resumeList={resumeList}
          page={page}
          isLoading={isLoading}
          errorMessage={listError}
          deleteSuccessMessage={deleteSuccessMessage}
          previewResumeId={preview?.resumeId ?? null}
          activeDeleteResumeId={deleteSelection?.resumeId ?? null}
          onViewResume={handleViewResume}
          onDeleteResume={handleDeleteResume}
          onPageChange={setPage}
          onRetry={retryLoading}
          libraryHeadingRef={libraryHeadingRef}
        />
      </section>
      {deleteSelection && accessToken && (
        <ResumeDeleteDialog
          key={deleteSelection.resumeId}
          resumeId={deleteSelection.resumeId}
          opener={deleteSelection.opener}
          onConfirm={confirmResumeDeletion}
          onClose={handleDeleteDialogClose}
        />
      )}
      {preview && accessToken && (
        <ResumePreviewDialog
          key={preview.resumeId}
          resumeId={preview.resumeId}
          opener={preview.opener}
          token={accessToken}
          onUnauthorized={logout}
          onClose={handlePreviewClose}
        />
      )}
    </main>
  );
}
