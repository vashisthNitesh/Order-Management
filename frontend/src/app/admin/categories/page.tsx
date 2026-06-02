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
import { ImageUpload } from "@/components/admin/ImageUpload";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import toast from "react-hot-toast";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  icon: z.string().optional(),
  sort_order: z.string().optional(),
  is_active: z.boolean(),
});

type FormData = z.infer<typeof schema>;

function CategoryModal({
  category,
  onClose,
  restaurantId,
}: {
  category?: Category;
  onClose: () => void;
  restaurantId: number;
}) {
  const queryClient = useQueryClient();
  const [imageFile, setImageFile] = useState<File | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
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
      if (imageFile) {
        const fd = new FormData();
        fd.append("name", data.name);
        fd.append("description", data.description || "");
        fd.append("icon", data.icon || "");
        fd.append("sort_order", data.sort_order || "0");
        fd.append("is_active", String(data.is_active));
        fd.append("restaurant", String(restaurantId));
        fd.append("image", imageFile);
        return category
          ? categoryApi.update(category.id, fd)
          : categoryApi.create(fd);
      }
      const payload = {
        ...data,
        restaurant: restaurantId,
        sort_order: parseInt(data.sort_order || "0"),
      };
      return category
        ? categoryApi.update(category.id, payload)
        : categoryApi.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      toast.success(category ? "Category updated!" : "Category created!");
      onClose();
    },
    onError: (err: any) => {
      const msg = err?.response?.data
        ? Object.values(err.response.data).flat().join(", ")
        : "Failed to save category";
      toast.error(msg as string);
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="bg-white dark:bg-gray-900 rounded-3xl w-full max-w-md shadow-2xl max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100 dark:border-gray-800 sticky top-0 bg-white dark:bg-gray-900 rounded-t-3xl z-10">
          <div>
            <h2 className="font-bold text-gray-900 dark:text-white text-lg">
              {category ? "Edit Category" : "Add Category"}
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              {category ? `Editing "${category.name}"` : "Create a new menu category"}
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
            currentUrl={category?.image_url}
            onFileChange={setImageFile}
            label="Category Image (optional)"
          />

          {/* Name + Icon */}
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2 space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Name <span className="text-red-500">*</span>
              </label>
              <Input
                {...register("name")}
                placeholder="e.g. Main Course"
                className="rounded-xl"
              />
              {errors.name && (
                <p className="text-xs text-red-500">{errors.name.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Emoji Icon
              </label>
              <Input
                {...register("icon")}
                placeholder="🍽️"
                className="rounded-xl text-center text-xl"
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
              placeholder="Optional short description..."
              className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
            />
          </div>

          {/* Sort order + Active */}
          <div className="flex items-center gap-4">
            <div className="w-32 space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Sort Order
              </label>
              <Input
                {...register("sort_order")}
                type="number"
                min="0"
                placeholder="0"
                className="rounded-xl"
              />
            </div>
            <label className="flex items-center gap-2 cursor-pointer mt-5">
              <input
                type="checkbox"
                {...register("is_active")}
                className="w-4 h-4 rounded accent-emerald-600"
              />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Active (visible on menu)
              </span>
            </label>
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
              ) : category ? (
                "Update Category"
              ) : (
                "Add Category"
              )}
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
    queryFn: () =>
      categoryApi.list(restaurantId).then((r) => r.data.results || r.data),
  });

  const { mutate: deleteCat } = useMutation({
    mutationFn: (id: number) => categoryApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      toast.success("Category deleted");
    },
    onError: () => toast.error("Failed to delete category"),
  });

  const openAdd = () => { setEditCat(undefined); setModalOpen(true); };
  const openEdit = (cat: Category) => { setEditCat(cat); setModalOpen(true); };

  return (
    <AdminLayout>
      <div className="p-6 space-y-5">
        <div className="flex justify-between items-center">
          <p className="text-sm text-gray-500">
            {categories.length} categor{categories.length !== 1 ? "ies" : "y"}
          </p>
          <Button variant="brand" onClick={openAdd} className="rounded-xl">
            <Plus className="w-4 h-4" /> Add Category
          </Button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-28 rounded-2xl" />
            ))}
          </div>
        ) : categories.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <p className="text-4xl mb-2">📂</p>
            <p className="font-medium">No categories yet</p>
            <Button variant="brand" onClick={openAdd} className="mt-4 rounded-xl">
              <Plus className="w-4 h-4" /> Add First Category
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {categories.map((cat) => (
              <motion.div
                key={cat.id}
                layout
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-5 hover:shadow-md transition-all duration-200 group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl flex items-center justify-center text-2xl border border-emerald-100 dark:border-emerald-800">
                      {cat.icon || "🍽️"}
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-900 dark:text-white">
                        {cat.name}
                      </h3>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {cat.item_count} item{cat.item_count !== 1 ? "s" : ""}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => openEdit(cat)}
                      className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center hover:bg-emerald-50 hover:text-emerald-600 transition-colors"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Delete "${cat.name}"?`)) deleteCat(cat.id);
                      }}
                      className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center hover:bg-red-50 hover:text-red-500 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                {cat.description && (
                  <p className="text-xs text-gray-500 mt-3 line-clamp-2">
                    {cat.description}
                  </p>
                )}
                {!cat.is_active && (
                  <span className="mt-2 inline-block text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full font-medium">
                    Inactive
                  </span>
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
