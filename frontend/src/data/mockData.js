// Mock data for development and testing
export const mockOrders = [
  {
    id: 1,
    name: "Raj Kumar",
    phone: "9999999999",
    orders: [
      { item: "Cotton Shirt", qty: 10 },
      { item: "Denim Jeans", qty: 5 }
    ],
    time: "10:05 AM",
    date: "2024-10-17"
  },
  {
    id: 2,
    name: "Priya Sharma",
    phone: "8888888888",
    orders: [
      { item: "Silk Saree", qty: 3 }
    ],
    time: "11:20 AM",
    date: "2024-10-17"
  },
  {
    id: 3,
    name: "Amit Singh",
    phone: "7777777777",
    orders: [
      { item: "Cotton Shirt", qty: 2 },
      { item: "Formal Trousers", qty: 3 }
    ],
    time: "12:15 PM",
    date: "2024-10-17"
  },
  {
    id: 4,
    name: "Sneha Patel",
    phone: "6666666666",
    orders: [
      { item: "Designer Kurti", qty: 4 },
      { item: "Palazzo Pants", qty: 2 }
    ],
    time: "01:30 PM",
    date: "2024-10-17"
  },
  {
    id: 5,
    name: "Rohit Verma",
    phone: "5555555555",
    orders: [
      { item: "Polo T-Shirt", qty: 6 }
    ],
    time: "02:45 PM",
    date: "2024-10-17"
  },
  {
    id: 6,
    name: "Kavya Reddy",
    phone: "4444444444",
    orders: [
      { item: "Silk Saree", qty: 2 },
      { item: "Cotton Shirt", qty: 1 }
    ],
    time: "03:20 PM",
    date: "2024-10-17"
  },
  {
    id: 7,
    name: "Vikash Gupta",
    phone: "3333333333",
    orders: [
      { item: "Denim Jeans", qty: 3 },
      { item: "Casual Shirt", qty: 2 }
    ],
    time: "04:10 PM",
    date: "2024-10-17"
  },
  {
    id: 8,
    name: "Anita Joshi",
    phone: "2222222222",
    orders: [
      { item: "Traditional Lehenga", qty: 1 },
      { item: "Designer Kurti", qty: 2 }
    ],
    time: "05:00 PM",
    date: "2024-10-17"
  },
  {
    id: 9,
    name: "Suresh Yadav",
    phone: "1111111111",
    orders: [
      { item: "Formal Trousers", qty: 4 },
      { item: "Polo T-Shirt", qty: 3 }
    ],
    time: "06:15 PM",
    date: "2024-10-17"
  },
  {
    id: 10,
    name: "Meera Agarwal",
    phone: "9876543210",
    orders: [
      { item: "Cotton Shirt", qty: 2 },
      { item: "Palazzo Pants", qty: 3 },
      { item: "Designer Kurti", qty: 1 }
    ],
    time: "07:30 PM",
    date: "2024-10-17"
  }
];

// Utility functions for data processing
export const getOrdersSummary = (orders) => {
  const summary = {};
  
  orders.forEach(order => {
    const key = `${order.name}_${order.phone}`;
    if (!summary[key]) {
      summary[key] = {
        name: order.name,
        phone: order.phone,
        items: [],
        totalQuantity: 0
      };
    }
    
    order.orders.forEach(item => {
      const existingItem = summary[key].items.find(i => i.item === item.item);
      if (existingItem) {
        existingItem.qty += item.qty;
      } else {
        summary[key].items.push({ ...item });
      }
      summary[key].totalQuantity += item.qty;
    });
  });
  
  return Object.values(summary);
};

export const getTopItems = (orders, limit = 10) => {
  const itemCounts = {};
  
  orders.forEach(order => {
    order.orders.forEach(item => {
      itemCounts[item.item] = (itemCounts[item.item] || 0) + item.qty;
    });
  });
  
  return Object.entries(itemCounts)
    .sort(([,a], [,b]) => b - a)
    .slice(0, limit)
    .map(([item, count]) => ({ item, count }));
};

export const getDashboardStats = (orders) => {
  const totalOrders = orders.length;
  const uniqueCustomers = new Set(orders.map(order => order.phone)).size;
  const topItems = getTopItems(orders, 1);
  const mostOrderedItem = topItems.length > 0 ? topItems[0].item : 'N/A';
  const totalQuantity = orders.reduce((sum, order) => 
    sum + order.orders.reduce((orderSum, item) => orderSum + item.qty, 0), 0
  );
  
  return {
    totalOrders,
    uniqueCustomers,
    mostOrderedItem,
    totalQuantity
  };
};

export const getOrdersOverTime = (orders) => {
  const timeData = {};
  
  orders.forEach(order => {
    const hour = order.time.split(':')[0];
    const period = order.time.includes('PM') ? 'PM' : 'AM';
    const timeKey = `${hour}${period}`;
    
    timeData[timeKey] = (timeData[timeKey] || 0) + 1;
  });
  
  return Object.entries(timeData)
    .map(([time, count]) => ({ time, orders: count }))
    .sort((a, b) => {
      const getHour = (timeStr) => {
        const hour = parseInt(timeStr.slice(0, -2));
        const period = timeStr.slice(-2);
        return period === 'PM' && hour !== 12 ? hour + 12 : hour;
      };
      return getHour(a.time) - getHour(b.time);
    });
};
