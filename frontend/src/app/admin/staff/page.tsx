"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, Edit2, Trash2, X, UserCheck } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { StaffProfile } from "@/types";
import { staffApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { AdminLayout } from "@/components/admin/AdminLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import toast from "react-hot-toast";

const ROLE_COLORS: Record<string, string> = {
  admin: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  manager: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  waiter: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  kitchen: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
};

function StaffModal({ onClose, restaurantId }: { onClose: () => void; restaurantId: number }) {
  const queryClient = useQueryClient();
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      username: "",
      email: "",
      first_name: "",
      last_name: "",
      password: "",
      role: "waiter",
      phone: "",
    },
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (data: any) => staffApi.create({ ...data, restaurant: restaurantId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["staff"] });
      toast.success("Staff account created!");
      onClose();
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.username?.[0] || err?.response?.data?.email?.[0] || "Failed to create staff";
      toast.error(msg);
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white dark:bg-gray-900 rounded-3xl p-6 w-full max-w-md shadow-2xl"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-bold text-gray-900 dark:text-white">Create Staff Account</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center"><X className="w-4 h-4" /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutate(d))} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">First Name *</label>
              <Input {...register("first_name")} placeholder="John" required />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Last Name *</label>
              <Input {...register("last_name")} placeholder="Doe" required />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Username *</label>
              <Input {...register("username")} placeholder="john.doe" required autoCapitalize="none" />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Role *</label>
              <select {...register("role")} className="w-full h-10 rounded-xl border border-input bg-background px-3 text-sm">
                <option value="waiter">Waiter</option>
                <option value="kitchen">Kitchen Staff</option>
                <option value="manager">Manager</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div className="col-span-2 space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Email *</label>
              <Input {...register("email")} type="email" placeholder="john@bistro.com" required />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Phone</label>
              <Input {...register("phone")} placeholder="+1 555 0000" />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Password *</label>
              <Input {...register("password")} type="password" placeholder="Min 8 chars" required minLength={8} />
            </div>
          </div>
          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1 rounded-xl">Cancel</Button>
            <Button type="submit" variant="brand" className="flex-1 rounded-xl" disabled={isPending}>
              {isPending ? "Creating..." : "Create Account"}
            </Button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

export default function AdminStaffPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const restaurantId = user?.restaurant_id || 1;

  const { data: staffList = [], isLoading } = useQuery<StaffProfile[]>({
    queryKey: ["staff", restaurantId],
    queryFn: () => staffApi.list({ restaurant: restaurantId }).then((r) => r.data.results || r.data),
  });

  const { mutate: deleteStaff } = useMutation({
    mutationFn: (id: number) => staffApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["staff"] });
      toast.success("Staff account removed");
    },
  });

  return (
    <AdminLayout>
      <div className="p-6 space-y-5">
        <div className="flex justify-end">
          <Button variant="brand" onClick={() => setModalOpen(true)} className="rounded-xl">
            <Plus className="w-4 h-4" /> Add Staff
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-2xl" />)}
          </div>
        ) : (
          <div className="space-y-3">
            {staffList.map((staff) => (
              <motion.div
                key={staff.id}
                layout
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-4 flex items-center gap-4"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                  {staff.full_name?.charAt(0) || staff.user.username?.charAt(0) || "?"}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <p className="font-semibold text-gray-900 dark:text-white truncate">{staff.full_name}</p>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${ROLE_COLORS[staff.role] || "bg-gray-100 text-gray-500"}`}>
                      {staff.role}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400">{staff.user.email}</p>
                  {staff.phone && <p className="text-xs text-gray-400">{staff.phone}</p>}
                </div>
                <div className="flex items-center gap-1.5">
                  <div className={`w-2 h-2 rounded-full ${staff.is_active ? "bg-green-500" : "bg-gray-300"}`} />
                  <button
                    onClick={() => { if (confirm("Remove this staff account?")) deleteStaff(staff.id); }}
                    className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {staffList.length === 0 && !isLoading && (
          <div className="text-center py-16 text-gray-400">
            <UserCheck className="w-10 h-10 mx-auto mb-2 opacity-50" />
            <p className="font-medium">No staff members yet</p>
          </div>
        )}
      </div>

      {modalOpen && (
        <StaffModal onClose={() => setModalOpen(false)} restaurantId={restaurantId} />
      )}
    </AdminLayout>
  );
}
