"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Clock, RefreshCw } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Order, OrderStatus } from "@/types";
import { orderApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { StaffLayout } from "@/components/staff/StaffLayout";
import { formatPrice } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import toast from "react-hot-toast";

const KITCHEN_COLUMNS: { status: OrderStatus; label: string; color: string; bg: string }[] = [
  { status: "pending", label: "New Orders", color: "text-yellow-600", bg: "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800" },
  { status: "preparing", label: "Cooking", color: "text-emerald-600", bg: "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800" },
  { status: "ready", label: "Ready", color: "text-green-600", bg: "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800" },
];

interface KitchenCardProps {
  order: Order;
  onAdvance: (id: number, nextStatus: OrderStatus) => void;
  isPending: boolean;
  nextStatus: OrderStatus | null;
  actionLabel: string;
}

function KitchenCard({ order, onAdvance, isPending, nextStatus, actionLabel }: KitchenCardProps) {
  const elapsed = Math.floor((Date.now() - new Date(order.created_at).getTime()) / 60000);
  const isUrgent = elapsed > 15;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className={`rounded-2xl border p-4 space-y-3 ${isUrgent ? "border-red-300 bg-red-50 dark:bg-red-900/20" : "bg-white dark:bg-gray-900 border-gray-100 dark:border-gray-800"}`}
    >
      <div className="flex items-center justify-between">
        <span className="font-bold font-mono text-sm text-gray-900 dark:text-white">
          #{order.order_number}
        </span>
        <span className={`flex items-center gap-1 text-xs font-medium ${isUrgent ? "text-red-500" : "text-gray-400"}`}>
          <Clock className="w-3 h-3" />
          {elapsed}m
        </span>
      </div>

      <div className="flex items-center gap-1.5">
        <span className="text-xs font-bold text-white bg-emerald-600 px-2 py-0.5 rounded-full">
          T{order.table_number}
        </span>
        {order.customer_name && (
          <span className="text-xs text-gray-500">{order.customer_name}</span>
        )}
      </div>

      <div className="space-y-1.5">
        {order.items.map((item) => (
          <div key={item.id} className="flex items-center gap-2 text-sm">
            <span className="w-6 h-6 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 font-bold rounded text-xs flex items-center justify-center flex-shrink-0">
              {item.quantity}
            </span>
            <span className="text-gray-700 dark:text-gray-300 font-medium">{item.menu_item_name}</span>
          </div>
        ))}
      </div>

      {order.special_instructions && (
        <p className="text-xs bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-2 text-yellow-700 dark:text-yellow-400">
          📝 {order.special_instructions}
        </p>
      )}

      {nextStatus && (
        <Button
          variant="brand"
          size="sm"
          className="w-full rounded-xl"
          onClick={() => onAdvance(order.id, nextStatus)}
          disabled={isPending}
        >
          {actionLabel}
        </Button>
      )}
    </motion.div>
  );
}

export default function KitchenViewPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: allOrders = [], isLoading, refetch, isRefetching } = useQuery<Order[]>({
    queryKey: ["kitchen-orders", user?.restaurant_id],
    queryFn: async () => {
      const responses = await Promise.all([
        orderApi.list({ status: "pending", ...(user?.restaurant_id ? { restaurant: user.restaurant_id } : {}), ordering: "created_at" }),
        orderApi.list({ status: "preparing", ...(user?.restaurant_id ? { restaurant: user.restaurant_id } : {}), ordering: "created_at" }),
        orderApi.list({ status: "ready", ...(user?.restaurant_id ? { restaurant: user.restaurant_id } : {}), ordering: "created_at" }),
      ]);
      return responses.flatMap((r) => r.data.results || r.data);
    },
    refetchInterval: 10000,
  });

  const { mutate: updateStatus, isPending } = useMutation({
    mutationFn: ({ id, status }: { id: number; status: OrderStatus }) =>
      orderApi.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["kitchen-orders"] });
      toast.success("Status updated");
    },
  });

  const getColumnOrders = (status: OrderStatus) =>
    allOrders.filter((o) => o.status === status);

  const nextStatusMap: Record<OrderStatus, { status: OrderStatus | null; label: string }> = {
    pending: { status: "preparing", label: "Start Cooking" },
    preparing: { status: "ready", label: "Mark Ready" },
    ready: { status: "served", label: "Mark Served" },
    confirmed: { status: "preparing", label: "Start Cooking" },
    served: { status: null, label: "" },
    cancelled: { status: null, label: "" },
  };

  return (
    <StaffLayout>
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-gray-900 dark:text-white">Kitchen View</h2>
          <button
            onClick={() => refetch()}
            className={`w-9 h-9 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex items-center justify-center text-gray-500 hover:text-emerald-600 transition-colors ${isRefetching ? "animate-spin" : ""}`}
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {KITCHEN_COLUMNS.map(({ status, label, color, bg }) => {
            const colOrders = getColumnOrders(status);
            return (
              <div key={status} className={`rounded-2xl border p-3 ${bg}`}>
                <div className="flex items-center justify-between mb-3">
                  <h3 className={`font-bold text-sm ${color}`}>{label}</h3>
                  <span className={`text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center ${color} bg-white dark:bg-gray-800`}>
                    {colOrders.length}
                  </span>
                </div>
                <AnimatePresence mode="popLayout">
                  <div className="space-y-3 min-h-[100px]">
                    {isLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                      </div>
                    ) : colOrders.length === 0 ? (
                      <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-center py-8 text-sm text-gray-400"
                      >
                        No orders
                      </motion.p>
                    ) : (
                      colOrders.map((order) => {
                        const { status: next, label: actionLabel } = nextStatusMap[order.status as OrderStatus];
                        return (
                          <KitchenCard
                            key={order.id}
                            order={order}
                            onAdvance={(id, s) => updateStatus({ id, status: s })}
                            isPending={isPending}
                            nextStatus={next}
                            actionLabel={actionLabel}
                          />
                        );
                      })
                    )}
                  </div>
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </StaffLayout>
  );
}
