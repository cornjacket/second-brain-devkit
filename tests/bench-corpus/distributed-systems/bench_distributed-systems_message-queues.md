---
tags: [bench, distributed-systems]
---

# Message Queues and Brokers

Message queues decouple producers from consumers across a network by durably buffering records in a broker, absorbing bursts and letting the two sides scale and fail independently. A log-structured broker like Kafka appends messages to partitioned, replicated commit logs and tracks each consumer group's committed offset, giving replayable ordered delivery within a partition. Traditional brokers push messages and delete them on acknowledgement, offering per-message acking and dead-letter queues for poison messages. Delivery semantics range from at-most-once to at-least-once to exactly-once, the last requiring idempotent consumers or transactional offset commits since the network can duplicate or reorder. Consumer groups rebalance partitions when members join or leave, and slow consumers create lag measured against the log head. In-flight visibility timeouts, acknowledgement deadlines, and redelivery on consumer crash make the broker the durable coordination point between otherwise independent services.
