"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ShoppingBag } from "lucide-react";
import { useCartStore } from "@/store/cartStore";
import { formatPrice } from "@/lib/utils";

export function FloatingCartButton() {
  const { totalItems, totalPrice, openCart } = useCartStore();
  const count = totalItems();

  return (
    <AnimatePresence>
      {count > 0 && (
        <motion.button
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          transition={{ type: "spring", damping: 20, stiffness: 300 }}
          onClick={openCart}
          className="fixed bottom-6 left-4 right-4 z-30 mx-auto max-w-sm"
        >
          <div className="bg-gradient-to-r from-emerald-600 to-teal-500 rounded-2xl shadow-2xl shadow-emerald-400/40 p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <ShoppingBag className="w-6 h-6 text-white" />
                <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-white text-emerald-700 rounded-full text-[10px] font-bold flex items-center justify-center">
                  {count}
                </span>
              </div>
              <span className="text-white font-semibold">{count} item{count > 1 ? "s" : ""}</span>
            </div>
            <div className="text-white font-bold">{formatPrice(totalPrice())}</div>
          </div>
        </motion.button>
      )}
    </AnimatePresence>
  );
}
