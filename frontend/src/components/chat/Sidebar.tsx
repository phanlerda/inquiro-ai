// frontend/src/components/chat/Sidebar.tsx
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
    // Không set isLoading = true ở đây để tránh màn hình loading nhấp nháy mỗi khi tự động làm mới
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/documents/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDocuments(response.data);
    } catch (error) {
      console.error("Failed to fetch documents:", error);
      toast.error("Không thể tải danh sách tài liệu.");
    } finally {
      // Chỉ set isLoading = false ở lần tải đầu tiên
      if(isLoading) setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchDocuments(); // Tải lần đầu
      
      // Thiết lập tự động làm mới mỗi 10 giây
      const intervalId = setInterval(() => {
        console.log("Tự động làm mới danh sách tài liệu...");
        fetchDocuments();
      }, 10000);

      // Dọn dẹp interval khi component bị unmount để tránh memory leak
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
      fetchDocuments(); // Làm mới danh sách ngay sau khi xóa
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
        return <FiFileText className="mr-2 text-gray-400 shrink-0" />;
    }
  }

  return (
    <>
      <div className="w-1/5 min-w-[280px] bg-gray-800 text-white p-4 flex flex-col h-screen">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-center">RAG Chatbot</h1>
        </div>

        <button onClick={onNewChat} className="w-full flex items-center justify-center bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md mb-2 transition-colors duration-150">
          <FiPlusSquare className="mr-2" />
          Cuộc trò chuyện mới
        </button>

         <button onClick={() => setUploadModalOpen(true)} className="w-full flex items-center justify-center bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 px-4 rounded-md mb-4 transition-colors duration-150">
            <FiUploadCloud className="mr-2" />
            Upload Tài liệu
          </button>

        <div className="flex-grow overflow-y-auto border-t border-gray-700 pt-4">
          <h2 className="text-xs font-semibold text-gray-400 uppercase mb-2">Tài liệu của bạn</h2>
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
                <FiLoader className="animate-spin text-gray-400" size={24}/>
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
                  className={`group p-2 rounded-md text-sm mb-1 flex items-center justify-between transition-colors duration-150 ${
                    isSelectable ? 'hover:bg-gray-700 cursor-pointer' : 'opacity-50 cursor-not-allowed'
                  } ${
                    selectedDocumentId === doc.id ? 'bg-gray-700' : ''
                  }`}
                  title={isSelectable ? doc.filename : `Tài liệu đang ở trạng thái: ${doc.status}`}
                >
                  <div className="flex items-center truncate">
                    {renderDocStatusIcon(doc.status)}
                    <span className="truncate">{doc.filename}</span>
                  </div>
                  <button 
                    onClick={(e) => handleDeleteClick(doc, e)}
                    className="p-1 rounded-md text-gray-500 hover:bg-red-500 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Xóa tài liệu"
                  >
                    <FiTrash2 size={14} />
                  </button>
                </div>
              )
            })
          ) : (
            <div className="text-center text-sm text-gray-400 mt-4 p-4 border border-dashed border-gray-600 rounded-lg">
                <FiInfo className="mx-auto mb-2" size={24} />
                <p>Bạn chưa có tài liệu nào.</p>
                <p>Hãy nhấn "Upload Tài liệu" để bắt đầu.</p>
            </div>
          )}
        </div>

        <div className="mt-auto border-t border-gray-700 pt-4">
          <button onClick={handleLogout} className="w-full flex items-center text-sm text-red-400 hover:bg-red-700 hover:text-white py-2 px-3 rounded-md transition-colors duration-150">
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