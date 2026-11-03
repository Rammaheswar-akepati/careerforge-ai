import { useRef, useState, type FormEvent } from "react";

import { ApiError } from "../api/client";

const MAX_FILE_SIZE = 5 * 1024 * 1024;

interface ResumeUploadFormProps {
  onUpload: (file: File) => Promise<void>;
}

function getUploadErrorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "We could not upload this PDF. Please try again.";
}

export function ResumeUploadForm({ onUpload }: ResumeUploadFormProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const submittingRef = useRef(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  function clearFileInput() {
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function handleFileChange(file: File | undefined) {
    setSelectedFile(null);
    setErrorMessage("");
    setSuccessMessage("");

    if (!file) {
      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setErrorMessage("Choose a PDF file to upload.");
      clearFileInput();
      return;
    }
    if (file.type && file.type !== "application/pdf") {
      setErrorMessage("Choose a PDF file to upload.");
      clearFileInput();
      return;
    }
    if (file.size === 0) {
      setErrorMessage("The selected PDF is empty.");
      clearFileInput();
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      setErrorMessage("The PDF must be 5 MiB or smaller.");
      clearFileInput();
      return;
    }

    setSelectedFile(file);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile || submittingRef.current) {
      return;
    }

    submittingRef.current = true;
    setIsSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      await onUpload(selectedFile);
      setSuccessMessage("Your resume was uploaded successfully.");
      setSelectedFile(null);
      clearFileInput();
    } catch (error) {
      setErrorMessage(getUploadErrorMessage(error));
    } finally {
      submittingRef.current = false;
      setIsSubmitting(false);
    }
  }

  return (
    <section className="dashboard-card upload-card" aria-labelledby="upload-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">ADD TO YOUR LIBRARY</p>
          <h2 id="upload-title">Upload a resume</h2>
        </div>
        <span className="upload-file-badge" aria-hidden="true">
          PDF
        </span>
      </div>
      <p className="section-description">
        Choose a PDF up to 5 MiB. We’ll extract and organize its text for your
        workspace.
      </p>

      {errorMessage && (
        <p className="form-message error-message" role="alert">
          {errorMessage}
        </p>
      )}
      {successMessage && (
        <p className="form-message success-message" role="status">
          {successMessage}
        </p>
      )}

      <form className="resume-upload-form" onSubmit={handleSubmit}>
        <label className="resume-file-field">
          <span className="visually-hidden">Choose a PDF resume</span>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={(event) => handleFileChange(event.currentTarget.files?.[0])}
            disabled={isSubmitting}
          />
        </label>
        {selectedFile && (
          <p className="selected-file" title={selectedFile.name}>
            Selected: {selectedFile.name}
          </p>
        )}
        <button
          className="primary-button upload-button"
          type="submit"
          disabled={!selectedFile || isSubmitting}
        >
          {isSubmitting ? "Uploading..." : "Upload PDF"}
          {!isSubmitting && <span aria-hidden="true">↑</span>}
        </button>
      </form>
    </section>
  );
}
