"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, Edit2, Trash2, X, Tag, Calendar } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Offer } from "@/types";
import { offerApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { AdminLayout } from "@/components/admin/AdminLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils";
import toast from "react-hot-toast";

function OfferModal({ offer, onClose, restaurantId }: { offer?: Offer; onClose: () => void; restaurantId: number }) {
  const queryClient = useQueryClient();
  const { register, handleSubmit } = useForm({
    defaultValues: {
      title: offer?.title || "",
      description: offer?.description || "",
      discount_type: offer?.discount_type || "percentage",
      discount_value: offer?.discount_value || "",
      min_order_amount: offer?.min_order_amount || "0",
      start_date: offer?.start_date?.slice(0, 16) || "",
      end_date: offer?.end_date?.slice(0, 16) || "",
      is_active: offer?.is_active ?? true,
      promo_code: offer?.promo_code || "",
    },
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (data: any) => {
      const payload = { ...data, restaurant: restaurantId };
      return offer ? offerApi.update(offer.id, payload) : offerApi.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["offers"] });
      toast.success(offer ? "Offer updated!" : "Offer created!");
      onClose();
    },
    onError: () => toast.error("Failed to save offer"),
  });

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white dark:bg-gray-900 rounded-3xl p-6 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-bold text-gray-900 dark:text-white">{offer ? "Edit Offer" : "Create Offer"}</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center"><X className="w-4 h-4" /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutate(d))} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Title *</label>
            <Input {...register("title")} placeholder="e.g. Happy Hour Special" required />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Description</label>
            <textarea {...register("description")} rows={2} placeholder="Offer description..." className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm resize-none" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Discount Type</label>
              <select {...register("discount_type")} className="w-full h-10 rounded-xl border border-input bg-background px-3 text-sm">
                <option value="percentage">Percentage (%)</option>
                <option value="fixed">Fixed Amount (₹)</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Discount Value *</label>
              <Input {...register("discount_value")} type="number" step="0.01" placeholder="20" required />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Min Order Amount (₹)</label>
              <Input {...register("min_order_amount")} type="number" step="0.01" placeholder="0" />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Promo Code</label>
              <Input {...register("promo_code")} placeholder="SAVE20" />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Start Date *</label>
              <Input {...register("start_date")} type="datetime-local" required />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">End Date *</label>
              <Input {...register("end_date")} type="datetime-local" required />
            </div>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" {...register("is_active")} className="w-4 h-4 accent-emerald-600" />
            <span className="text-sm text-gray-700 dark:text-gray-300">Active</span>
          </label>
          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1 rounded-xl">Cancel</Button>
            <Button type="submit" variant="brand" className="flex-1 rounded-xl" disabled={isPending}>
              {isPending ? "Saving..." : offer ? "Update" : "Create"}
            </Button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

export default function AdminOffersPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editOffer, setEditOffer] = useState<Offer | undefined>();
  const restaurantId = user?.restaurant_id || 1;

  const { data: offers = [], isLoading } = useQuery<Offer[]>({
    queryKey: ["offers", restaurantId],
    queryFn: () => offerApi.list({ restaurant: restaurantId }).then((r) => r.data.results || r.data),
  });

  const { mutate: deleteOffer } = useMutation({
    mutationFn: (id: number) => offerApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["offers"] });
      toast.success("Offer deleted");
    },
  });

  return (
    <AdminLayout>
      <div className="p-6 space-y-5">
        <div className="flex justify-end">
          <Button variant="brand" onClick={() => { setEditOffer(undefined); setModalOpen(true); }} className="rounded-xl">
            <Plus className="w-4 h-4" /> Create Offer
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-28 rounded-2xl" />)}
          </div>
        ) : (
          <div className="space-y-3">
            {offers.map((offer) => (
              <motion.div
                key={offer.id}
                layout
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-5 flex items-center gap-4"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-emerald-600 to-teal-500 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Tag className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <h3 className="font-bold text-gray-900 dark:text-white truncate">{offer.title}</h3>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${offer.is_valid ? "bg-green-100 text-green-600" : "bg-gray-100 text-gray-500"}`}>
                      {offer.is_valid ? "Active" : "Expired"}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mb-1">{offer.description}</p>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span className="font-bold text-orange-500">{offer.discount_display}</span>
                    {offer.promo_code && <span className="font-mono bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded">{offer.promo_code}</span>}
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(offer.end_date).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex gap-1.5">
                  <button onClick={() => { setEditOffer(offer); setModalOpen(true); }} className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center hover:text-blue-500 transition-colors">
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button onClick={() => { if (confirm("Delete?")) deleteOffer(offer.id); }} className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center hover:text-red-500 transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {offers.length === 0 && !isLoading && (
          <div className="text-center py-16 text-gray-400">
            <div className="text-4xl mb-2">🏷️</div>
            <p className="font-medium">No offers yet</p>
          </div>
        )}
      </div>

      {modalOpen && (
        <OfferModal offer={editOffer} onClose={() => setModalOpen(false)} restaurantId={restaurantId} />
      )}
    </AdminLayout>
  );
}
