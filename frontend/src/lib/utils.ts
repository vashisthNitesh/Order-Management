import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { FoodType } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: string | number): string {
  const num = typeof price === "string" ? parseFloat(price) : price;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(num);
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800 border-yellow-200",
    confirmed: "bg-blue-100 text-blue-800 border-blue-200",
    preparing: "bg-orange-100 text-orange-800 border-orange-200",
    ready: "bg-green-100 text-green-800 border-green-200",
    served: "bg-gray-100 text-gray-800 border-gray-200",
    cancelled: "bg-red-100 text-red-800 border-red-200",
  };
  return colors[status] || "bg-gray-100 text-gray-800";
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: "Order Received",
    confirmed: "Confirmed",
    preparing: "Preparing",
    ready: "Ready to Serve",
    served: "Served",
    cancelled: "Cancelled",
  };
  return labels[status] || status;
}

export function getFoodTypeColor(foodType: FoodType): string {
  const colors: Record<FoodType, string> = {
    veg: "text-green-600 border-green-500",
    non_veg: "text-red-600 border-red-500",
    vegan: "text-emerald-600 border-emerald-500",
  };
  return colors[foodType];
}

export function getFoodTypeLabel(foodType: FoodType): string {
  const labels: Record<FoodType, string> = {
    veg: "Veg",
    non_veg: "Non-Veg",
    vegan: "Vegan",
  };
  return labels[foodType];
}

export function getOrderStatusSteps() {
  return [
    { status: "pending", label: "Order Received", icon: "clipboard" },
    { status: "confirmed", label: "Confirmed", icon: "check-circle" },
    { status: "preparing", label: "Preparing", icon: "chef-hat" },
    { status: "ready", label: "Ready", icon: "bell" },
    { status: "served", label: "Served", icon: "utensils" },
  ];
}

export function getImageUrl(path: string | null | undefined): string {
  if (!path) return "/images/placeholder-food.jpg";
  if (path.startsWith("http")) return path;
  return `${process.env.NEXT_PUBLIC_MEDIA_URL || "http://localhost:8000"}${path}`;
}
