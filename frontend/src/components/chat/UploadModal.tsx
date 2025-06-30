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
    <div className="fixed inset-0 z-50 flex justify-center items-center bg-black/60">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md border border-blue-100 animate-fadeIn p-7 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-700 transition-colors"
          aria-label="Đóng"
        >
          <FiX size={22} />
        </button>
        <div className="flex flex-col items-center mb-6">
          <div className="bg-blue-100 rounded-full p-4 mb-3 shadow">
            <FiUploadCloud size={32} className="text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-blue-800 mb-1">Upload Tài liệu</h2>
          <p className="text-gray-500 text-sm">Chỉ hỗ trợ file PDF.</p>
        </div>
        <div className="mb-5">
          <label className="w-full flex flex-col items-center px-4 py-6 bg-blue-50 text-blue-600 rounded-xl shadow-inner tracking-wide border-2 border-dashed border-blue-300 cursor-pointer hover:bg-blue-100 hover:text-blue-800 transition-all">
            <span className="mt-2 text-base leading-normal truncate">{file ? file.name : 'Chọn một file PDF'}</span>
            <input type='file' className="hidden" onChange={handleFileChange} accept=".pdf" />
          </label>
        </div>
        <button
          onClick={handleUpload}
          disabled={isUploading || !file}
          className="w-full bg-gradient-to-r from-blue-500 to-blue-700 text-white py-2 px-4 rounded-xl font-semibold hover:from-blue-600 hover:to-blue-800 transition-all disabled:opacity-50"
        >
          {isUploading ? 'Đang xử lý...' : 'Tải lên'}
        </button>
        {message && (
          <p className={`mt-5 text-center text-sm ${message.includes('thành công') ? 'text-green-600' : 'text-red-500'}`}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
}