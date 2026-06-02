export interface Restaurant {
  id: number;
  name: string;
  logo: string | null;
  logo_url?: string;
  address: string;
  phone: string;
  email: string;
  description: string;
  is_active: boolean;
}

export interface Table {
  id: number;
  restaurant: number;
  table_number: string;
  capacity: number;
  qr_code: string | null;
  qr_code_url: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Category {
  id: number;
  restaurant: number;
  name: string;
  description: string;
  icon: string;
  image_url: string | null;
  sort_order: number;
  is_active: boolean;
  item_count: number;
  items?: MenuItem[];
}

export type FoodType = 'veg' | 'non_veg' | 'vegan';

export interface MenuItem {
  id: number;
  category: number;
  category_name: string;
  name: string;
  description: string;
  image: string | null;
  image_url: string | null;
  price: string;
  food_type: FoodType;
  is_popular: boolean;
  is_special: boolean;
  is_available: boolean;
  preparation_time: number;
  calories: number | null;
  sort_order: number;
}

export type OrderStatus = 'pending' | 'confirmed' | 'preparing' | 'ready' | 'served' | 'cancelled';

export interface OrderItem {
  id: number;
  menu_item: number;
  menu_item_name: string;
  menu_item_image: string | null;
  quantity: number;
  unit_price: string;
  subtotal: string;
  special_instructions: string;
}

export interface OrderStatusHistory {
  id: number;
  status: OrderStatus;
  changed_by_name: string;
  note: string;
  created_at: string;
}

export interface Order {
  id: number;
  restaurant: number;
  table: number;
  table_number: string;
  order_number: string;
  status: OrderStatus;
  total_amount: string;
  special_instructions: string;
  customer_name: string;
  customer_phone: string;
  items: OrderItem[];
  status_history: OrderStatusHistory[];
  created_at: string;
  updated_at: string;
}

export interface Offer {
  id: number;
  restaurant: number;
  title: string;
  description: string;
  image_url: string | null;
  discount_type: 'percentage' | 'fixed';
  discount_value: string;
  min_order_amount: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  is_valid: boolean;
  discount_display: string;
  promo_code: string;
  usage_limit: number | null;
  usage_count: number;
}

export interface StaffProfile {
  id: number;
  user: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    is_active: boolean;
  };
  full_name: string;
  restaurant: number;
  role: 'admin' | 'manager' | 'waiter' | 'kitchen';
  phone: string;
  avatar: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_superuser: boolean;
  role: string;
  restaurant: string | null;
  restaurant_id: number | null;
}

export interface AuthTokens {
  access: string;
  refresh: string;
  user: AuthUser;
}

// Cart types (client-side only)
export interface CartItem {
  menuItem: MenuItem;
  quantity: number;
  specialInstructions?: string;
}

export interface DashboardStats {
  today_orders: number;
  today_revenue: number;
  pending_orders: number;
  preparing_orders: number;
  ready_orders: number;
  total_orders: number;
}
