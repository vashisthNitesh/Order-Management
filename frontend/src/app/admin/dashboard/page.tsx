"use client";

import { motion } from "framer-motion";
import {
  ShoppingBag,
  DollarSign,
  Clock,
  CheckCircle2,
  TrendingUp,
  Activity,
  RefreshCw,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { orderApi } from "@/lib/api";
import { Order, DashboardStats } from "@/types";
import { useAuthStore } from "@/store/authStore";
import { AdminLayout } from "@/components/admin/AdminLayout";
import { StatCard } from "@/components/admin/StatCard";
import { formatPrice, formatDate, getStatusColor, getStatusLabel } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export default function AdminDashboardPage() {
  const { user } = useAuthStore();

  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>({
    queryKey: ["dashboard-stats", user?.restaurant_id],
    queryFn: () =>
      orderApi.dashboardStats(user?.restaurant_id ?? undefined).then((r) => r.data),
    refetchInterval: 30000,
  });

  const { data: recentOrders, isLoading: ordersLoading } = useQuery<Order[]>({
    queryKey: ["recent-orders", user?.restaurant_id],
    queryFn: () =>
      orderApi
        .list({
          ordering: "-created_at",
          ...(user?.restaurant_id ? { restaurant: user.restaurant_id } : {}),
        })
        .then((r) => {
          const data = r.data;
          return (data.results || data).slice(0, 10);
        }),
    refetchInterval: 15000,
  });

  return (
    <AdminLayout>
      <div className="p-6 space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {statsLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-32 rounded-2xl" />
              ))
            : [
                {
                  title: "Today's Orders",
                  value: stats?.today_orders || 0,
                  icon: ShoppingBag,
                  color: "orange",
                },
                {
                  title: "Today's Revenue",
                  value: formatPrice(stats?.today_revenue || 0),
                  icon: DollarSign,
                  color: "green",
                },
                {
                  title: "Pending Orders",
                  value: stats?.pending_orders || 0,
                  icon: Clock,
                  color: "blue",
                },
                {
                  title: "Preparing",
                  value: stats?.preparing_orders || 0,
                  icon: Activity,
                  color: "purple",
                },
              ].map((card) => (
                <motion.div
                  key={card.title}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <StatCard {...card} />
                </motion.div>
              ))}
        </div>

        {/* Ready orders alert */}
        {stats && stats.ready_orders > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-2xl p-4 flex items-center gap-3"
          >
            <div className="w-10 h-10 bg-green-100 dark:bg-green-900/40 rounded-xl flex items-center justify-center flex-shrink-0">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="font-semibold text-green-800 dark:text-green-400 text-sm">
                {stats.ready_orders} order{stats.ready_orders > 1 ? "s" : ""} ready to serve
              </p>
              <p className="text-xs text-green-600">Please serve your customers</p>
            </div>
          </motion.div>
        )}

        {/* Recent orders */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-50 dark:border-gray-800">
            <h2 className="font-bold text-gray-900 dark:text-white">Recent Orders</h2>
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <RefreshCw className="w-3 h-3" /> Live
            </span>
          </div>

          {ordersLoading ? (
            <div className="divide-y divide-gray-50 dark:divide-gray-800">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="px-6 py-3">
                  <Skeleton className="h-10 rounded-xl" />
                </div>
              ))}
            </div>
          ) : (
            <div className="divide-y divide-gray-50 dark:divide-gray-800">
              {recentOrders?.map((order) => (
                <div
                  key={order.id}
                  className="flex items-center gap-3 px-6 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                >
                  <div className="w-8 h-8 bg-orange-100 dark:bg-orange-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                    <ShoppingBag className="w-4 h-4 text-orange-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-gray-900 dark:text-white">
                        #{order.order_number}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full border ${getStatusColor(
                          order.status
                        )}`}
                      >
                        {getStatusLabel(order.status)}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400">
                      Table {order.table_number} · {order.items.length} items ·{" "}
                      {formatDate(order.created_at)}
                    </p>
                  </div>
                  <span className="font-bold text-gray-900 dark:text-white text-sm">
                    {formatPrice(order.total_amount)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}
