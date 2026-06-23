'use client';

import React, { useState } from 'react';
import { ingestFile } from '@/lib/aiApi';
import nextToast from 'next/toast';

interface DocumentUploaderProps {
  sessionId: string;
}

const DocumentUploader: React.FC<DocumentUploaderProps> = ({ sessionId }) => {
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);

  const handleFileUpload = async (file: File) => {
    if (!sessionId) {
      nextToast.error('Session ID is required.');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication token not found.');
      }

      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/files/upload`, true);
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.setRequestHeader('Content-Type', file.type);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(progress);
        }
      };

      xhr.onload = () => {
        setIsUploading(false);
        if (xhr.status >= 200 && xhr.status < 300) {
          const contentType = xhr.getResponseHeader('Content-Type');
          if (contentType && contentType.includes('application/json')) {
            const response = JSON.parse(xhr.responseText);
            nextToast.success(`✓ Indexed ${response.chunks_indexed} chunks`);
          } else {
            throw new Error('Unexpected response format.');
          }
        } else {
          const errorResponse = JSON.parse(xhr.responseText);
          throw new Error(errorResponse.message || 'File upload failed.');
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
      nextToast.error(error.message || 'An error occurred during file upload.');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  return (
    <div
      className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center cursor-pointer"
      onDragOver={(event) => event.preventDefault()}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept=".xlsx,.xls,.pdf,.docx"
        className="hidden"
        id="file-upload"
        onChange={handleFileSelect}
      />
      <label htmlFor="file-upload" className="block text-gray-600">
        Drag and drop a file here or <span className="text-blue-500 underline">browse</span>
      </label>
      {isUploading && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-blue-500 h-4 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600 mt-2">{uploadProgress}% uploaded</p>
        </div>
      )}
    </div>
  );
};

export default DocumentUploader;