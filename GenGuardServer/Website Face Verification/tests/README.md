# GenGuardServer





## Frameworks
### Flask
After initially utilizing Flask for our networking communications, we encountered several performance challenges during the development of our face verification signup process and QR code generation for users. Flask, a micro web framework written in Python, is well-suited for small to medium web applications due to its simplicity and flexibility. However, its synchronous nature posed limitations when handling concurrent requests, which led to performance bottlenecks.

To address these issues, we explored various frameworks and approaches. Our investigation led us to the concept of asynchronous communication between functions, which appeared to be a more efficient method for handling multiple requests simultaneously. This is when we discovered FastAPI.

### FastAPI
FastAPI is an asynchronous web framework, also written in Python, designed to build APIs with high performance. Unlike Flask, which processes requests synchronously, FastAPI uses asynchronous request handling to manage multiple requests at once without waiting for each one to complete before starting the next. This approach significantly improves the throughput and scalability of web applications, particularly in I/O-bound and high-concurrency environments.

**The switch to FastAPI was driven by the following considerations:**
1. Performance: FastAPI's asynchronous nature allows for non-blocking request handling, leading to higher throughput and better utilization of resources.
2. Scalability: The ability to handle numerous requests concurrently makes FastAPI a more scalable option for growing applications.
3. Modern Python Features: FastAPI leverages modern Python features like type hints and native async/await syntax, which enhances code quality and developer experience.



| Feature | Flask | FastAPI |
|---------|-------|---------|
| Programming Model | Synchronous | Asynchronous |
| Performance | Suitable for simpler, low to medium traffic applications | High performance, ideal for I/O-bound and high-concurrency applications |
| Ease of Use | Simple and flexible, great for beginners | Slightly steeper learning curve but offers more advanced features |
| Community Support | Mature with extensive community support | Growing community, increasingly popular in modern web development |
| Typing Support | Limited, mostly through extensions | Built-in support for Pydantic and type hints |
| Framework Maturity | Highly mature and stable | Relatively new but rapidly evolving |


This comparative analysis helped us determine that FastAPI was the more appropriate choice for our project's requirements, especially considering our need for efficient handling of high-concurrency tasks and the desire for a more scalable architecture.



## What is Asynchronous Programming?

Asynchronous programming is a method of concurrency that allows a unit of work to run separately from the main application thread. When the work is complete, it notifies the main thread with its result. In the context of web servers and applications, this means being able to handle multiple requests simultaneously, rather than sequentially.

### Key Concepts of Asynchronous Programming:

1. Non-Blocking Operations: Traditional synchronous programming halts the execution of further operations until the current one completes. Asynchronous programming, on the other hand, allows the execution of other tasks while waiting for an operation to complete.


2. Concurrency: Asynchronous programming enables concurrency, which is the ability to deal with many things at once. In a web server context, this means being able to handle multiple client requests concurrently.

3. Callbacks and Promises: Asynchronous programming often involves the use of callbacks or promises. A **callback** is a function that will be executed after a task completes, while a **promise** is an object that represents the eventual completion or failure of an asynchronous operation.


### Advantages of Asynchronous Programming:

1. Improved Performance and Responsiveness: By not blocking the thread while waiting for responses, asynchronous programming can significantly improve the performance and responsiveness of an application.
2. Better Resource Utilization: It allows for more efficient use of server resources, as threads are not idly waiting for I/O operations to complete.

### Real-World Example:

Imagine a restaurant as a web server. In a synchronous setup, a waiter (the server) takes an order from one table and waits at the kitchen (external service) until the order is ready before serving it and moving to the next table. In contrast, in an asynchronous setup, the waiter takes orders from multiple tables and while the kitchen is preparing them, continues to take more orders or serve other tables. The kitchen (external service) notifies the waiter when an order is ready. This way, the waiter (server) can handle multiple tables (requests) efficiently without idle waiting.

## pip install thorugh
export PIP_BREAK_SYSTEM_PACKAGES=true


### Progress Through work:
we managed to decrease the processing time of the model by resizing the image to the minial resulation and still be able to dedect 96.7% faces:

Face detection took 5.551442384719849 seconds
**To**
Face detection took 0.9049489498138428 seconds
**NEW model**
Detection Time: 0.0343 seconds

**©GenGuard**
