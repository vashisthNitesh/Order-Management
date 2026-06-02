"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, QrCode, Download, Edit2, Trash2, X } from "lucide-react";
import Image from "next/image";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Table } from "@/types";
import { tableApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { AdminLayout } from "@/components/admin/AdminLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import toast from "react-hot-toast";

function TableModal({ table, onClose, restaurantId }: { table?: Table; onClose: () => void; restaurantId: number }) {
  const queryClient = useQueryClient();
  const { register, handleSubmit } = useForm({
    defaultValues: {
      table_number: table?.table_number || "",
      capacity: table?.capacity || 4,
    },
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (data: any) => {
      const payload = { ...data, restaurant: restaurantId };
      return table ? tableApi.update(table.id, payload) : tableApi.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tables"] });
      toast.success(table ? "Table updated!" : "Table created!");
      onClose();
    },
    onError: () => toast.error("Failed to save table"),
  });

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white dark:bg-gray-900 rounded-3xl p-6 w-full max-w-sm shadow-2xl"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-bold text-gray-900 dark:text-white">{table ? "Edit Table" : "Add Table"}</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center"><X className="w-4 h-4" /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutate(d))} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Table Number *</label>
            <Input {...register("table_number")} placeholder="e.g. 1, A1, VIP-1" required />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Capacity</label>
            <Input {...register("capacity")} type="number" min="1" placeholder="4" />
          </div>
          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1 rounded-xl">Cancel</Button>
            <Button type="submit" variant="brand" className="flex-1 rounded-xl" disabled={isPending}>
              {isPending ? "Saving..." : table ? "Update" : "Create"}
            </Button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

function QRModal({ table, onClose }: { table: Table; onClose: () => void }) {
  const queryClient = useQueryClient();

  const { mutate: regen, isPending } = useMutation({
    mutationFn: () => tableApi.regenerateQr(table.id, window.location.origin),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tables"] });
      toast.success("QR code regenerated!");
    },
  });

  const handleDownload = () => {
    if (!table.qr_code_url) return;
    const link = document.createElement("a");
    link.href = table.qr_code_url;
    link.download = `table-${table.table_number}-qr.png`;
    link.click();
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white dark:bg-gray-900 rounded-3xl p-6 w-full max-w-sm shadow-2xl text-center"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-bold text-gray-900 dark:text-white">QR Code - Table {table.table_number}</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center"><X className="w-4 h-4" /></button>
        </div>

        {table.qr_code_url ? (
          <div className="relative w-48 h-48 mx-auto mb-4 rounded-2xl overflow-hidden border-4 border-gray-100">
            <Image src={table.qr_code_url} alt={`QR Table ${table.table_number}`} fill className="object-contain" />
          </div>
        ) : (
          <div className="w-48 h-48 mx-auto mb-4 bg-gray-100 rounded-2xl flex items-center justify-center">
            <QrCode className="w-12 h-12 text-gray-400" />
          </div>
        )}

        <p className="text-xs text-gray-400 mb-4">
          Scan to order from Table {table.table_number}
        </p>

        <div className="flex gap-2">
          <Button variant="outline" onClick={() => regen()} disabled={isPending} className="flex-1 rounded-xl">
            {isPending ? "..." : "Regenerate"}
          </Button>
          <Button variant="brand" onClick={handleDownload} disabled={!table.qr_code_url} className="flex-1 rounded-xl">
            <Download className="w-4 h-4" /> Download
          </Button>
        </div>
      </motion.div>
    </div>
  );
}

export default function AdminTablesPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [tableModal, setTableModal] = useState(false);
  const [qrModal, setQrModal] = useState<Table | null>(null);
  const [editTable, setEditTable] = useState<Table | undefined>();
  const restaurantId = user?.restaurant_id || 1;

  const { data: tables = [], isLoading } = useQuery<Table[]>({
    queryKey: ["tables", restaurantId],
    queryFn: () => tableApi.list(restaurantId).then((r) => r.data.results || r.data),
  });

  const { mutate: deleteTable } = useMutation({
    mutationFn: (id: number) => tableApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tables"] });
      toast.success("Table deleted");
    },
  });

  return (
    <AdminLayout>
      <div className="p-6 space-y-5">
        <div className="flex justify-end">
          <Button variant="brand" onClick={() => { setEditTable(undefined); setTableModal(true); }} className="rounded-xl">
            <Plus className="w-4 h-4" /> Add Table
          </Button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-40 rounded-2xl" />)}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {tables.map((table) => (
              <motion.div
                key={table.id}
                layout
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-4 group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="text-xs text-gray-400 mb-0.5">Table</p>
                    <p className="text-2xl font-black text-gray-900 dark:text-white">{table.table_number}</p>
                  </div>
                  <div className={`w-2 h-2 rounded-full mt-1 ${table.is_active ? "bg-green-500" : "bg-gray-300"}`} />
                </div>
                <p className="text-xs text-gray-400 mb-4">Capacity: {table.capacity} guests</p>
                <div className="flex gap-1.5">
                  <button
                    onClick={() => setQrModal(table)}
                    className="flex-1 flex items-center justify-center gap-1 bg-orange-50 dark:bg-orange-900/20 text-orange-600 rounded-xl py-2 text-xs font-medium hover:bg-orange-100 transition-colors"
                  >
                    <QrCode className="w-3.5 h-3.5" /> QR
                  </button>
                  <button
                    onClick={() => { setEditTable(table); setTableModal(true); }}
                    className="w-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center hover:text-blue-500 transition-colors"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => { if (confirm("Delete table?")) deleteTable(table.id); }}
                    className="w-8 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {tableModal && (
        <TableModal table={editTable} onClose={() => setTableModal(false)} restaurantId={restaurantId} />
      )}
      {qrModal && (
        <QRModal table={qrModal} onClose={() => setQrModal(null)} />
      )}
    </AdminLayout>
  );
}
