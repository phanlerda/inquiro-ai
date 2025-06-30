import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import AuthGuard from '@/components/AuthGuard';
import { Toaster } from 'react-hot-toast';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: '🤖 Inquiro AI',
  description: 'Chat với tài liệu của bạn',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="bg-gradient-to-br from-blue-50 via-white to-blue-100">
      <body className={`${inter.className} min-h-screen text-gray-800 bg-transparent`}>
        <Toaster 
          position="top-center"
          toastOptions={{
            duration: 5000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
        <AuthGuard>
          {children}
        </AuthGuard>
      </body>
    </html>
  );
}