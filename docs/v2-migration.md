# Migration Guide: v1 to v2

## Overview

Version 2 introduces a more intuitive API with stronger typing and better transaction handling. This guide helps you transition existing code with clear examples and explanations.

## Quick Migration Checklist

1. Update client initialization to use `AppFactory`
2. Convert method calls to use `send` with explicit `args`
3. Replace `compose()` with `new_group()` for transactions
4. Access results through `abi_return` property
5. Use `CommonAppCallParams` for transaction parameters

## Step-by-Step Changes

> For the sake of brevity, the examples below are simplified and do not include all the details of the original code and are based on the ['helloworld'](../examples/helloworld/application.json) example.

### 1. Client Initialization (Factory Pattern)

**Before (v1):**

```python
# Direct client creation required manual setup
client = HelloWorldAppClient(
    algod_client=algod_client,
    indexer_client=indexer_client,
    creator=get_localnet_default_account(algod_client),
)
```

**After (v2):**

```python
# Factory handles deployment and configuration
factory = algorand.client.get_typed_app_factory(
    HelloWorldAppFactory,
    default_sender=deployer.address  # Sets default transaction sender
)
client, result = factory.deploy()  # Returns ready-to-use client along with the deployment result
```

### 2. Making Method Calls

**Before (v1):**

```python
# Positional arguments with implicit typing
response = client.hello(name="World")
```

**After (v2):**

```python
# Explicit arguments with type safety
response = client.send.hello(args=HelloArgs(name="World"))

# Simplified tuple syntax (still type-checked)
response = client.send.hello(args=("World",))

# Access typed return value
assert response.abi_return == "Hello, World"
```

### 3. Transaction Groups

**Before (v1):**

```python
# Chained compose() method
group = (client.compose()
    .hello(name="there")
    .hello_world_check(name="World")
).execute()
```

**After (v2):**

```python
# Clear group construction pattern
result = (client.new_group()  # Start transaction group
    .hello(args=("World",))  # First call
    .hello_world_check(args=HelloWorldCheckArgs(name="World"))  # Second call
    .send()  # Execute group
)

# Access all results with type inference
assert result.abi_return == "Hello, World"
```

### 4. Deployment Configuration

**Before (v1):**

```python
# Update parameters mixed with deployment logic
client.deploy(allow_delete=True, allow_update=True)
```

**After (v2):**

```python
# Clear separation of compilation parameters
client, result = factory.deploy(
    compilation_params={
        "deletable": True,  # Control app permissions
        "updatable": True,
    }
)
```

## Key Improvements

| Feature          | v1              | v2 Benefit                   |
| ---------------- | --------------- | ---------------------------- |
| **Typing**       | Implicit        | ARC-56 compliant dataclasses |
| **Transactions** | `compose()`     | Clear `new_group()` flow     |
| **Results**      | `.return_value` | Type-inferred `.abi_return`  |
| **Safety**       | Optional params | Required argument structures |

## Common Migration Issues

1. **Missing `args=` parameter**:
   → Fix: Wrap arguments in `args=YourArgsClass(...)` or `args=(...)`. Dataclasses can be imported from the generated client.

2. **`compose()` not found**:
   → Fix: Replace with `new_group()` and ensure chain ends with `.send()`

3. **Transaction parameter errors**:
   → Fix: Use `CommonAppCallParams` instead of raw transaction parameters

## Pro Tips

-   Use tuple syntax for simple methods: `args=("World",)`
-   Access `response.returns` for detailed simulation results
-   Combine factory patterns with `algokit-utils-py` v3 features for best results

Need help? Submit an issue on [GitHub](https://github.com/algorandfoundation/algokit-client-generator-py/issues), for reference on the application specification refer to [ARC-56 specification](https://arc.algorand.foundation/ARCs/arc-0056).

```

```
