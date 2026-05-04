"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Header } from "@/components/layouts/header";
import { AdminSidebar } from "@/components/layouts/sidebar";
import { ToastContainer } from "@/components/layouts/toast-container";
import { useAuth } from "@/lib/hooks/use-auth";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, user, _hasHydrated } = useAuth();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    // Wait for hydration before checking auth
    if (!_hasHydrated) return;

    if (!isAuthenticated || !user) {
      router.replace("/login");
      return;
    }

    // Define allowed admin roles
    const adminRoles = ["super_admin", "admin", "org_admin"];

    // Only admin roles can access admin layout
    if (!adminRoles.includes(user.role)) {
      console.log(`Access denied: user role "${user.role}" is not an admin role`);
      router.replace("/search");
      return;
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setChecked(true);
  }, [isAuthenticated, user, router, _hasHydrated]);

  // Show nothing while checking authentication
  if (!checked) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="text-sm text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-background min-h-screen">
      <AdminSidebar />

      {/* Main content area - offset by sidebar width */}
      <div className="lg:pl-64">
        <Header />
        <main className="p-6">{children}</main>
      </div>

      <ToastContainer />
    </div>
  );
}
