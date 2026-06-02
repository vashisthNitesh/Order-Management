"use client";

import { FoodType } from "@/types";
import { cn } from "@/lib/utils";

interface FoodTypeBadgeProps {
  type: FoodType;
  size?: "sm" | "md";
}

export function FoodTypeBadge({ type, size = "sm" }: FoodTypeBadgeProps) {
  const colors: Record<FoodType, { dot: string; border: string }> = {
    veg: { dot: "bg-green-500", border: "border-green-500" },
    non_veg: { dot: "bg-red-500", border: "border-red-500" },
    vegan: { dot: "bg-emerald-500", border: "border-emerald-500" },
  };

  const { dot, border } = colors[type];
  const boxSize = size === "sm" ? "w-4 h-4" : "w-5 h-5";
  const dotSize = size === "sm" ? "w-2 h-2" : "w-2.5 h-2.5";

  return (
    <div
      className={cn(
        "inline-flex items-center justify-center rounded-sm border",
        boxSize,
        border
      )}
      title={type === "veg" ? "Vegetarian" : type === "non_veg" ? "Non-Vegetarian" : "Vegan"}
    >
      <div className={cn("rounded-full", dot, dotSize)} />
    </div>
  );
}
