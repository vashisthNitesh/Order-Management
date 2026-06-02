"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, Edit2, Trash2, X } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Category } from "@/types";
import { categoryApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { AdminLayout } from "@/components/admin/AdminLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import toast from "react-hot-toast";

const schema = z.object({
  name: z.string().min(1, "Required"),
  description: z.string().optional(),
  icon: z.string().optional(),
  sort_order: z.string().optional(),
  is_active: z.boolean(),
});

type FormData = z.infer<typeof schema>;

function CategoryModal({ category, onClose, restaurantId }: { category?: Category; onClose: () => void; restaurantId: number }) {
  const queryClient = useQueryClient();
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: category?.name || "",
      description: category?.description || "",
      icon: category?.icon || "",
      sort_order: category?.sort_order?.toString() || "0",
      is_active: category?.is_active ?? true,
    },
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (data: FormData) => {
      const payload = { ...data, restaurant: restaurantId, sort_order: parseInt(data.sort_order || "0") };
      return category ? categoryApi.update(category.id, payload) : categoryApi.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      toast.success(category ? "Category updated!" : "Category created!");
      onClose();
    },
    onError: () => toast.error("Failed to save category"),
  });

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white dark:bg-gray-900 rounded-3xl p-6 w-full max-w-md shadow-2xl"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-bold text-gray-900 dark:text-white">{category ? "Edit Category" : "Add Category"}</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center"><X className="w-4 h-4" /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutate(d))} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2 space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Name *</label>
              <Input {...register("name")} placeholder="e.g. Starters" />
              {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Emoji Icon</label>
              <Input {...register("icon")} placeholder="🥗" />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Sort Order</label>
              <Input {...register("sort_order")} type="number" placeholder="0" />
            </div>
            <div className="col-span-2 space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Description</label>
              <Input {...register("description")} placeholder="Optional description" />
            </div>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" {...register("is_active")} className="w-4 h-4 accent-orange-500" />
            <span className="text-sm text-gray-700 dark:text-gray-300">Active</span>
          </label>
          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1 rounded-xl">Cancel</Button>
            <Button type="submit" variant="brand" className="flex-1 rounded-xl" disabled={isPending}>
              {isPending ? "Saving..." : category ? "Update" : "Create"}
            </Button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

export default function AdminCategoriesPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editCat, setEditCat] = useState<Category | undefined>();
  const restaurantId = user?.restaurant_id || 1;

  const { data: categories = [], isLoading } = useQuery<Category[]>({
    queryKey: ["categories", restaurantId],
    queryFn: () => categoryApi.list(restaurantId).then((r) => r.data.results || r.data),
  });

  const { mutate: deleteCat } = useMutation({
    mutationFn: (id: number) => categoryApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      toast.success("Category deleted");
    },
  });

  return (
    <AdminLayout>
      <div className="p-6 space-y-5">
        <div className="flex justify-end">
          <Button variant="brand" onClick={() => { setEditCat(undefined); setModalOpen(true); }} className="rounded-xl">
            <Plus className="w-4 h-4" /> Add Category
          </Button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-2xl" />)}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {categories.map((cat) => (
              <motion.div
                key={cat.id}
                layout
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-5 group relative"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-orange-50 dark:bg-orange-900/20 rounded-xl flex items-center justify-center text-2xl">
                      {cat.icon || "🍽️"}
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-900 dark:text-white">{cat.name}</h3>
                      <p className="text-xs text-gray-400">{cat.item_count} items</p>
                    </div>
                  </div>
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => { setEditCat(cat); setModalOpen(true); }}
                      className="w-7 h-7 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center hover:bg-blue-50 hover:text-blue-500 transition-colors"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => { if (confirm("Delete?")) deleteCat(cat.id); }}
                      className="w-7 h-7 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center hover:bg-red-50 hover:text-red-500 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                {!cat.is_active && (
                  <span className="absolute top-2 left-2 text-[10px] bg-gray-200 text-gray-500 px-2 py-0.5 rounded-full">Inactive</span>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {modalOpen && (
        <CategoryModal
          category={editCat}
          onClose={() => setModalOpen(false)}
          restaurantId={restaurantId}
        />
      )}
    </AdminLayout>
  );
}
