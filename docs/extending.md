### Creating Custom Components

#### Auto-Discovery of Components

The system automatically discovers and registers components from the following locations:
- `triggered/triggers/` - Custom trigger implementations
- `triggered/actions/` - Custom action implementations
- `triggered/tools/` - Custom tool implementations

You can override these paths using environment variables:
```bash
export TRIGGERED_TRIGGERS_MODULE="my_package.triggers"
export TRIGGERED_ACTIONS_MODULE="my_package.actions"
export TRIGGERED_TOOLS_MODULE="my_package.tools"
```

#### Adding a Custom Trigger

1. Create a new file in your triggers directory:
```python
from triggered.core import Trigger

class MyCustomTrigger(Trigger):
    name = "my-custom"  # This will be the trigger type
    description = "My custom trigger description"

    def __init__(self, config: dict):
        super().__init__(config)
        # Initialize your trigger

    async def check(self):
        # Implement trigger logic
        return TriggerContext(
            data={
                "trigger": True,  # or False
                "reason": "Trigger reason"
            }
        )
```

2. The trigger will be automatically discovered and registered.

#### Adding a Custom Action

1. Create a new file in your actions directory:
```python
from triggered.core import Action

class MyCustomAction(Action):
    name = "my-custom"  # This will be the action type
    description = "My custom action description"

    def __init__(self, config: dict):
        super().__init__(config)
        # Initialize your action

    async def execute(self, ctx):
        # Implement action logic
        return result
```

2. The action will be automatically discovered and registered.

#### Adding a Custom Tool

1. Create a new file in your tools directory:
```python
from triggered.tools import Tool

class MyCustomTool(Tool):
    name = "my_tool"
    description = "My custom tool description"

    async def execute(self, **kwargs):
        # Tool implementation
        return result
```

2. The tool will be automatically discovered and registered.

#### Manual Registration

If you prefer to register components manually or need more control, you can use the registration functions:

```python
from triggered.registry import register_trigger, register_action, register_tool

# Register a trigger
register_trigger("my-custom", MyCustomTrigger)

# Register an action
register_action("my-custom", MyCustomAction)

# Register a tool
register_tool("my-tool", MyCustomTool)
```

#### Component Structure

Your custom components directory should follow this structure:
```
my_components/
├── triggers/
│   ├── __init__.py
│   └── my_custom_trigger.py
├── actions/
│   ├── __init__.py
│   └── my_custom_action.py
└── tools/
    ├── __init__.py
    └── my_custom_tool.py
```

Each component should:
1. Inherit from the appropriate base class
2. Define a `name` and `description` class variable
3. Implement the required methods
4. Be placed in the correct directory

The system will automatically:
- Discover all components in the specified directories
- Register them with appropriate names
- Make them available in the CLI and API
