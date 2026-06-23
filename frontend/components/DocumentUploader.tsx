'use client';

import React, { useState } from 'react';
import { ingestFile } from '@/lib/aiApi';
import nextToast from 'next/toast';

interface DocumentUploaderProps {
  sessionId: string;
}

const DocumentUploader: React.FC<DocumentUploaderProps> = ({ sessionId }) => {
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    if (!sessionId) {
      nextToast.error('Session ID is required to upload files.');
      return;
    }

    setIsUploading(true);
    setProgress(0);
    setSuccessMessage(null);

    try {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/files/upload`);
      xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('token') || ''}`);
      xhr.setRequestHeader('Content-Type', file.type);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100);
          setProgress(percentComplete);
        }
      };

      xhr.onload = () => {
        setIsUploading(false);
        if (xhr.status >= 200 && xhr.status < 300) {
          const contentType = xhr.getResponseHeader('Content-Type');
          if (contentType && contentType.includes('application/json')) {
            const response = JSON.parse(xhr.responseText);
            setSuccessMessage(`✓ Indexed ${response.chunks_indexed} chunks`);
          } else {
            nextToast.error('Unexpected response format from server.');
          }
        } else {
          const contentType = xhr.getResponseHeader('Content-Type');
          if (contentType && contentType.includes('application/json')) {
            const errorResponse = JSON.parse(xhr.responseText);
            nextToast.error(errorResponse.message || 'File upload failed.');
          } else {
            nextToast.error('File upload failed with an unknown error.');
          }
        }
      };

      xhr.onerror = () => {
        setIsUploading(false);
        nextToast.error('Network error occurred during file upload.');
      };

      const formData = new FormData();
      formData.append('file', file);
      formData.append('sessionId', sessionId);
      xhr.send(formData);
    } catch (error) {
      setIsUploading(false);
      nextToast.error('An unexpected error occurred.');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)) {
        handleFileUpload(file);
      } else {
        nextToast.error('Unsupported file type. Please upload .xlsx, .xls, .pdf, or .docx files.');
      }
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)) {
        handleFileUpload(file);
      } else {
        nextToast.error('Unsupported file type. Please upload .xlsx, .xls, .pdf, or .docx files.');
      }
    }
  };

  return (
    <div className="p-4 border border-dashed border-gray-300 rounded-md bg-gray-50">
      <div
        className="flex flex-col items-center justify-center h-32 cursor-pointer"
        onDrop={handleDrop}
        onDragOver={(event) => event.preventDefault()}
      >
        <p className="text-gray-500">Drag and drop your file here</p>
        <p className="text-gray-500">or</p>
        <label className="text-blue-500 cursor-pointer">
          Select a file
          <input
            type="file"
            className="hidden"
            onChange={handleFileSelect}
            accept=".xlsx,.xls,.pdf,.docx"
          />
        </label>
      </div>
      {isUploading && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-blue-500 h-4 rounded-full"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-gray-500 text-sm mt-2">{progress}% uploaded</p>
        </div>
      )}
      {successMessage && (
        <div className="mt-4 text-green-500 text-sm">{successMessage}</div>
      )}
    </div>
  );
};

export default DocumentUploader;