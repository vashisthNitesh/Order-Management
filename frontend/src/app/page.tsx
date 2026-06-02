"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  QrCode,
  UtensilsCrossed,
  Users,
  ChefHat,
  Smartphone,
  ClipboardList,
  CheckCircle2,
  Zap,
  Star,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12 } },
};

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 overflow-hidden">

      {/* ── HERO ────────────────────────────────────────────────────── */}
      <section className="mesh-bg relative min-h-[92vh] flex flex-col items-center justify-center text-center px-4 py-24">
        {/* Decorative blobs */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-emerald-500/10 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-400/10 rounded-full blur-3xl animate-float [animation-delay:2s]" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-900/20 rounded-full blur-3xl" />
        </div>

        <motion.div
          variants={stagger}
          initial="hidden"
          animate="show"
          className="relative z-10 max-w-4xl mx-auto"
        >
          {/* Pill badge */}
          <motion.div variants={fadeUp} className="mb-6 flex justify-center">
            <span className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-1.5 rounded-full text-sm font-medium backdrop-blur-sm">
              <Zap className="w-3.5 h-3.5 fill-emerald-400" />
              Smart Restaurant Ordering
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            variants={fadeUp}
            className="text-5xl md:text-7xl font-extrabold text-white mb-6 leading-[1.08] tracking-tight"
          >
            Scan. Order.{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-300">
              Enjoy.
            </span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            variants={fadeUp}
            className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            A seamless QR-based ordering experience for your restaurant — no app
            download, no waiting, no friction. Just great food, fast.
          </motion.p>

          {/* CTA buttons */}
          <motion.div
            variants={fadeUp}
            className="flex flex-col sm:flex-row items-center justify-center gap-3"
          >
            <Link href="/menu/1">
              <Button
                variant="brand"
                size="xl"
                className="rounded-2xl w-full sm:w-auto"
              >
                View Menu <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
            <Link href="/staff/login">
              <Button
                variant="outline"
                size="xl"
                className="rounded-2xl w-full sm:w-auto border-white/10 text-white hover:bg-white/10 hover:text-white bg-transparent"
              >
                Staff Login
              </Button>
            </Link>
          </motion.div>
        </motion.div>

        {/* Floating food emoji cards */}
        <div className="pointer-events-none absolute bottom-8 left-0 right-0 flex justify-center gap-4 px-4 opacity-30 select-none">
          {["🍔", "🍕", "🥗", "🍣", "🍝", "🍰"].map((emoji, i) => (
            <span
              key={i}
              className="text-3xl animate-float"
              style={{ animationDelay: `${i * 0.4}s` }}
            >
              {emoji}
            </span>
          ))}
        </div>
      </section>

      {/* ── STATS BAR ───────────────────────────────────────────────── */}
      <section className="bg-emerald-600 py-5">
        <div className="max-w-5xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center text-white">
            {[
              { value: "2 min", label: "Avg. order time" },
              { value: "23+", label: "Menu items" },
              { value: "7", label: "Categories" },
              { value: "10", label: "Tables" },
            ].map((s) => (
              <div key={s.label}>
                <p className="text-2xl font-extrabold">{s.value}</p>
                <p className="text-emerald-100 text-xs mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── PORTALS ─────────────────────────────────────────────────── */}
      <section className="py-20 px-4 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-3">
              One system, three portals
            </h2>
            <p className="text-gray-500 dark:text-gray-400 max-w-xl mx-auto">
              Customers order from their phone, staff manage from the dashboard,
              admins control everything from the back office.
            </p>
          </motion.div>

          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid md:grid-cols-3 gap-6"
          >
            {[
              {
                icon: <Smartphone className="w-6 h-6" />,
                color: "from-emerald-500 to-teal-400",
                shadow: "shadow-emerald-200/60 dark:shadow-emerald-900/30",
                title: "Customer Menu",
                desc: "Scan the QR code on your table, browse the full menu, add items to cart and place your order in seconds.",
                href: "/menu/1",
                cta: "Browse Menu",
              },
              {
                icon: <ClipboardList className="w-6 h-6" />,
                color: "from-violet-500 to-purple-400",
                shadow: "shadow-violet-200/60 dark:shadow-violet-900/30",
                title: "Staff Dashboard",
                desc: "Live incoming orders, one-tap status updates, kitchen display view. Built for speed on the floor.",
                href: "/staff/login",
                cta: "Staff Login",
              },
              {
                icon: <Users className="w-6 h-6" />,
                color: "from-rose-500 to-pink-400",
                shadow: "shadow-rose-200/60 dark:shadow-rose-900/30",
                title: "Admin Panel",
                desc: "Manage menu items, categories, offers, tables, and staff. Full control with real-time analytics.",
                href: "/admin/login",
                cta: "Admin Login",
              },
            ].map((card) => (
              <motion.div
                key={card.title}
                variants={fadeUp}
                className="group bg-white dark:bg-gray-800 rounded-3xl p-7 border border-gray-100 dark:border-gray-700 hover:shadow-xl hover:-translate-y-1.5 transition-all duration-300"
              >
                <div
                  className={`w-12 h-12 bg-gradient-to-br ${card.color} rounded-2xl flex items-center justify-center text-white mb-5 shadow-lg ${card.shadow}`}
                >
                  {card.icon}
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                  {card.title}
                </h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed mb-5">
                  {card.desc}
                </p>
                <Link
                  href={card.href}
                  className={`inline-flex items-center gap-1.5 text-sm font-semibold bg-gradient-to-r ${card.color} bg-clip-text text-transparent group-hover:gap-2.5 transition-all`}
                >
                  {card.cta} <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-current transition-colors" />
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── HOW IT WORKS ────────────────────────────────────────────── */}
      <section className="py-20 px-4 bg-white dark:bg-gray-950">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-14"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-3">
              How it works
            </h2>
            <p className="text-gray-500 dark:text-gray-400">
              Order your food in three simple steps — no app needed.
            </p>
          </motion.div>

          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid md:grid-cols-3 gap-8 relative"
          >
            {/* connector line (desktop) */}
            <div className="hidden md:block absolute top-10 left-[calc(16.67%+24px)] right-[calc(16.67%+24px)] h-px bg-gradient-to-r from-emerald-200 via-teal-200 to-emerald-200 dark:from-emerald-900 dark:via-teal-900 dark:to-emerald-900" />

            {[
              {
                step: "01",
                icon: <QrCode className="w-6 h-6" />,
                title: "Scan the QR code",
                desc: "Each table has a unique QR code. Scan it with your phone camera to instantly open the menu.",
              },
              {
                step: "02",
                icon: <UtensilsCrossed className="w-6 h-6" />,
                title: "Browse & add to cart",
                desc: "Explore categories, check out today's specials, and add your favourites to the cart.",
              },
              {
                step: "03",
                icon: <CheckCircle2 className="w-6 h-6" />,
                title: "Place order & track",
                desc: "Review your order, hit confirm, and track it live — from kitchen to your table.",
              },
            ].map((s) => (
              <motion.div
                key={s.step}
                variants={fadeUp}
                className="flex flex-col items-center text-center"
              >
                <div className="relative mb-5">
                  <div className="w-16 h-16 bg-emerald-50 dark:bg-emerald-900/30 rounded-2xl flex items-center justify-center text-emerald-600 dark:text-emerald-400 z-10 relative border border-emerald-100 dark:border-emerald-800">
                    {s.icon}
                  </div>
                  <span className="absolute -top-2 -right-2 w-5 h-5 bg-emerald-600 text-white text-[10px] font-black rounded-full flex items-center justify-center">
                    {s.step.slice(1)}
                  </span>
                </div>
                <h3 className="font-bold text-gray-900 dark:text-white mb-2">
                  {s.title}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
                  {s.desc}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── FEATURES GRID ───────────────────────────────────────────── */}
      <section className="py-20 px-4 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-3">
              Everything your restaurant needs
            </h2>
          </motion.div>

          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid grid-cols-2 md:grid-cols-3 gap-4"
          >
            {[
              { icon: "🔲", label: "QR Code per table" },
              { icon: "🛒", label: "Real-time cart" },
              { icon: "📡", label: "Live order tracking" },
              { icon: "👨‍🍳", label: "Kitchen display view" },
              { icon: "📊", label: "Admin dashboard" },
              { icon: "🏷️", label: "Promotional offers" },
              { icon: "🥗", label: "Veg / Non-Veg tags" },
              { icon: "⭐", label: "Popular & specials" },
              { icon: "📱", label: "Mobile-first design" },
            ].map((f) => (
              <motion.div
                key={f.label}
                variants={fadeUp}
                className="bg-white dark:bg-gray-800 rounded-2xl p-5 flex items-center gap-3 border border-gray-100 dark:border-gray-700 hover:border-emerald-200 dark:hover:border-emerald-800 transition-colors"
              >
                <span className="text-2xl flex-shrink-0">{f.icon}</span>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {f.label}
                </span>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── BOTTOM CTA ──────────────────────────────────────────────── */}
      <section className="mesh-bg py-24 px-4 text-center relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-emerald-500/10 rounded-full blur-3xl" />
        </div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="relative z-10 max-w-xl mx-auto"
        >
          <div className="text-5xl mb-4">🍽️</div>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to order?
          </h2>
          <p className="text-gray-400 mb-8">
            Scan the QR code at your table or browse the menu directly.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/menu/1">
              <Button variant="brand" size="lg" className="rounded-2xl w-full sm:w-auto">
                Open Menu <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link href="/admin/login">
              <Button
                variant="outline"
                size="lg"
                className="rounded-2xl w-full sm:w-auto border-white/10 text-white hover:bg-white/10 hover:text-white bg-transparent"
              >
                Admin Login
              </Button>
            </Link>
          </div>
        </motion.div>
      </section>

    </div>
  );
}
