# Lab 8 Architectural Design: QuickBite Food Delivery

## System
QuickBite is a food delivery platform. Customers place orders, restaurants prepare food, riders deliver, and a dispatcher coordinates.

## Agents

| Agent | Type | Responsibilities | Percepts | Actions | Goals | Protocols | Characteristics |
|---|---|---|---|---|---|---|---|
| CustomerAgent | BDI | Place orders, track status, receive delivery | order confirmation, status updates | place_order, cancel_order, rate_delivery | get food delivered | order, status | one per customer |
| RestaurantAgent | Reactive | Accept orders, prepare food, notify ready | new order, preparation complete | accept_order, mark_ready, reject_order | fulfil orders | order, ready | one per restaurant |
| RiderAgent | Reactive | Accept pickup, deliver, report status | pickup assigned, delivery complete | accept_pickup, mark_delivered | deliver on time | pickup, delivery | many |
| Dispatcher | Orchestrator | Match orders to restaurants and riders, track progress | order placed, food ready, rider free | assign_restaurant, assign_rider, notify_customer | minimise delivery time | order, assignment, status | singleton |

## Interaction overview
1. Customer places an order -> Dispatcher.
2. Dispatcher assigns a restaurant -> Restaurant.
3. Restaurant prepares and marks ready -> Dispatcher.
4. Dispatcher assigns a rider -> Rider.
5. Rider picks up and delivers -> Customer.

## Agent classes
See agents.py.
