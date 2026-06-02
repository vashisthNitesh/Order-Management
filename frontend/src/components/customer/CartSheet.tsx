"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Minus, Plus, ShoppingBag, Trash2, ArrowRight } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useCartStore } from "@/store/cartStore";
import { formatPrice, getImageUrl } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export function CartSheet() {
  const router = useRouter();
  const {
    items,
    isOpen,
    closeCart,
    updateQuantity,
    removeItem,
    clearCart,
    tableId,
    totalItems,
    totalPrice,
  } = useCartStore();

  const handleCheckout = () => {
    closeCart();
    router.push(`/order/review?table=${tableId}`);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeCart}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full max-w-md bg-white dark:bg-gray-900 z-50 flex flex-col shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b border-gray-100 dark:border-gray-800">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl flex items-center justify-center">
                  <ShoppingBag className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <h2 className="font-bold text-gray-900 dark:text-white">Your Cart</h2>
                  <p className="text-xs text-gray-500">{totalItems()} items</p>
                </div>
              </div>
              <button
                onClick={closeCart}
                className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center hover:bg-gray-200 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Table info */}
            {tableId && (
              <div className="mx-4 mt-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-3 flex items-center gap-2">
                <span className="text-emerald-600 text-xl">🍽️</span>
                <span className="text-sm text-emerald-700 dark:text-emerald-300 font-medium">
                  Table {tableId}
                </span>
              </div>
            )}

            {/* Items */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              <AnimatePresence>
                {items.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex flex-col items-center justify-center h-48 text-center"
                  >
                    <div className="text-5xl mb-3">🛒</div>
                    <p className="text-gray-500 font-medium">Your cart is empty</p>
                    <p className="text-gray-400 text-sm mt-1">Add items from the menu</p>
                  </motion.div>
                ) : (
                  items.map((cartItem) => (
                    <motion.div
                      key={cartItem.menuItem.id}
                      layout
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="flex gap-3 bg-gray-50 dark:bg-gray-800 rounded-2xl p-3"
                    >
                      <div className="relative w-16 h-16 rounded-xl overflow-hidden flex-shrink-0">
                        <Image
                          src={getImageUrl(cartItem.menuItem.image_url || cartItem.menuItem.image)}
                          alt={cartItem.menuItem.name}
                          fill
                          className="object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = "/images/placeholder-food.jpg";
                          }}
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 dark:text-white text-sm truncate">
                          {cartItem.menuItem.name}
                        </p>
                        <p className="text-emerald-600 font-semibold text-sm mt-0.5">
                          {formatPrice(
                            parseFloat(cartItem.menuItem.price) * cartItem.quantity
                          )}
                        </p>
                        <div className="flex items-center justify-between mt-2">
                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() =>
                                updateQuantity(cartItem.menuItem.id, cartItem.quantity - 1)
                              }
                              className="w-6 h-6 rounded-lg bg-white dark:bg-gray-700 shadow-sm flex items-center justify-center hover:bg-gray-100 transition-colors"
                            >
                              <Minus className="w-3 h-3" />
                            </button>
                            <span className="w-5 text-center font-bold text-sm">
                              {cartItem.quantity}
                            </span>
                            <button
                              onClick={() =>
                                updateQuantity(cartItem.menuItem.id, cartItem.quantity + 1)
                              }
                              className="w-6 h-6 rounded-lg bg-emerald-600 shadow-sm flex items-center justify-center hover:bg-emerald-700 transition-colors"
                            >
                              <Plus className="w-3 h-3 text-white" />
                            </button>
                          </div>
                          <button
                            onClick={() => removeItem(cartItem.menuItem.id)}
                            className="text-red-400 hover:text-red-500 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>

            {/* Footer */}
            {items.length > 0 && (
              <div className="p-4 border-t border-gray-100 dark:border-gray-800 space-y-3">
                <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                  <span>Subtotal</span>
                  <span className="font-semibold">{formatPrice(totalPrice())}</span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={clearCart}
                    className="px-3 py-2 text-xs text-red-500 border border-red-200 rounded-xl hover:bg-red-50 transition-colors"
                  >
                    Clear
                  </button>
                  <Button
                    variant="brand"
                    className="flex-1 rounded-xl"
                    onClick={handleCheckout}
                  >
                    Place Order · {formatPrice(totalPrice())}
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
