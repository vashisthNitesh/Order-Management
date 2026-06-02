"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Search, Edit2, Trash2, X, Upload } from "lucide-react";
import Image from "next/image";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { MenuItem, Category } from "@/types";
import { menuItemApi, categoryApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { AdminLayout } from "@/components/admin/AdminLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FoodTypeBadge } from "@/components/customer/FoodTypeBadge";
import { formatPrice, getImageUrl } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import toast from "react-hot-toast";

const itemSchema = z.object({
  name: z.string().min(1, "Required"),
  description: z.string().optional(),
  price: z.string().min(1, "Required"),
  category: z.string().min(1, "Required"),
  food_type: z.enum(["veg", "non_veg", "vegan"]),
  is_available: z.boolean(),
  is_popular: z.boolean(),
  is_special: z.boolean(),
  preparation_time: z.string(),
});

type ItemForm = z.infer<typeof itemSchema>;

function MenuItemModal({
  item,
  categories,
  onClose,
}: {
  item?: MenuItem;
  categories: Category[];
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const { register, handleSubmit, formState: { errors } } = useForm<ItemForm>({
    resolver: zodResolver(itemSchema),
    defaultValues: {
      name: item?.name || "",
      description: item?.description || "",
      price: item?.price?.toString() || "",
      category: item?.category?.toString() || "",
      food_type: (item?.food_type as any) || "veg",
      is_available: item?.is_available ?? true,
      is_popular: item?.is_popular ?? false,
      is_special: item?.is_special ?? false,
      preparation_time: item?.preparation_time?.toString() || "15",
    },
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (data: ItemForm) => {
      const payload = {
        ...data,
        price: parseFloat(data.price),
        category: parseInt(data.category),
        preparation_time: parseInt(data.preparation_time),
      };
      return item
        ? menuItemApi.update(item.id, payload)
        : menuItemApi.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["menu-items"] });
      toast.success(item ? "Item updated!" : "Item created!");
      onClose();
    },
    onError: () => toast.error("Failed to save item"),
  });

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white dark:bg-gray-900 rounded-3xl p-6 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-bold text-gray-900 dark:text-white text-lg">
            {item ? "Edit Item" : "Add Menu Item"}
          </h2>
          <button onClick={onClose} className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit((d) => mutate(d))} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2 space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Item Name *</label>
              <Input {...register("name")} placeholder="e.g. Grilled Salmon" />
              {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Price *</label>
              <Input {...register("price")} type="number" step="0.01" placeholder="0.00" />
              {errors.price && <p className="text-xs text-red-500">{errors.price.message}</p>}
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Prep Time (min)</label>
              <Input {...register("preparation_time")} type="number" placeholder="15" />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Category *</label>
              <select
                {...register("category")}
                className="w-full h-10 rounded-xl border border-input bg-background px-3 text-sm"
              >
                <option value="">Select category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
              {errors.category && <p className="text-xs text-red-500">{errors.category.message}</p>}
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Food Type *</label>
              <select
                {...register("food_type")}
                className="w-full h-10 rounded-xl border border-input bg-background px-3 text-sm"
              >
                <option value="veg">Vegetarian</option>
                <option value="non_veg">Non-Vegetarian</option>
                <option value="vegan">Vegan</option>
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Description</label>
            <textarea
              {...register("description")}
              rows={2}
              placeholder="Brief description..."
              className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm resize-none"
            />
          </div>

          {/* Toggles */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { name: "is_available", label: "Available" },
              { name: "is_popular", label: "Popular" },
              { name: "is_special", label: "Special" },
            ].map(({ name, label }) => (
              <label key={name} className="flex items-center gap-2 cursor-pointer bg-gray-50 dark:bg-gray-800 rounded-xl p-3">
                <input
                  type="checkbox"
                  {...register(name as keyof ItemForm)}
                  className="w-4 h-4 rounded accent-orange-500"
                />
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{label}</span>
              </label>
            ))}
          </div>

          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1 rounded-xl">Cancel</Button>
            <Button type="submit" variant="brand" className="flex-1 rounded-xl" disabled={isPending}>
              {isPending ? "Saving..." : item ? "Update" : "Create"}
            </Button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

export default function AdminMenuPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editItem, setEditItem] = useState<MenuItem | undefined>();

  const { data: items = [], isLoading } = useQuery<MenuItem[]>({
    queryKey: ["menu-items", user?.restaurant_id],
    queryFn: () =>
      menuItemApi
        .list(user?.restaurant_id ? { category__restaurant: user.restaurant_id } : {})
        .then((r) => r.data.results || r.data),
  });

  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ["categories", user?.restaurant_id],
    queryFn: () =>
      categoryApi.list(user?.restaurant_id ?? undefined).then((r) => r.data.results || r.data),
  });

  const { mutate: deleteItem } = useMutation({
    mutationFn: (id: number) => menuItemApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["menu-items"] });
      toast.success("Item deleted");
    },
  });

  const filtered = items.filter((item) =>
    item.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AdminLayout>
      <div className="p-6 space-y-5">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search items..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 rounded-xl"
            />
          </div>
          <Button
            variant="brand"
            onClick={() => { setEditItem(undefined); setModalOpen(true); }}
            className="rounded-xl whitespace-nowrap"
          >
            <Plus className="w-4 h-4" /> Add Item
          </Button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-48 rounded-2xl" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((item) => (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden group"
              >
                <div className="relative h-36 bg-gray-100 dark:bg-gray-800">
                  <Image
                    src={getImageUrl(item.image_url || item.image)}
                    alt={item.name}
                    fill
                    className="object-cover"
                    onError={(e) => { (e.target as HTMLImageElement).src = "/images/placeholder-food.jpg"; }}
                  />
                  {!item.is_available && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                      <span className="text-white text-xs font-bold bg-black/50 px-2 py-1 rounded-full">Unavailable</span>
                    </div>
                  )}
                  <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => { setEditItem(item); setModalOpen(true); }}
                      className="w-7 h-7 bg-white rounded-lg shadow flex items-center justify-center hover:bg-gray-50"
                    >
                      <Edit2 className="w-3.5 h-3.5 text-gray-600" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm("Delete this item?")) deleteItem(item.id);
                      }}
                      className="w-7 h-7 bg-white rounded-lg shadow flex items-center justify-center hover:bg-red-50"
                    >
                      <Trash2 className="w-3.5 h-3.5 text-red-500" />
                    </button>
                  </div>
                </div>
                <div className="p-4">
                  <div className="flex items-center gap-1.5 mb-1">
                    <FoodTypeBadge type={item.food_type} />
                    <h3 className="font-semibold text-gray-900 dark:text-white text-sm truncate">{item.name}</h3>
                  </div>
                  <p className="text-xs text-gray-400 mb-2 truncate">{item.category_name}</p>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-orange-500">{formatPrice(item.price)}</span>
                    <div className="flex gap-1">
                      {item.is_popular && <span className="text-[10px] bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded-full font-medium">Popular</span>}
                      {item.is_special && <span className="text-[10px] bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded-full font-medium">Special</span>}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {filtered.length === 0 && !isLoading && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-4xl mb-2">🍽️</p>
            <p className="font-medium">No menu items found</p>
          </div>
        )}
      </div>

      {modalOpen && (
        <MenuItemModal
          item={editItem}
          categories={categories}
          onClose={() => setModalOpen(false)}
        />
      )}
    </AdminLayout>
  );
}
