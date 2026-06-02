"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Search, X, UtensilsCrossed, ChefHat } from "lucide-react";
import Image from "next/image";
import { useQuery } from "@tanstack/react-query";
import { tableApi, categoryApi, menuItemApi, offerApi } from "@/lib/api";
import { Category, MenuItem, Offer } from "@/types";
import { useCartStore } from "@/store/cartStore";
import { MenuItemCard } from "@/components/customer/MenuItemCard";
import { FloatingCartButton } from "@/components/customer/FloatingCartButton";
import { CartSheet } from "@/components/customer/CartSheet";
import { OfferBanner } from "@/components/customer/OfferBanner";
import { MenuSkeleton } from "@/components/customer/MenuSkeleton";
import { Input } from "@/components/ui/input";
import { getImageUrl } from "@/lib/utils";

const RESTAURANT_ID = parseInt(process.env.NEXT_PUBLIC_DEFAULT_RESTAURANT_ID || "1");

export default function MenuPage({ params }: { params: { tableId: string } }) {
  const tableId = parseInt(params.tableId);
  const [activeCategory, setActiveCategory] = useState<number | "popular" | "specials">("popular");
  const [search, setSearch] = useState("");
  const { setTable } = useCartStore();
  const categoryRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const { data: table } = useQuery({
    queryKey: ["table", tableId],
    queryFn: () => tableApi.get(tableId).then((r) => r.data),
  });

  const { data: categories = [], isLoading } = useQuery<Category[]>({
    queryKey: ["categories", RESTAURANT_ID],
    queryFn: () =>
      categoryApi.list(RESTAURANT_ID).then((r) => r.data.results || r.data),
  });

  const { data: popularItems = [] } = useQuery<MenuItem[]>({
    queryKey: ["popular-items", RESTAURANT_ID],
    queryFn: () => menuItemApi.popular(RESTAURANT_ID).then((r) => r.data),
  });

  const { data: specialItems = [] } = useQuery<MenuItem[]>({
    queryKey: ["special-items", RESTAURANT_ID],
    queryFn: () => menuItemApi.specials(RESTAURANT_ID).then((r) => r.data),
  });

  const { data: offers = [] } = useQuery<Offer[]>({
    queryKey: ["offers", RESTAURANT_ID],
    queryFn: () =>
      offerApi
        .list({ restaurant: RESTAURANT_ID, active_only: "true" })
        .then((r) => r.data.results || r.data),
  });

  useEffect(() => {
    if (table) {
      setTable(table.id, table.restaurant);
    }
  }, [table, setTable]);

  const getDisplayedItems = (): MenuItem[] => {
    let items: MenuItem[] = [];

    if (activeCategory === "popular") {
      items = popularItems;
    } else if (activeCategory === "specials") {
      items = specialItems;
    } else {
      const cat = categories.find((c) => c.id === activeCategory);
      items = cat?.items || [];
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      items = items.filter(
        (item) =>
          item.name.toLowerCase().includes(q) ||
          item.description.toLowerCase().includes(q)
      );
    }

    return items;
  };

  const displayedItems = getDisplayedItems();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 pb-32">
      {/* Hero header */}
      <div className="relative bg-gradient-to-br from-orange-600 via-orange-500 to-amber-500 pt-safe">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-20 -right-20 w-64 h-64 bg-white/10 rounded-full" />
          <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-white/5 rounded-full" />
        </div>
        <div className="relative px-4 pt-8 pb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <UtensilsCrossed className="w-5 h-5 text-white/80" />
              <span className="text-white/80 text-sm font-medium">The Grand Bistro</span>
            </div>
            <div className="glass rounded-xl px-3 py-1.5 text-white text-xs font-bold flex items-center gap-1.5">
              <span>🍽️</span> Table {table?.table_number || tableId}
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white mb-1">
            What would you like?
          </h1>
          <p className="text-white/70 text-sm">Browse our menu and order directly</p>
        </div>

        {/* Search */}
        <div className="px-4 pb-5">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search dishes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 pr-10 bg-white dark:bg-gray-800 border-0 shadow-lg rounded-2xl h-12"
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                className="absolute right-3.5 top-1/2 -translate-y-1/2"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="px-4 space-y-6 pt-5">
        {/* Offers */}
        {offers.length > 0 && <OfferBanner offers={offers} />}

        {/* Category tabs */}
        {isLoading ? (
          <MenuSkeleton />
        ) : (
          <>
            <div className="flex gap-2 overflow-x-auto scrollbar-hide pb-1">
              {/* Special tabs */}
              {[
                { key: "popular" as const, label: "⭐ Popular", count: popularItems.length },
                { key: "specials" as const, label: "👨‍🍳 Specials", count: specialItems.length },
              ].map(({ key, label, count }) => (
                <motion.button
                  key={key}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setActiveCategory(key)}
                  className={`flex-shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-semibold transition-all duration-200 ${
                    activeCategory === key
                      ? "bg-orange-500 text-white shadow-lg shadow-orange-200"
                      : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:border-orange-300"
                  }`}
                >
                  {label}
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded-full ${
                      activeCategory === key
                        ? "bg-white/30 text-white"
                        : "bg-gray-100 dark:bg-gray-700 text-gray-500"
                    }`}
                  >
                    {count}
                  </span>
                </motion.button>
              ))}

              {/* Category tabs */}
              {categories
                .filter((c) => c.is_active)
                .map((cat) => (
                  <motion.button
                    key={cat.id}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setActiveCategory(cat.id)}
                    className={`flex-shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-semibold transition-all duration-200 ${
                      activeCategory === cat.id
                        ? "bg-orange-500 text-white shadow-lg shadow-orange-200"
                        : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:border-orange-300"
                    }`}
                  >
                    {cat.icon && <span>{cat.icon}</span>}
                    {cat.name}
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded-full ${
                        activeCategory === cat.id
                          ? "bg-white/30 text-white"
                          : "bg-gray-100 dark:bg-gray-700 text-gray-500"
                      }`}
                    >
                      {cat.item_count}
                    </span>
                  </motion.button>
                ))}
            </div>

            {/* Section title */}
            <div className="flex items-center gap-2">
              <ChefHat className="w-4 h-4 text-orange-500" />
              <h2 className="font-bold text-gray-900 dark:text-white">
                {activeCategory === "popular"
                  ? "Popular Items"
                  : activeCategory === "specials"
                  ? "Chef's Specials"
                  : categories.find((c) => c.id === activeCategory)?.name || ""}
              </h2>
              <span className="text-xs text-gray-400 font-medium">
                {displayedItems.length} items
              </span>
            </div>

            {/* Items grid */}
            {displayedItems.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center py-16 text-center"
              >
                <div className="text-6xl mb-4">🍽️</div>
                <p className="font-semibold text-gray-700 dark:text-gray-300">
                  {search ? "No items found" : "No items available"}
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  {search ? "Try a different search" : "Check back later"}
                </p>
              </motion.div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {displayedItems.map((item) => (
                  <MenuItemCard key={item.id} item={item} />
                ))}
              </div>
            )}
          </>
        )}
      </div>

      <FloatingCartButton />
      <CartSheet />
    </div>
  );
}
