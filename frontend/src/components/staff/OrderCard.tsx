"use client";

import { motion } from "framer-motion";
import { Clock, MapPin, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Order, OrderStatus } from "@/types";
import { orderApi } from "@/lib/api";
import { formatPrice, getStatusColor, getStatusLabel } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import toast from "react-hot-toast";

interface OrderCardProps {
  order: Order;
}

const STATUS_NEXT: Record<OrderStatus, OrderStatus | null> = {
  pending: "confirmed",
  confirmed: "preparing",
  preparing: "ready",
  ready: "served",
  served: null,
  cancelled: null,
};

const STATUS_NEXT_LABEL: Record<OrderStatus, string> = {
  pending: "Confirm",
  confirmed: "Start Cooking",
  preparing: "Mark Ready",
  ready: "Mark Served",
  served: "",
  cancelled: "",
};

export function OrderCard({ order }: OrderCardProps) {
  const [expanded, setExpanded] = useState(false);
  const queryClient = useQueryClient();

  const { mutate: updateStatus, isPending } = useMutation({
    mutationFn: (status: OrderStatus) => orderApi.updateStatus(order.id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      toast.success("Order status updated");
    },
    onError: () => toast.error("Failed to update status"),
  });

  const nextStatus = STATUS_NEXT[order.status as OrderStatus];
  const elapsed = Math.floor(
    (Date.now() - new Date(order.created_at).getTime()) / 60000
  );

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden shadow-sm"
    >
      {/* Card header */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-bold text-gray-900 dark:text-white font-mono text-sm">
                #{order.order_number}
              </span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getStatusColor(
                  order.status
                )}`}
              >
                {getStatusLabel(order.status)}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-400">
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3" /> Table {order.table_number}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" /> {elapsed}m ago
              </span>
              {order.customer_name && (
                <span className="text-gray-500">{order.customer_name}</span>
              )}
            </div>
          </div>
          <div className="text-right">
            <p className="font-bold text-gray-900 dark:text-white">
              {formatPrice(order.total_amount)}
            </p>
            <p className="text-xs text-gray-400">{order.items.length} items</p>
          </div>
        </div>

        {/* Items preview */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between text-xs text-gray-500 hover:text-gray-700 transition-colors py-1"
        >
          <span>
            {order.items
              .slice(0, 3)
              .map((i) => `${i.quantity}× ${i.menu_item_name}`)
              .join(", ")}
            {order.items.length > 3 && ` +${order.items.length - 3} more`}
          </span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {/* Expanded items */}
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            className="mt-2 space-y-1 border-t border-gray-50 dark:border-gray-800 pt-2"
          >
            {order.items.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400"
              >
                <span className="flex items-center gap-1.5">
                  <span className="w-4 h-4 bg-orange-100 dark:bg-orange-900/30 text-orange-600 rounded flex items-center justify-center font-bold text-[10px]">
                    {item.quantity}
                  </span>
                  {item.menu_item_name}
                </span>
                <span>{formatPrice(item.subtotal)}</span>
              </div>
            ))}
            {order.special_instructions && (
              <p className="text-xs text-orange-600 bg-orange-50 dark:bg-orange-900/20 rounded-lg px-2 py-1 mt-1">
                📝 {order.special_instructions}
              </p>
            )}
          </motion.div>
        )}
      </div>

      {/* Action */}
      {nextStatus && (
        <div className="px-4 pb-4">
          <Button
            variant="brand"
            size="sm"
            className="w-full rounded-xl"
            onClick={() => updateStatus(nextStatus)}
            disabled={isPending}
          >
            {isPending ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              STATUS_NEXT_LABEL[order.status as OrderStatus]
            )}
          </Button>
        </div>
      )}
    </motion.div>
  );
}
