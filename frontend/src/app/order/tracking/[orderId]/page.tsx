"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Clock, CheckCircle2, ChefHat, Bell, UtensilsCrossed, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { orderApi } from "@/lib/api";
import { Order, OrderStatus } from "@/types";
import { formatPrice, formatDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import Link from "next/link";

const STATUS_STEPS: { status: OrderStatus; label: string; icon: React.ReactNode; desc: string }[] = [
  { status: "pending", label: "Order Received", icon: <Clock className="w-5 h-5" />, desc: "We received your order" },
  { status: "confirmed", label: "Confirmed", icon: <CheckCircle2 className="w-5 h-5" />, desc: "Order confirmed by staff" },
  { status: "preparing", label: "Preparing", icon: <ChefHat className="w-5 h-5" />, desc: "Chef is cooking your meal" },
  { status: "ready", label: "Ready", icon: <Bell className="w-5 h-5" />, desc: "Your order is ready!" },
  { status: "served", label: "Served", icon: <UtensilsCrossed className="w-5 h-5" />, desc: "Enjoy your meal!" },
];

function getStepIndex(status: OrderStatus): number {
  return STATUS_STEPS.findIndex((s) => s.status === status);
}

export default function OrderTrackingPage({ params }: { params: { orderId: string } }) {
  const router = useRouter();
  const orderId = parseInt(params.orderId);

  const { data: order, isLoading } = useQuery<Order>({
    queryKey: ["order", orderId],
    queryFn: () => orderApi.get(orderId).then((r) => r.data),
    refetchInterval: 10000,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4 text-center">
        <div>
          <div className="text-5xl mb-3">😕</div>
          <p className="font-semibold text-gray-900">Order not found</p>
          <Link href="/">
            <Button variant="brand" className="mt-4">Go Home</Button>
          </Link>
        </div>
      </div>
    );
  }

  const currentStepIndex = order.status === "cancelled" ? -1 : getStepIndex(order.status as OrderStatus);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 pb-12">
      {/* Header */}
      <div className="bg-white dark:bg-gray-900 px-4 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-3 sticky top-0 z-10">
        <button
          onClick={() => router.back()}
          className="w-9 h-9 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h1 className="font-bold text-gray-900 dark:text-white">Track Order</h1>
          <p className="text-xs text-gray-500 font-mono">#{order.order_number}</p>
        </div>
        <div className="ml-auto">
          <span className="text-xs text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded-lg">
            Auto-refreshing
          </span>
        </div>
      </div>

      <div className="px-4 py-5 space-y-4">
        {/* Status card */}
        {order.status === "cancelled" ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 dark:bg-red-900/20 rounded-2xl p-6 text-center border border-red-100 dark:border-red-800"
          >
            <XCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
            <h2 className="font-bold text-red-700 dark:text-red-400 text-lg">Order Cancelled</h2>
            <p className="text-red-500 text-sm mt-1">Your order has been cancelled</p>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-100 dark:border-gray-800"
          >
            {/* Progress Steps */}
            <div className="relative">
              {/* Connector line */}
              <div className="absolute left-5 top-5 bottom-5 w-0.5 bg-gray-100 dark:bg-gray-800 z-0" />
              <div
                className="absolute left-5 top-5 w-0.5 bg-emerald-500 z-0 transition-all duration-1000"
                style={{
                  height: `${currentStepIndex >= 0 ? (currentStepIndex / (STATUS_STEPS.length - 1)) * 100 : 0}%`,
                }}
              />

              <div className="relative z-10 space-y-6">
                {STATUS_STEPS.map((step, index) => {
                  const isComplete = index < currentStepIndex;
                  const isActive = index === currentStepIndex;
                  const isPending = index > currentStepIndex;

                  return (
                    <motion.div
                      key={step.status}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center gap-4"
                    >
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-500 ${
                          isComplete
                            ? "bg-emerald-600 text-white shadow-lg shadow-emerald-200"
                            : isActive
                            ? "bg-emerald-600 text-white shadow-lg shadow-emerald-200 ring-4 ring-emerald-100"
                            : "bg-gray-100 dark:bg-gray-800 text-gray-400"
                        }`}
                      >
                        {isComplete ? (
                          <CheckCircle2 className="w-5 h-5" />
                        ) : (
                          <span className={isActive ? "animate-pulse" : ""}>{step.icon}</span>
                        )}
                      </div>
                      <div className="flex-1">
                        <p
                          className={`font-semibold text-sm ${
                            isActive || isComplete
                              ? "text-gray-900 dark:text-white"
                              : "text-gray-400"
                          }`}
                        >
                          {step.label}
                        </p>
                        {isActive && (
                          <p className="text-xs text-emerald-600 mt-0.5">{step.desc}</p>
                        )}
                      </div>
                      {isActive && (
                        <div className="flex gap-1">
                          <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce" />
                          <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce [animation-delay:0.1s]" />
                          <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce [animation-delay:0.2s]" />
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        )}

        {/* Order details */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800">
          <div className="px-4 py-3 border-b border-gray-50 dark:border-gray-800 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 dark:text-white text-sm">Order Details</h2>
            <span className="text-xs text-gray-400 font-mono">#{order.order_number}</span>
          </div>
          <div className="divide-y divide-gray-50 dark:divide-gray-800">
            {order.items.map((item) => (
              <div key={item.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 bg-orange-100 dark:bg-orange-900/30 text-orange-600 rounded-md flex items-center justify-center text-xs font-bold">
                    {item.quantity}
                  </span>
                  <span className="text-gray-700 dark:text-gray-300">{item.menu_item_name}</span>
                </div>
                <span className="font-medium text-gray-900 dark:text-white">
                  {formatPrice(item.subtotal)}
                </span>
              </div>
            ))}
          </div>
          <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between">
            <span className="font-bold text-gray-900 dark:text-white">Total</span>
            <span className="font-bold text-orange-500 text-lg">
              {formatPrice(order.total_amount)}
            </span>
          </div>
        </div>

        {/* Placed at */}
        <p className="text-center text-xs text-gray-400">
          Placed at {formatDate(order.created_at)}
        </p>

        <Link href="/menu/1">
          <Button variant="outline" className="w-full rounded-xl">
            Order More
          </Button>
        </Link>
      </div>
    </div>
  );
}
