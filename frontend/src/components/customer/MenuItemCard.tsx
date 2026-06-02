"use client";

import { motion } from "framer-motion";
import { Plus, Minus, Star, Clock } from "lucide-react";
import Image from "next/image";
import { MenuItem } from "@/types";
import { useCartStore } from "@/store/cartStore";
import { formatPrice, getImageUrl } from "@/lib/utils";
import { FoodTypeBadge } from "./FoodTypeBadge";
import { Button } from "@/components/ui/button";

interface MenuItemCardProps {
  item: MenuItem;
}

export function MenuItemCard({ item }: MenuItemCardProps) {
  const { items, addItem, updateQuantity } = useCartStore();
  const cartItem = items.find((i) => i.menuItem.id === item.id);
  const quantity = cartItem?.quantity || 0;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="group relative bg-white dark:bg-gray-800 rounded-2xl overflow-hidden shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300"
    >
      {/* Image */}
      <div className="relative h-44 overflow-hidden bg-gray-100 dark:bg-gray-700">
        <Image
          src={getImageUrl(item.image_url || item.image)}
          alt={item.name}
          fill
          className="object-cover group-hover:scale-105 transition-transform duration-500"
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          onError={(e) => {
            (e.target as HTMLImageElement).src = "/images/placeholder-food.jpg";
          }}
        />
        {/* Badges */}
        <div className="absolute top-2 left-2 flex gap-1.5">
          {item.is_popular && (
            <span className="bg-emerald-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
              <Star className="w-2.5 h-2.5 fill-white" /> Popular
            </span>
          )}
          {item.is_special && (
            <span className="bg-purple-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
              Chef's Special
            </span>
          )}
        </div>
        {!item.is_available && (
          <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
            <span className="text-white font-semibold text-sm bg-black/50 px-3 py-1 rounded-full">
              Not Available
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-1.5">
            <FoodTypeBadge type={item.food_type} />
            <h3 className="font-semibold text-gray-900 dark:text-white text-sm leading-tight">
              {item.name}
            </h3>
          </div>
        </div>

        <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mb-3 leading-relaxed">
          {item.description}
        </p>

        <div className="flex items-center gap-2 mb-3">
          {item.preparation_time && (
            <span className="flex items-center gap-1 text-[11px] text-gray-400">
              <Clock className="w-3 h-3" /> {item.preparation_time}m
            </span>
          )}
          {item.calories && (
            <span className="text-[11px] text-gray-400">{item.calories} cal</span>
          )}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-lg font-bold text-gray-900 dark:text-white">
            {formatPrice(item.price)}
          </span>

          {item.is_available && (
            <div>
              {quantity === 0 ? (
                <Button
                  size="sm"
                  variant="brand"
                  onClick={() => addItem(item)}
                  className="h-8 px-4 rounded-xl"
                >
                  <Plus className="w-3.5 h-3.5" /> Add
                </Button>
              ) : (
                <div className="flex items-center gap-1.5 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-1">
                  <button
                    onClick={() => updateQuantity(item.id, quantity - 1)}
                    className="w-7 h-7 bg-white dark:bg-gray-700 rounded-lg shadow-sm flex items-center justify-center hover:bg-gray-50 transition-colors"
                  >
                    <Minus className="w-3 h-3 text-emerald-600" />
                  </button>
                  <span className="w-6 text-center font-bold text-emerald-600 text-sm">
                    {quantity}
                  </span>
                  <button
                    onClick={() => addItem(item)}
                    className="w-7 h-7 bg-emerald-600 rounded-lg shadow-sm flex items-center justify-center hover:bg-emerald-700 transition-colors"
                  >
                    <Plus className="w-3 h-3 text-white" />
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
