// frontend/src/components/chat/UploadModal.tsx
'use client';

import { useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '@/store/authStore';
import { FiUploadCloud, FiX } from 'react-icons/fi';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function UploadModal({ isOpen, onClose }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');
  const { token } = useAuthStore();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
      setMessage('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('Vui lòng chọn một file.');
      return;
    }
    if (!token) {
      setMessage('Lỗi xác thực. Vui lòng đăng nhập lại.');
      return;
    }

    setIsUploading(true);
    setMessage('Đang tải lên...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/documents/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setMessage(`Tải lên thành công! Document ID: ${response.data.id}. Backend đang xử lý...`);
      setFile(null);
    } catch (error: any) {
      console.error(error);
      setMessage(error.response?.data?.detail || 'Tải lên thất bại.');
    } finally {
      setIsUploading(false);
    }
  };
  
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center">
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Upload Tài liệu</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-800"><FiX size={24} /></button>
        </div>
        <div className="mb-4">
          <label className="w-full flex flex-col items-center px-4 py-6 bg-white text-blue-500 rounded-lg shadow-lg tracking-wide uppercase border border-blue-500 cursor-pointer hover:bg-blue-500 hover:text-white">
            <FiUploadCloud size={32} />
            <span className="mt-2 text-base leading-normal">{file ? file.name : 'Chọn một file PDF'}</span>
            <input type='file' className="hidden" onChange={handleFileChange} accept=".pdf" />
          </label>
        </div>
        <button
          onClick={handleUpload}
          disabled={isUploading || !file}
          className="w-full bg-brand-primary text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:opacity-50"
        >
          {isUploading ? 'Đang xử lý...' : 'Tải lên'}
        </button>
        {message && <p className="mt-4 text-sm text-center">{message}</p>}
      </div>
    </div>
  );
}