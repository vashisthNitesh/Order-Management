"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, Search, Edit2, Trash2, X } from "lucide-react";
import Image from "next/image";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { MenuItem, Category } from "@/types";
import { menuItemApi, categoryApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { AdminLayout } from "@/components/admin/AdminLayout";
import { ImageUpload } from "@/components/admin/ImageUpload";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FoodTypeBadge } from "@/components/customer/FoodTypeBadge";
import { formatPrice, getImageUrl } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import toast from "react-hot-toast";

const itemSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  price: z.string().min(1, "Price is required"),
  category: z.string().min(1, "Category is required"),
  food_type: z.enum(["veg", "non_veg", "vegan"]),
  is_available: z.boolean(),
  is_popular: z.boolean(),
  is_special: z.boolean(),
  preparation_time: z.string().optional(),
  calories: z.string().optional(),
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
  const [imageFile, setImageFile] = useState<File | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<ItemForm>({
    resolver: zodResolver(itemSchema),
    defaultValues: {
      name: item?.name || "",
      description: item?.description || "",
      price: item?.price?.toString() || "",
      category: item?.category?.toString() || "",
      food_type: item?.food_type || "veg",
      is_available: item?.is_available ?? true,
      is_popular: item?.is_popular ?? false,
      is_special: item?.is_special ?? false,
      preparation_time: item?.preparation_time?.toString() || "15",
      calories: item?.calories?.toString() || "",
    },
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (data: ItemForm) => {
      // Use FormData when an image is attached, plain JSON otherwise
      if (imageFile) {
        const fd = new FormData();
        fd.append("name", data.name);
        fd.append("description", data.description || "");
        fd.append("price", data.price);
        fd.append("category", data.category);
        fd.append("food_type", data.food_type);
        fd.append("is_available", String(data.is_available));
        fd.append("is_popular", String(data.is_popular));
        fd.append("is_special", String(data.is_special));
        fd.append("preparation_time", data.preparation_time || "15");
        if (data.calories) fd.append("calories", data.calories);
        fd.append("image", imageFile);
        return item ? menuItemApi.update(item.id, fd) : menuItemApi.create(fd);
      }
      const payload: Record<string, unknown> = {
        ...data,
        price: parseFloat(data.price),
        category: parseInt(data.category),
        preparation_time: parseInt(data.preparation_time || "15"),
        calories: data.calories ? parseInt(data.calories) : null,
      };
      return item ? menuItemApi.update(item.id, payload) : menuItemApi.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["menu-items"] });
      queryClient.invalidateQueries({ queryKey: ["category-items"] });
      toast.success(item ? "Item updated!" : "Item created!");
      onClose();
    },
    onError: (err: any) => {
      const msg = err?.response?.data
        ? Object.values(err.response.data).flat().join(", ")
        : "Failed to save item";
      toast.error(msg as string);
    },
  });

  const foodType = watch("food_type");

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="bg-white dark:bg-gray-900 rounded-3xl w-full max-w-xl shadow-2xl max-h-[92vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100 dark:border-gray-800 sticky top-0 bg-white dark:bg-gray-900 rounded-t-3xl z-10">
          <div>
            <h2 className="font-bold text-gray-900 dark:text-white text-lg">
              {item ? "Edit Menu Item" : "Add Menu Item"}
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              {item ? `Editing "${item.name}"` : "Fill in the details below"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center hover:bg-gray-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit((d) => mutate(d))} className="p-6 space-y-5">
          {/* Image */}
          <ImageUpload
            currentUrl={item?.image_url || item?.image}
            onFileChange={setImageFile}
            label="Item Photo"
          />

          {/* Name + Category */}
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2 space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Item Name <span className="text-red-500">*</span>
              </label>
              <Input
                {...register("name")}
                placeholder="e.g. Paneer Butter Masala"
                className="rounded-xl"
              />
              {errors.name && (
                <p className="text-xs text-red-500">{errors.name.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Category <span className="text-red-500">*</span>
              </label>
              <select
                {...register("category")}
                className="w-full h-10 rounded-xl border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">Select category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.icon} {c.name}
                  </option>
                ))}
              </select>
              {errors.category && (
                <p className="text-xs text-red-500">{errors.category.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Food Type <span className="text-red-500">*</span>
              </label>
              <select
                {...register("food_type")}
                className="w-full h-10 rounded-xl border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="veg">🟢 Vegetarian</option>
                <option value="non_veg">🔴 Non-Vegetarian</option>
                <option value="vegan">🟣 Vegan</option>
              </select>
            </div>
          </div>

          {/* Price + Prep + Calories */}
          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Price (₹) <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm font-medium">
                  ₹
                </span>
                <Input
                  {...register("price")}
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0"
                  className="rounded-xl pl-7"
                />
              </div>
              {errors.price && (
                <p className="text-xs text-red-500">{errors.price.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Prep Time (min)
              </label>
              <Input
                {...register("preparation_time")}
                type="number"
                min="1"
                placeholder="15"
                className="rounded-xl"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Calories
              </label>
              <Input
                {...register("calories")}
                type="number"
                min="0"
                placeholder="Optional"
                className="rounded-xl"
              />
            </div>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Description
            </label>
            <textarea
              {...register("description")}
              rows={2}
              placeholder="Brief description of the item..."
              className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
            />
          </div>

          {/* Toggles */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Options
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(
                [
                  { field: "is_available", label: "Available", icon: "✅" },
                  { field: "is_popular", label: "Popular", icon: "⭐" },
                  { field: "is_special", label: "Special", icon: "👨‍🍳" },
                ] as const
              ).map(({ field, label, icon }) => (
                <label
                  key={field}
                  className="flex items-center gap-2 cursor-pointer bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl p-3 transition-colors"
                >
                  <input
                    type="checkbox"
                    {...register(field)}
                    className="w-4 h-4 rounded accent-emerald-600"
                  />
                  <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                    {icon} {label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="flex-1 rounded-xl"
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="brand"
              className="flex-1 rounded-xl"
              disabled={isPending}
            >
              {isPending ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Saving...
                </span>
              ) : item ? (
                "Update Item"
              ) : (
                "Add Item"
              )}
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
  const [filterCategory, setFilterCategory] = useState<string>("");

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
      categoryApi
        .list(user?.restaurant_id ?? undefined)
        .then((r) => r.data.results || r.data),
  });

  const { mutate: deleteItem } = useMutation({
    mutationFn: (id: number) => menuItemApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["menu-items"] });
      queryClient.invalidateQueries({ queryKey: ["category-items"] });
      toast.success("Item deleted");
    },
    onError: () => toast.error("Failed to delete item"),
  });

  const filtered = items.filter((item) => {
    const matchesSearch =
      !search ||
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.description?.toLowerCase().includes(search.toLowerCase());
    const matchesCat =
      !filterCategory || item.category.toString() === filterCategory;
    return matchesSearch && matchesCat;
  });

  const openAdd = () => {
    setEditItem(undefined);
    setModalOpen(true);
  };

  const openEdit = (item: MenuItem) => {
    setEditItem(item);
    setModalOpen(true);
  };

  return (
    <AdminLayout>
      <div className="p-6 space-y-5">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search items..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 rounded-xl"
            />
          </div>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="h-10 rounded-xl border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <Button variant="brand" onClick={openAdd} className="rounded-xl whitespace-nowrap">
            <Plus className="w-4 h-4" /> Add Item
          </Button>
        </div>

        {/* Count */}
        <p className="text-sm text-gray-500">
          {filtered.length} item{filtered.length !== 1 ? "s" : ""}
        </p>

        {/* Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-52 rounded-2xl" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <p className="text-4xl mb-2">🍽️</p>
            <p className="font-medium">
              {search ? "No items found" : "No menu items yet"}
            </p>
            {!search && (
              <Button
                variant="brand"
                onClick={openAdd}
                className="mt-4 rounded-xl"
              >
                <Plus className="w-4 h-4" /> Add First Item
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((item) => (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden group hover:shadow-lg transition-all duration-200"
              >
                <div className="relative h-36 bg-gray-100 dark:bg-gray-800">
                  <Image
                    src={getImageUrl(item.image_url || item.image)}
                    alt={item.name}
                    fill
                    className="object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src =
                        "/images/placeholder-food.jpg";
                    }}
                  />
                  {!item.is_available && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                      <span className="text-white text-xs font-bold bg-black/50 px-2 py-1 rounded-full">
                        Unavailable
                      </span>
                    </div>
                  )}
                  <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => openEdit(item)}
                      className="w-8 h-8 bg-white rounded-xl shadow-md flex items-center justify-center hover:bg-emerald-50 hover:text-emerald-600 transition-colors"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Delete "${item.name}"?`))
                          deleteItem(item.id);
                      }}
                      className="w-8 h-8 bg-white rounded-xl shadow-md flex items-center justify-center hover:bg-red-50 hover:text-red-500 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <div className="p-4">
                  <div className="flex items-center gap-1.5 mb-1">
                    <FoodTypeBadge type={item.food_type} />
                    <h3 className="font-semibold text-gray-900 dark:text-white text-sm truncate">
                      {item.name}
                    </h3>
                  </div>
                  <p className="text-xs text-gray-400 mb-2 truncate">
                    {item.category_name}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-emerald-600 text-sm">
                      {formatPrice(item.price)}
                    </span>
                    <div className="flex gap-1">
                      {item.is_popular && (
                        <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full font-medium">
                          Popular
                        </span>
                      )}
                      {item.is_special && (
                        <span className="text-[10px] bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded-full font-medium">
                          Special
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
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
