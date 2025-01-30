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

### 5. State Access

**Before (v1):**

```python
# Global state access via dedicated method
global_response = client.get_global_state()
print(global_response.int1)  # 42
print(global_response.bytes1.as_str)  # "test"

# Local state required opt-in first
client.opt_in_opt_in()
local_response = client.get_local_state(account=None)
print(local_response.local_int1)  # 123

# Box state required manual transactions
```

**After (v2):**

```python
# Single entry point via .state property
global_state = client.state.global_state.get_all()
print(global_state["int1"])  # 42 (native int)
print(global_state["bytes1"].decode())  # "test"
## or access key directly via property
print(client.state.global_state.int1)
print(client.state.global_state.bytes1.decode())

# Explicit account for local state
local_state = client.state.local_state("ADDRESS").get_all()
print(local_state["local_int1"])  # 123
## or access key directly via property
print(client.state.local_state("ADDRESS").local_int1)

# Box access via same interface
box_key = client.state.boxes.box_key # access box key directly
all_boxes = client.state.boxes.get_all() # access all boxes
box_mapping = client.state.boxes.box_map.get_map() # access map directly
box_mapping_content = client.state.boxes.box_map.get_value(Inputs(add=InputsAdd(a=1, b=2), subtract=InputsSubtract(a=4, b=3))) # access map content directly by typed key
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
