import Link from "next/link";
import { ArrowRight, QrCode, UtensilsCrossed, Users } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-amber-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="max-w-6xl mx-auto px-4 py-20">
        {/* Hero */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <UtensilsCrossed className="w-4 h-4" />
            Smart Restaurant Ordering System
          </div>
          <h1 className="text-5xl md:text-7xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
            Order Smarter,{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-amber-500">
              Dine Better
            </span>
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto mb-10">
            Scan the QR code on your table to access the menu, place orders, and
            track your food — no app download required.
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              icon: <QrCode className="w-8 h-8 text-orange-500" />,
              title: "QR Code Ordering",
              desc: "Scan the QR on your table and browse the menu instantly. No login needed.",
              href: "/menu/1",
              cta: "View Menu",
            },
            {
              icon: <UtensilsCrossed className="w-8 h-8 text-blue-500" />,
              title: "Staff Dashboard",
              desc: "Real-time order management and kitchen display for restaurant staff.",
              href: "/staff/login",
              cta: "Staff Login",
            },
            {
              icon: <Users className="w-8 h-8 text-purple-500" />,
              title: "Admin Panel",
              desc: "Full control over menu, tables, offers, and staff management.",
              href: "/admin/login",
              cta: "Admin Login",
            },
          ].map((card) => (
            <Link
              key={card.title}
              href={card.href}
              className="group bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
            >
              <div className="mb-4">{card.icon}</div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                {card.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4 text-sm leading-relaxed">
                {card.desc}
              </p>
              <span className="inline-flex items-center gap-1.5 text-orange-500 font-medium text-sm group-hover:gap-2.5 transition-all">
                {card.cta} <ArrowRight className="w-4 h-4" />
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
