// frontend/src/app/login/page.tsx
'use client'; // Đánh dấu là Client Component

import { useForm, SubmitHandler } from 'react-hook-form';
import axios from 'axios';
import { useRouter } from 'next/navigation'; // Dùng next/navigation cho App Router
import { useAuthStore } from '@/store/authStore';
import { useState } from 'react';
import Link from 'next/link';

type Inputs = {
  username: string; // API của chúng ta dùng username cho email
  password: string;
};

export default function LoginPage() {
  const { register, handleSubmit, formState: { errors } } = useForm<Inputs>();
  const router = useRouter();
  const { setToken } = useAuthStore();
  const [apiError, setApiError] = useState<string | null>(null);

  const onSubmit: SubmitHandler<Inputs> = async (data) => {
    setApiError(null);
    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/login`,
        new URLSearchParams(data), // Gửi dưới dạng x-www-form-urlencoded
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
      setToken(response.data.access_token);
      // Tạm thời không lấy user info từ đây, sẽ làm sau khi có endpoint /me
      router.push('/'); // Chuyển hướng về trang chủ (hoặc trang chat)
    } catch (error: any) {
      if (error.response && error.response.data && error.response.data.detail) {
        setApiError(error.response.data.detail);
      } else {
        setApiError('Đã có lỗi xảy ra khi đăng nhập.');
      }
      console.error('Login error:', error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h1 className="text-2xl font-bold mb-6 text-center">Đăng nhập</h1>
        {apiError && <p className="text-red-500 text-sm mb-4">{apiError}</p>}
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700">Email (Username)</label>
            <input
              type="email"
              {...register('username', { required: 'Email không được để trống' })}
              className={`mt-1 block w-full px-3 py-2 border ${errors.username ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary sm:text-sm`}
            />
            {errors.username && <p className="text-red-500 text-xs mt-1">{errors.username.message}</p>}
          </div>
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700">Mật khẩu</label>
            <input
              type="password"
              {...register('password', { required: 'Mật khẩu không được để trống' })}
              className={`mt-1 block w-full px-3 py-2 border ${errors.password ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary sm:text-sm`}
            />
            {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
          </div>
          <button
            type="submit"
            className="w-full bg-brand-primary text-white py-2 px-4 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-primary"
          >
            Đăng nhập
          </button>
        </form>
        <p className="mt-4 text-center text-sm">
          Chưa có tài khoản?{' '}
          <Link href="/register" className="font-medium text-brand-primary hover:text-blue-600">
            Đăng ký ngay
          </Link>
        </p>
      </div>
    </div>
  );
}