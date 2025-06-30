'use client';

import { FiX, FiAlertTriangle } from 'react-icons/fi';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
}

export default function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
}: ConfirmationModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md border border-red-100 animate-fadeIn">
        {/* Close button */}
        <button
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 transition-colors"
          onClick={onClose}
          aria-label="Đóng"
        >
          <FiX className="w-5 h-5" />
        </button>
        <div className="flex items-center p-6 pb-2">
          <div className="mr-4 flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 shadow">
            <FiAlertTriangle className="h-7 w-7 text-red-600" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">{title}</h3>
            <p className="mt-1 text-gray-500">{message}</p>
          </div>
        </div>
        <div className="px-6 pb-6 pt-2 flex flex-col sm:flex-row-reverse gap-3">
          <button
            type="button"
            className="inline-flex justify-center rounded-xl shadow px-5 py-2 bg-gradient-to-r from-red-500 to-red-700 text-base font-semibold text-white hover:from-red-600 hover:to-red-800 focus:outline-none focus:ring-2 focus:ring-red-300 transition-all sm:w-auto"
            onClick={() => {
              onConfirm();
              onClose();
            }}
          >
            Xóa
          </button>
          <button
            type="button"
            className="inline-flex justify-center rounded-xl border border-gray-300 shadow px-5 py-2 bg-white text-base font-semibold text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-200 transition-all sm:w-auto"
            onClick={onClose}
          >
            Hủy
          </button>
        </div>
      </div>
    </div>
  );
}