import { useState } from "react";

export default function UploadBox({ setFile }) {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      validateAndSetFile(file);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      validateAndSetFile(file);
    }
  };

  const validateAndSetFile = (file) => {
    const allowedTypes = [
      'image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff',
      'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm',
      'audio/wav', 'audio/mp3', 'audio/flac', 'audio/aac', 'audio/ogg',
      'text/plain', 'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword'
    ];
    const maxSize = 100 * 1024 * 1024; // 100MB

    if (!allowedTypes.includes(file.type)) {
      alert('Please select a valid file type: Images (JPG, PNG, BMP, TIFF), Videos (MP4, AVI, MOV, MKV, WEBM), Audio (WAV, MP3, FLAC, AAC, OGG), Documents (TXT, PDF, DOC, DOCX)');
      return;
    }

    if (file.size > maxSize) {
      alert('File size must be less than 100MB');
      return;
    }

    setFile(file);
  };

  return (
    <div
      className={`upload-box ${dragActive ? 'drag-active' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <div className="upload-content">
        <div className="upload-icon">📁</div>
        <p className="upload-text">
          Drag & drop your file here, or{" "}
          <label className="upload-link">
            browse
            <input
              type="file"
              onChange={handleChange}
              accept="image/jpeg,image/jpg,image/png,video/mp4,video/avi"
              style={{ display: "none" }}
            />
          </label>
        </p>
        <p className="upload-hint">
          Supports: JPG, PNG images and MP4, AVI videos (max 100MB)
        </p>
      </div>
    </div>
  );
}