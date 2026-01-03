"use client";
import React, { useState, useEffect } from "react";
import axios from "axios";
import { useDropzone } from "react-dropzone";

const AudioForm: React.FC = () => {
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [audioPreview, setAudioPreview] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Dropzone setup
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      "audio/mpeg": [".mp3"],
      "audio/wav": [".wav"],
      "audio/ogg": [".ogg"],
    },
    multiple: false,
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
    onDrop: (acceptedFiles) => {
      const file = acceptedFiles[0];
      if (file) {
        if (audioPreview) URL.revokeObjectURL(audioPreview); // cleanup old
        setAudioFile(file);
        setAudioPreview(URL.createObjectURL(file)); // temporary preview URL
      }
    },
  });

  // Cleanup preview URL on unmount
  useEffect(() => {
    return () => {
      if (audioPreview) URL.revokeObjectURL(audioPreview);
    };
  }, [audioPreview]);

  // Handle submit
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!audioFile || isLoading) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("my-file", audioFile);

      const res = await axios.post("/api/uploadaudio", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      console.log("Backend response:", res.data);
      alert(`Upload successful: ${JSON.stringify(res.data)}`);
    } catch (err) {
      console.error("Upload error:", err);
      alert("Error uploading file");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div
        {...getRootProps({
          style: {
            border: "2px dashed gray",
            padding: "20px",
            textAlign: "center",
            cursor: "pointer",
          },
        })}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>Drop the audio file here...</p>
        ) : (
          <p>Drag & drop or click to select an audio file</p>
        )}
      </div>

      {/* Preview */}
      {audioPreview && (
        <div style={{ marginTop: "1rem" }}>
          <h4>Preview:</h4>
          <audio controls src={audioPreview}></audio>
        </div>
      )}

      <button
        type="submit"
        disabled={!audioFile || isLoading}
        style={{ marginTop: "1rem" }}
      >
        {isLoading ? "Uploading..." : "Submit"}
      </button>
    </form>
  );
};

export default AudioForm;
