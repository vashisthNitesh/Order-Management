"use client";

import { motion } from "framer-motion";
import { Tag } from "lucide-react";
import { Offer } from "@/types";

interface OfferBannerProps {
  offers: Offer[];
}

export function OfferBanner({ offers }: OfferBannerProps) {
  if (!offers.length) return null;

  return (
    <div className="overflow-x-auto scrollbar-hide">
      <div className="flex gap-3 pb-1">
        {offers.map((offer, i) => (
          <motion.div
            key={offer.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex-shrink-0 bg-gradient-to-r from-emerald-600 to-teal-500 rounded-2xl p-4 min-w-[260px] text-white relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-full -translate-y-6 translate-x-6" />
            <div className="absolute bottom-0 left-0 w-16 h-16 bg-white/10 rounded-full translate-y-4 -translate-x-4" />
            <div className="relative z-10">
              <div className="flex items-center gap-1.5 mb-1.5">
                <Tag className="w-3.5 h-3.5" />
                <span className="text-xs font-medium opacity-90">Limited Offer</span>
              </div>
              <h3 className="font-bold text-sm mb-0.5">{offer.title}</h3>
              <p className="text-xs opacity-80 line-clamp-1">{offer.description}</p>
              <div className="mt-2 inline-block bg-white/20 backdrop-blur-sm rounded-lg px-2.5 py-1 text-xs font-bold">
                {offer.discount_display}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
