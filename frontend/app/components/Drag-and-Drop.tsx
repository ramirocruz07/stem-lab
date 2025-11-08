"use client";
import React, { useRef, useState, useEffect } from "react";
import { useDropzone, FileWithPath } from "react-dropzone";

interface DropzoneProps {
  required?: boolean;
  name: string;
}

const Dropzone: React.FC<DropzoneProps> = ({ required, name }) => {
  const hiddenInputRef = useRef<HTMLInputElement | null>(null);
  const [audioPreview, setAudioPreview] = useState<string | null>(null);

  const { getRootProps, getInputProps, open, acceptedFiles } = useDropzone({
    onDrop: (incomingFiles: FileWithPath[]) => {
      // Revoke previous URL if exists
      if (audioPreview) {
        URL.revokeObjectURL(audioPreview);
        console.log("Revoked previous URL");
      }

      if (hiddenInputRef.current) {
        const dataTransfer = new DataTransfer();
        incomingFiles.forEach((file) => {
          dataTransfer.items.add(file);
        });
        hiddenInputRef.current.files = dataTransfer.files;
      }

      // Set new audio preview
      if (incomingFiles.length > 0) {
        setAudioPreview(URL.createObjectURL(incomingFiles[0]));
      }
    },
    accept: {
      "audio/mpeg": [".mp3"],
      "audio/wav": [".wav"],
    },
    multiple: false,
  });

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      if (audioPreview) URL.revokeObjectURL(audioPreview);
    };
  }, [audioPreview]);

  return (
    <div className="container">
      <div {...getRootProps({ className: "dropzone" })}>
        <input
          type="file"
          name={name}
          required={required}
          style={{ opacity: 0, position: "absolute", pointerEvents: "none" }}
          ref={hiddenInputRef}
        />
        <input {...getInputProps()} />
        <p>Drag 'n' drop an audio file here</p>
        <button type="button" onClick={open}>
          Open File Dialog
        </button>
      </div>

      {audioPreview && (
        <div style={{ marginTop: "1rem" }}>
          <h4>Preview:</h4>
          <audio controls src={audioPreview}></audio>
        </div>
      )}

      <aside>
        <h4>Selected File</h4>
        <ul>
          {acceptedFiles.map((file) => (
            <li key={file.path}>
              {file.path} - {file.size} bytes
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
};

export default Dropzone;
