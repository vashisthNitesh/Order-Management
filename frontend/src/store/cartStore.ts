import { create } from "zustand";
import { persist } from "zustand/middleware";
import { CartItem, MenuItem } from "@/types";

interface CartStore {
  items: CartItem[];
  tableId: number | null;
  restaurantId: number | null;
  isOpen: boolean;

  setTable: (tableId: number, restaurantId: number) => void;
  addItem: (menuItem: MenuItem, quantity?: number, specialInstructions?: string) => void;
  removeItem: (menuItemId: number) => void;
  updateQuantity: (menuItemId: number, quantity: number) => void;
  clearCart: () => void;
  toggleCart: () => void;
  openCart: () => void;
  closeCart: () => void;

  // Computed
  totalItems: () => number;
  totalPrice: () => number;
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      items: [],
      tableId: null,
      restaurantId: null,
      isOpen: false,

      setTable: (tableId, restaurantId) => set({ tableId, restaurantId }),

      addItem: (menuItem, quantity = 1, specialInstructions = "") => {
        const { items } = get();
        const existing = items.find((i) => i.menuItem.id === menuItem.id);
        if (existing) {
          set({
            items: items.map((i) =>
              i.menuItem.id === menuItem.id
                ? { ...i, quantity: i.quantity + quantity }
                : i
            ),
          });
        } else {
          set({ items: [...items, { menuItem, quantity, specialInstructions }] });
        }
      },

      removeItem: (menuItemId) => {
        set({ items: get().items.filter((i) => i.menuItem.id !== menuItemId) });
      },

      updateQuantity: (menuItemId, quantity) => {
        if (quantity <= 0) {
          get().removeItem(menuItemId);
          return;
        }
        set({
          items: get().items.map((i) =>
            i.menuItem.id === menuItemId ? { ...i, quantity } : i
          ),
        });
      },

      clearCart: () => set({ items: [], isOpen: false }),

      toggleCart: () => set((s) => ({ isOpen: !s.isOpen })),
      openCart: () => set({ isOpen: true }),
      closeCart: () => set({ isOpen: false }),

      totalItems: () => get().items.reduce((sum, i) => sum + i.quantity, 0),

      totalPrice: () =>
        get().items.reduce(
          (sum, i) => sum + parseFloat(i.menuItem.price) * i.quantity,
          0
        ),
    }),
    {
      name: "restaurant-cart",
      partialize: (state) => ({
        items: state.items,
        tableId: state.tableId,
        restaurantId: state.restaurantId,
      }),
    }
  )
);
