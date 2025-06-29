// frontend/src/components/AuthGuard.tsx
'use client';

import { useAuthStore } from '@/store/authStore';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect, ReactNode } from 'react';

interface AuthGuardProps {
  children: ReactNode;
}

const publicPaths = ['/login', '/register']; // Các trang không cần xác thực

export default function AuthGuard({ children }: AuthGuardProps) {
  const { token } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!token && !publicPaths.includes(pathname)) {
      router.push('/login');
    }
  }, [token, router, pathname]);

  // Nếu đang ở trang public, hoặc đã có token, thì hiển thị children
  if (publicPaths.includes(pathname) || token) {
    return <>{children}</>;
  }

  // Trường hợp khác (ví dụ: đang load, hoặc chuyển hướng) có thể hiển thị một spinner
  return null; 
}