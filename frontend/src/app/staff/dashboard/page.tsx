"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RefreshCw, Filter } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Order, OrderStatus } from "@/types";
import { orderApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { StaffLayout } from "@/components/staff/StaffLayout";
import { OrderCard } from "@/components/staff/OrderCard";
import { Skeleton } from "@/components/ui/skeleton";

const STATUS_TABS: { value: OrderStatus | "all"; label: string; color: string }[] = [
  { value: "all", label: "All", color: "bg-gray-100 text-gray-700" },
  { value: "pending", label: "New", color: "bg-yellow-100 text-yellow-700" },
  { value: "confirmed", label: "Confirmed", color: "bg-blue-100 text-blue-700" },
  { value: "preparing", label: "Cooking", color: "bg-emerald-100 text-emerald-700" },
  { value: "ready", label: "Ready", color: "bg-green-100 text-green-700" },
  { value: "served", label: "Served", color: "bg-gray-100 text-gray-500" },
];

export default function StaffDashboardPage() {
  const [activeStatus, setActiveStatus] = useState<OrderStatus | "all">("all");
  const { user } = useAuthStore();

  const { data, isLoading, refetch, isRefetching } = useQuery<{ results: Order[]; count: number }>({
    queryKey: ["orders", activeStatus, user?.restaurant_id],
    queryFn: () =>
      orderApi
        .list({
          ...(activeStatus !== "all" ? { status: activeStatus } : {}),
          ...(user?.restaurant_id ? { restaurant: user.restaurant_id } : {}),
          ordering: "-created_at",
        })
        .then((r) => r.data),
    refetchInterval: 15000,
  });

  const orders = data?.results || (Array.isArray(data) ? data as Order[] : []);

  const countByStatus = (status: OrderStatus | "all") => {
    if (status === "all") return orders.length;
    return orders.filter((o) => o.status === status).length;
  };

  return (
    <StaffLayout>
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-gray-900 dark:text-white">
            Orders Dashboard
          </h2>
          <button
            onClick={() => refetch()}
            className={`w-9 h-9 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex items-center justify-center text-gray-500 hover:text-orange-500 transition-colors ${
              isRefetching ? "animate-spin" : ""
            }`}
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Status tabs */}
        <div className="flex gap-2 overflow-x-auto scrollbar-hide pb-1">
          {STATUS_TABS.map(({ value, label, color }) => (
            <button
              key={value}
              onClick={() => setActiveStatus(value)}
              className={`flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 ${
                activeStatus === value
                  ? "bg-emerald-600 text-white shadow-md"
                  : `${color} hover:ring-2 hover:ring-emerald-200`
              }`}
            >
              {label}
              <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                activeStatus === value ? "bg-white/30 text-white" : "bg-white/60"
              }`}>
                {isLoading ? "·" : countByStatus(value)}
              </span>
            </button>
          ))}
        </div>

        {/* Orders */}
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-32 rounded-2xl" />
            ))}
          </div>
        ) : orders.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center py-20 text-center"
          >
            <div className="text-5xl mb-3">📋</div>
            <p className="font-semibold text-gray-700 dark:text-gray-300">No orders</p>
            <p className="text-sm text-gray-400 mt-1">
              {activeStatus === "all" ? "No orders yet" : `No ${activeStatus} orders`}
            </p>
          </motion.div>
        ) : (
          <AnimatePresence mode="popLayout">
            <div className="space-y-3">
              {orders.map((order) => (
                <OrderCard key={order.id} order={order} />
              ))}
            </div>
          </AnimatePresence>
        )}
      </div>
    </StaffLayout>
  );
}
