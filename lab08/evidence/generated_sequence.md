```mermaid
sequenceDiagram
    participant CustomerAgent as CustomerAgent
    participant Dispatcher as Dispatcher
    participant RestaurantAgent as RestaurantAgent
    participant RiderAgent as RiderAgent
    CustomerAgent->>Dispatcher: request: Place order: 2 jollof rice, 1 grilled tilapia
    Dispatcher->>RestaurantAgent: request: Prepare order for customer, 2 jollof rice + 1 tilapia
    RestaurantAgent-->>Dispatcher: accept: Order accepted, preparing
    RestaurantAgent-->>Dispatcher: inform: Food ready for pickup
    Dispatcher->>RiderAgent: request: Pick up order from restaurant and deliver to customer
    RiderAgent-->>Dispatcher: accept: Pickup accepted
    RiderAgent-->>CustomerAgent: inform: Order delivered
    CustomerAgent-->>Dispatcher: accept: Thank you, order received
```
