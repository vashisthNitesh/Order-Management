"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, ArrowRight, Clock } from "lucide-react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export default function OrderSuccessPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const orderNumber = searchParams.get("order");
  const orderId = searchParams.get("id");

  useEffect(() => {
    if (!orderNumber) router.push("/");
  }, [orderNumber, router]);

  if (!orderNumber) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-amber-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-sm text-center">
        {/* Success animation */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", damping: 15, stiffness: 300 }}
          className="w-28 h-28 mx-auto mb-6 relative"
        >
          <div className="absolute inset-0 bg-green-100 dark:bg-green-900/30 rounded-full animate-ping opacity-30" />
          <div className="relative w-28 h-28 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center shadow-2xl shadow-green-200">
            <CheckCircle2 className="w-14 h-14 text-white" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-4"
        >
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
              Order Placed! 🎉
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Your order has been sent to the kitchen
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 border border-gray-100 dark:border-gray-700 shadow-sm">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Order Number</p>
            <p className="text-2xl font-bold text-orange-500 font-mono tracking-wider">
              #{orderNumber}
            </p>
          </div>

          <div className="bg-orange-50 dark:bg-orange-900/20 rounded-2xl p-4 flex items-start gap-3 text-left">
            <Clock className="w-5 h-5 text-orange-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-gray-900 dark:text-white text-sm">Estimated Time</p>
              <p className="text-xs text-gray-500 mt-0.5">15-25 minutes</p>
            </div>
          </div>

          <div className="flex flex-col gap-2 pt-2">
            <Link href={`/order/tracking/${orderId}`}>
              <Button variant="brand" size="lg" className="w-full rounded-2xl">
                Track Your Order <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link href="/menu/1">
              <Button variant="outline" size="lg" className="w-full rounded-2xl">
                Back to Menu
              </Button>
            </Link>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
