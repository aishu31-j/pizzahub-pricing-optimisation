# Data dictionary: pizzahub_orders.csv
Synthetic daily order data, 1 Jan - 30 Apr 2023, 4 regions (480 rows).

| Column | Type | Description |
|---|---|---|
| Date | date | Order date |
| Region | int | 1-4 |
| Unit Price | float | Price per pizza. Base $16; 5% discount in Region 3 from 1 Mar 2023 |
| Quantity Ordered | int | Pizzas ordered that day in the region |
| Distance | int | Miles from store: R1=2, R2=5, R3=9, R4=15 |
| Delivery Fees | float | $0.50/mile; 5% discount in Region 4 from 1 Mar 2023 |
| Discount Applied | int | 1 if the region's discount is active |

Costs: pizza $4 variable, delivery $0.50/mile variable, $5,000/yr fixed.