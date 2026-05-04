import { ToastContainer } from "@/components/layouts/toast-container";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full">{children}</div>
      <ToastContainer />
    </div>
  );
}
