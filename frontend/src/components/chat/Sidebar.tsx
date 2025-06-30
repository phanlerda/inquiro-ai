'use client';

import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Document } from '@/types/chat';
import {
  FiLogOut,
  FiPlusSquare,
  FiFileText,
  FiUploadCloud,
  FiTrash2,
  FiLoader,
  FiAlertCircle,
  FiInfo
} from 'react-icons/fi';
import UploadModal from './UploadModal';
import ConfirmationModal from './ConfirmationModal';

interface SidebarProps {
  onSelectDocument: (doc: Document) => void;
  onNewChat: () => void;
  selectedDocumentId: number | null;
}

export default function Sidebar({ onSelectDocument, onNewChat, selectedDocumentId }: SidebarProps) {
  const { logout, token } = useAuthStore();
  const router = useRouter();
  const [isUploadModalOpen, setUploadModalOpen] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [docToDelete, setDocToDelete] = useState<Document | null>(null);

  const fetchDocuments = async () => {
    if (!token) return;
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/documents/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDocuments(response.data);
    } catch (error) {
      console.error("Failed to fetch documents:", error);
      toast.error("Không thể tải danh sách tài liệu.");
    } finally {
      if(isLoading) setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchDocuments();
      const intervalId = setInterval(() => {
        fetchDocuments();
      }, 10000);
      return () => clearInterval(intervalId);
    }
  }, [token]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const handleDeleteClick = (doc: Document, event: React.MouseEvent) => {
    event.stopPropagation();
    setDocToDelete(doc);
  };

  const confirmDelete = async () => {
    if (!docToDelete || !token) return;
    const toastId = toast.loading("Đang xóa tài liệu...");
    try {
      await axios.delete(`${process.env.NEXT_PUBLIC_API_URL}/documents/${docToDelete.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Đã xóa thành công!`, { id: toastId });
      setDocToDelete(null);
      fetchDocuments();
      if(selectedDocumentId === docToDelete.id) {
        onNewChat();
      }
    } catch (error) {
      console.error("Failed to delete document:", error);
      toast.error("Xóa tài liệu thất bại!", { id: toastId });
      setDocToDelete(null);
    }
  };
  
  const renderDocStatusIcon = (status: Document['status']) => {
    switch (status) {
      case 'PROCESSING':
        return <FiLoader className="mr-2 text-yellow-400 shrink-0 animate-spin" title="Đang xử lý..."/>;
      case 'FAILED':
        return <FiAlertCircle className="mr-2 text-red-500 shrink-0" title="Xử lý thất bại"/>;
      default:
        return <FiFileText className="mr-2 text-blue-400 shrink-0" />;
    }
  }

  return (
    <>
      <div className="w-1/5 min-w-[280px] bg-gradient-to-b from-blue-900 via-blue-800 to-blue-700 text-white p-5 flex flex-col h-screen rounded-r-3xl shadow-2xl border-r border-blue-200">
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-center tracking-tight drop-shadow">🤖 Inquiro AI</h1>
        </div>

        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white font-semibold py-2 px-4 rounded-xl mb-2 shadow transition-all duration-150"
        >
          <FiPlusSquare className="mr-2" />
          Cuộc trò chuyện mới
        </button>

        <button
          onClick={() => setUploadModalOpen(true)}
          className="w-full flex items-center justify-center bg-gradient-to-r from-teal-500 to-teal-400 hover:from-teal-600 hover:to-teal-500 text-white font-semibold py-2 px-4 rounded-xl mb-4 shadow transition-all duration-150"
        >
          <FiUploadCloud className="mr-2" />
          Upload Tài liệu
        </button>

        <div className="flex-grow overflow-y-auto border-t border-blue-700 pt-4 custom-scrollbar">
          <h2 className="text-xs font-bold text-blue-200 uppercase mb-3 tracking-widest">Tài liệu của bạn</h2>
          {isLoading ? (
            <div className="flex items-center justify-center h-full py-8">
              <FiLoader className="animate-spin text-blue-200" size={28}/>
            </div>
          ) : documents.length > 0 ? (
            documents.map((doc) => {
              const isSelectable = doc.status === 'COMPLETED';
              return (
                <div
                  key={doc.id}
                  onClick={() => {
                    if (isSelectable && typeof onSelectDocument === 'function') {
                      onSelectDocument(doc);
                    }
                  }}
                  className={`group p-3 rounded-xl text-base mb-2 flex items-center justify-between transition-all duration-150 ${
                    isSelectable ? 'hover:bg-blue-800 cursor-pointer' : 'opacity-60 cursor-not-allowed'
                  } ${
                    selectedDocumentId === doc.id ? 'bg-blue-800 border border-blue-400' : ''
                  }`}
                  title={isSelectable ? doc.filename : `Tài liệu đang ở trạng thái: ${doc.status}`}
                >
                  <div className="flex items-center truncate">
                    {renderDocStatusIcon(doc.status)}
                    <span className="truncate">{doc.filename}</span>
                  </div>
                  <button 
                    onClick={(e) => handleDeleteClick(doc, e)}
                    className="p-1 rounded-md text-blue-200 hover:bg-red-500 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Xóa tài liệu"
                  >
                    <FiTrash2 size={16} />
                  </button>
                </div>
              )
            })
          ) : (
            <div className="text-center text-base text-blue-200 mt-6 p-4 border border-dashed border-blue-400 rounded-xl bg-blue-900/30">
              <FiInfo className="mx-auto mb-2" size={28} />
              <p>Bạn chưa có tài liệu nào.</p>
              <p>Hãy nhấn <span className="font-semibold">Upload Tài liệu</span> để bắt đầu.</p>
            </div>
          )}
        </div>

        <div className="mt-auto border-t border-blue-700 pt-5">
          <button
            onClick={handleLogout}
            className="w-full flex items-center text-base text-red-300 hover:bg-red-600 hover:text-white py-2 px-3 rounded-xl transition-all duration-150 font-semibold"
          >
            <FiLogOut className="mr-2" />
            Đăng xuất
          </button>
        </div>
      </div>
      
      <UploadModal 
        isOpen={isUploadModalOpen} 
        onClose={() => {
          setUploadModalOpen(false);
          fetchDocuments();
        }} 
      />
      <ConfirmationModal
        isOpen={!!docToDelete}
        onClose={() => setDocToDelete(null)}
        onConfirm={confirmDelete}
        title="Xác nhận Xóa"
        message={`Bạn có chắc chắn muốn xóa vĩnh viễn tài liệu "${docToDelete?.filename}" không?`}
      />
    </>
  );
}