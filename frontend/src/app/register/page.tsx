'use client';

import { useForm, SubmitHandler } from 'react-hook-form';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import Link from 'next/link';
import { FiMail, FiLock, FiUserPlus } from 'react-icons/fi';
import toast from 'react-hot-toast';

type RegisterInputs = {
  email: string;
  password: string;
  confirmPassword: string;
};

export default function RegisterPage() {
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm<RegisterInputs>();
  const router = useRouter();
  const password = watch('password');

  const onSubmit: SubmitHandler<RegisterInputs> = async (data) => {
    try {
      const { confirmPassword, ...registerData } = data;
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/register`,
        registerData
      );
      toast.success('Đăng ký thành công! Đang chuyển đến trang đăng nhập...');
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } catch (error: any) {
      const detail = error.response?.data?.detail || 'Đã có lỗi xảy ra khi đăng ký.';
      toast.error(detail);
      console.error('Registration error:', error);
    }
  };

  return (
    <main className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100">
      <div className="w-full max-w-md p-10 space-y-8 bg-white/90 rounded-3xl shadow-2xl border border-blue-100">
        <div className="text-center">
          <div className="inline-block p-4 bg-gradient-to-tr from-blue-200 to-blue-400 rounded-full mb-5 shadow">
            <FiUserPlus className="w-10 h-10 text-blue-700" />
          </div>
          <h1 className="text-4xl font-extrabold text-blue-900 tracking-tight">Tạo tài khoản</h1>
          <p className="mt-2 text-base text-gray-500">Bắt đầu hành trình của bạn với chúng tôi.</p>
        </div>
        
        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5">
          <div className="relative">
            <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-400" />
            <input
              type="email"
              placeholder="Email của bạn"
              autoComplete="email"
              {...register('email', { 
                required: 'Email không được để trống',
                pattern: { value: /^\S+@\S+$/i, message: 'Địa chỉ email không hợp lệ' }
              })}
              className={`w-full pl-12 pr-4 py-3 border ${errors.email ? 'border-red-400' : 'border-blue-200'} rounded-xl bg-blue-50 focus:bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition-all text-gray-800 placeholder:text-gray-400`}
            />
            {errors.email && <p className="text-red-500 text-xs mt-2 ml-1">{errors.email.message}</p>}
          </div>

          <div className="relative">
            <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-400" />
            <input
              type="password"
              placeholder="Mật khẩu"
              autoComplete="new-password"
              {...register('password', { 
                required: 'Mật khẩu không được để trống',
                minLength: { value: 6, message: 'Mật khẩu phải có ít nhất 6 ký tự' }
              })}
              className={`w-full pl-12 pr-4 py-3 border ${errors.password ? 'border-red-400' : 'border-blue-200'} rounded-xl bg-blue-50 focus:bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition-all text-gray-800 placeholder:text-gray-400`}
            />
            {errors.password && <p className="text-red-500 text-xs mt-2 ml-1">{errors.password.message}</p>}
          </div>

          <div className="relative">
            <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-400" />
            <input
              type="password"
              placeholder="Xác nhận mật khẩu"
              autoComplete="new-password"
              {...register('confirmPassword', { 
                required: 'Vui lòng xác nhận mật khẩu',
                validate: value => value === password || 'Mật khẩu xác nhận không khớp'
              })}
              className={`w-full pl-12 pr-4 py-3 border ${errors.confirmPassword ? 'border-red-400' : 'border-blue-200'} rounded-xl bg-blue-50 focus:bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition-all text-gray-800 placeholder:text-gray-400`}
            />
            {errors.confirmPassword && <p className="text-red-500 text-xs mt-2 ml-1">{errors.confirmPassword.message}</p>}
          </div>

          <div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center py-3 px-4 rounded-xl shadow-md text-base font-semibold text-white bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-300 transition-all duration-200 disabled:opacity-60"
            >
              {isSubmitting ? 'Đang xử lý...' : 'Đăng ký'}
            </button>
          </div>
        </form>

        <p className="mt-8 text-center text-sm text-gray-500">
          Đã có tài khoản?{' '}
          <Link href="/login" className="font-semibold text-blue-600 hover:underline hover:text-blue-800 transition-colors">
            Đăng nhập
          </Link>
        </p>
      </div>
    </main>
  );
}