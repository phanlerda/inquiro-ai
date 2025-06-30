'use client';

import { useForm, SubmitHandler } from 'react-hook-form';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import Link from 'next/link';
import { FiMail, FiLock, FiLogIn } from 'react-icons/fi';
import toast from 'react-hot-toast';

type Inputs = {
  username: string; // API của chúng ta dùng username cho email
  password: string;
};

export default function LoginPage() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Inputs>();
  const router = useRouter();
  const { setToken } = useAuthStore();

  const onSubmit: SubmitHandler<Inputs> = async (data) => {
    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/login`,
        new URLSearchParams(data),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );
      toast.success('Đăng nhập thành công!');
      setToken(response.data.access_token);
      router.push('/'); // Chuyển hướng về trang chat chính
    } catch (error: any) {
      const detail = error.response?.data?.detail || 'Email hoặc mật khẩu không chính xác.';
      toast.error(detail);
      console.error('Login error:', error);
    }
  };

  return (
    <main className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100">
      <div className="w-full max-w-md p-10 space-y-8 bg-white/90 rounded-3xl shadow-2xl border border-blue-100">
        <div className="text-center">
          <div className="inline-block p-4 bg-gradient-to-tr from-blue-200 to-blue-400 rounded-full mb-5 shadow">
            <FiLogIn className="w-10 h-10 text-blue-700" />
          </div>
          <h1 className="text-4xl font-extrabold text-blue-900 tracking-tight">Đăng nhập</h1>
          <p className="mt-2 text-base text-gray-500">Chào mừng bạn trở lại!</p>
        </div>
        
        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5">
          <div className="relative">
            <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-400" />
            <input
              type="email"
              placeholder="Email của bạn"
              autoComplete="email"
              {...register('username', { required: 'Email không được để trống' })}
              className={`w-full pl-12 pr-4 py-3 border ${errors.username ? 'border-red-400' : 'border-blue-200'} rounded-xl bg-blue-50 focus:bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition-all text-gray-800 placeholder:text-gray-400`}
            />
            {errors.username && <p className="text-red-500 text-xs mt-2 ml-1">{errors.username.message}</p>}
          </div>

          <div className="relative">
            <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-400" />
            <input
              type="password"
              placeholder="Mật khẩu"
              autoComplete="current-password"
              {...register('password', { required: 'Mật khẩu không được để trống' })}
              className={`w-full pl-12 pr-4 py-3 border ${errors.password ? 'border-red-400' : 'border-blue-200'} rounded-xl bg-blue-50 focus:bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition-all text-gray-800 placeholder:text-gray-400`}
            />
            {errors.password && <p className="text-red-500 text-xs mt-2 ml-1">{errors.password.message}</p>}
          </div>

          <div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center py-3 px-4 rounded-xl shadow-md text-base font-semibold text-white bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-300 transition-all duration-200 disabled:opacity-60"
            >
              {isSubmitting ? 'Đang xử lý...' : 'Đăng nhập'}
            </button>
          </div>
        </form>

        <p className="mt-8 text-center text-sm text-gray-500">
          Chưa có tài khoản?{' '}
          <Link href="/register" className="font-semibold text-blue-600 hover:underline hover:text-blue-800 transition-colors">
            Đăng ký ngay
          </Link>
        </p>
      </div>
    </main>
  );
}