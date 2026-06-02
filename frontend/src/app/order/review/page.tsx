"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, ChevronRight, MapPin, MessageSquare } from "lucide-react";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { useCartStore } from "@/store/cartStore";
import { orderApi } from "@/lib/api";
import { formatPrice, getImageUrl } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FoodTypeBadge } from "@/components/customer/FoodTypeBadge";
import toast from "react-hot-toast";

export default function OrderReviewPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tableId = searchParams.get("table");

  const { items, tableId: cartTableId, restaurantId, clearCart, totalPrice } = useCartStore();
  const [specialInstructions, setSpecialInstructions] = useState("");
  const [customerName, setCustomerName] = useState("");

  const { mutate: placeOrder, isPending } = useMutation({
    mutationFn: () =>
      orderApi.create({
        restaurant: restaurantId || 1,
        table: cartTableId || parseInt(tableId || "1"),
        special_instructions: specialInstructions,
        customer_name: customerName,
        items: items.map((item) => ({
          menu_item: item.menuItem.id,
          quantity: item.quantity,
          special_instructions: item.specialInstructions || "",
        })),
      }),
    onSuccess: (response) => {
      const order = response.data;
      clearCart();
      router.push(`/order/success?order=${order.order_number}&id=${order.id}`);
    },
    onError: () => {
      toast.error("Failed to place order. Please try again.");
    },
  });

  if (items.length === 0) {
    router.push(`/menu/${tableId || cartTableId || 1}`);
    return null;
  }

  const subtotal = totalPrice();
  const tax = subtotal * 0.1;
  const total = subtotal + tax;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 pb-32">
      {/* Header */}
      <div className="bg-white dark:bg-gray-900 px-4 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-3 sticky top-0 z-10">
        <button
          onClick={() => router.back()}
          className="w-9 h-9 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h1 className="font-bold text-gray-900 dark:text-white">Review Order</h1>
          <p className="text-xs text-gray-500">Table {tableId || cartTableId}</p>
        </div>
      </div>

      <div className="px-4 py-5 space-y-4">
        {/* Items */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl overflow-hidden border border-gray-100 dark:border-gray-800">
          <div className="px-4 py-3 border-b border-gray-50 dark:border-gray-800">
            <h2 className="font-semibold text-gray-900 dark:text-white text-sm">
              Order Items ({items.length})
            </h2>
          </div>
          <div className="divide-y divide-gray-50 dark:divide-gray-800">
            {items.map((cartItem) => (
              <motion.div
                key={cartItem.menuItem.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center gap-3 p-4"
              >
                <div className="relative w-14 h-14 rounded-xl overflow-hidden flex-shrink-0">
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
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <FoodTypeBadge type={cartItem.menuItem.food_type} size="sm" />
                    <p className="font-medium text-gray-900 dark:text-white text-sm truncate">
                      {cartItem.menuItem.name}
                    </p>
                  </div>
                  <p className="text-xs text-gray-400">
                    {formatPrice(cartItem.menuItem.price)} × {cartItem.quantity}
                  </p>
                </div>
                <span className="font-bold text-gray-900 dark:text-white text-sm">
                  {formatPrice(parseFloat(cartItem.menuItem.price) * cartItem.quantity)}
                </span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Table info */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-4 border border-gray-100 dark:border-gray-800 flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl flex items-center justify-center">
            <MapPin className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Dining at</p>
            <p className="font-semibold text-gray-900 dark:text-white">
              Table {tableId || cartTableId}
            </p>
          </div>
        </div>

        {/* Customer name (optional) */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-4 border border-gray-100 dark:border-gray-800 space-y-3">
          <h3 className="font-semibold text-gray-900 dark:text-white text-sm">Your Name (optional)</h3>
          <Input
            placeholder="Enter your name..."
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            className="rounded-xl"
          />
        </div>

        {/* Special instructions */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-4 border border-gray-100 dark:border-gray-800 space-y-3">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-emerald-600" />
            <h3 className="font-semibold text-gray-900 dark:text-white text-sm">Special Instructions</h3>
          </div>
          <textarea
            placeholder="Any allergies or special requests..."
            value={specialInstructions}
            onChange={(e) => setSpecialInstructions(e.target.value)}
            rows={3}
            className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none transition-all"
          />
        </div>

        {/* Bill summary */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-4 border border-gray-100 dark:border-gray-800 space-y-3">
          <h3 className="font-semibold text-gray-900 dark:text-white text-sm">Bill Summary</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-gray-600 dark:text-gray-400">
              <span>Subtotal</span>
              <span>{formatPrice(subtotal)}</span>
            </div>
            <div className="flex justify-between text-gray-600 dark:text-gray-400">
              <span>Tax (10%)</span>
              <span>{formatPrice(tax)}</span>
            </div>
            <div className="h-px bg-gray-100 dark:bg-gray-800" />
            <div className="flex justify-between font-bold text-gray-900 dark:text-white text-base">
              <span>Total</span>
              <span className="text-emerald-600">{formatPrice(total)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Place order button */}
      <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800 p-4 safe-area-bottom">
        <Button
          variant="brand"
          size="lg"
          className="w-full rounded-2xl"
          onClick={() => placeOrder()}
          disabled={isPending}
        >
          {isPending ? (
            <span className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Placing Order...
            </span>
          ) : (
            <>
              Place Order · {formatPrice(total)}
              <ChevronRight className="w-5 h-5" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
