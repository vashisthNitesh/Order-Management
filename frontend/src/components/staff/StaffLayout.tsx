"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, ChefHat, LogOut, Bell, UtensilsCrossed } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { authApi } from "@/lib/api";
import toast from "react-hot-toast";

interface StaffLayoutProps {
  children: React.ReactNode;
}

export function StaffLayout({ children }: StaffLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, clearAuth } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/staff/login");
    }
  }, [isAuthenticated, router]);

  const handleLogout = async () => {
    try {
      const token = useAuthStore.getState().refreshToken;
      if (token) await authApi.logout(token);
    } catch {}
    clearAuth();
    toast.success("Logged out");
    router.push("/staff/login");
  };

  if (!isAuthenticated) return null;

  const navItems = [
    { href: "/staff/dashboard", icon: LayoutDashboard, label: "Orders" },
    { href: "/staff/kitchen", icon: ChefHat, label: "Kitchen" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
      {/* Top Nav */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 sticky top-0 z-30">
        <div className="flex items-center justify-between px-4 h-14">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-orange-500 to-amber-500 rounded-xl flex items-center justify-center">
              <UtensilsCrossed className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="font-bold text-gray-900 dark:text-white text-sm">Staff Portal</span>
              <span className="block text-[10px] text-gray-400">{user?.restaurant || "Restaurant"}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="hidden sm:block text-xs text-gray-500 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded-lg capitalize">
              {user?.role}
            </span>
            <button
              onClick={handleLogout}
              className="w-8 h-8 text-gray-500 hover:text-red-500 flex items-center justify-center rounded-xl hover:bg-red-50 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab nav */}
        <nav className="flex border-t border-gray-50 dark:border-gray-800">
          {navItems.map(({ href, icon: Icon, label }) => (
            <Link
              key={href}
              href={href}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors ${
                pathname === href
                  ? "text-orange-500 border-b-2 border-orange-500"
                  : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}
        </nav>
      </header>

      <main className="flex-1">{children}</main>
    </div>
  );
}
