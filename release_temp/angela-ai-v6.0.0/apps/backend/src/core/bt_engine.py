import enum
from abc import ABC, abstractmethod
from typing import List, Any, Dict, Optional
import inspect

class NodeStatus(enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RUNNING = "RUNNING"

class Node(ABC):
    """Base class for all Behavior Tree nodes."""
    
    def __init__(self, name: str):
        self.name = name
        self.status = NodeStatus.FAILURE
        self.children: List['Node'] = []

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> NodeStatus:
        """Execute the node's logic."""
        pass

    def add_child(self, child: 'Node'):
        self.children.append(child)
        return self

class Composite(Node):
    """Base class for nodes that have children."""
    def __init__(self, name: str, children: List[Node] = None):
        super().__init__(name)
        if children:
            self.children = children

class Selector(Composite):
    """
    OR Logic: Tries children in order. 
    Returns SUCCESS if ANY child succeeds.
    Returns FAILURE only if ALL children fail.
    """
    async def run(self, context: Dict[str, Any]) -> NodeStatus:
        print(f"  [BT] Selector: {self.name}...")
        for child in self.children:
            result = await child.run(context)
            if result == NodeStatus.SUCCESS:
                print(f"    -> {child.name} SUCCEEDED. Selector {self.name} SUCCESS.")
                return NodeStatus.SUCCESS
            if result == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        
        print(f"    -> All children failed. Selector {self.name} FAILED.")
        return NodeStatus.FAILURE

class Sequence(Composite):
    """
    AND Logic: Runs children in order.
    Returns SUCCESS only if ALL children succeed.
    Returns FAILURE if ANY child fails.
    """
    async def run(self, context: Dict[str, Any]) -> NodeStatus:
        print(f"  [BT] Sequence: {self.name}...")
        for child in self.children:
            result = await child.run(context)
            if result == NodeStatus.FAILURE:
                print(f"    -> {child.name} FAILED. Sequence {self.name} FAILED.")
                return NodeStatus.FAILURE
            if result == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        
        print(f"    -> All children succeeded. Sequence {self.name} SUCCESS.")
        return NodeStatus.SUCCESS

class Condition(Node):
    """Leaf node that checks a condition."""
    def __init__(self, name: str, check_fn):
        super().__init__(name)
        self.check_fn = check_fn

    async def run(self, context: Dict[str, Any]) -> NodeStatus:
        if inspect.iscoroutinefunction(self.check_fn):
            result = await self.check_fn(context)
        else:
            result = self.check_fn(context)
            if inspect.isawaitable(result):
                result = await result
            
        status = NodeStatus.SUCCESS if result else NodeStatus.FAILURE
        print(f"  [BT] Condition: {self.name} -> {status.value}")
        return status

class Action(Node):
    """Leaf node that performs an action."""
    def __init__(self, name: str, action_fn):
        super().__init__(name)
        self.action_fn = action_fn

    async def run(self, context: Dict[str, Any]) -> NodeStatus:
        print(f"  [BT] Action: {self.name}...")
        try:
            if inspect.iscoroutinefunction(self.action_fn):
                result = await self.action_fn(context)
            else:
                result = self.action_fn(context)
                if inspect.isawaitable(result):
                    result = await result
                
            # If the action function returns a boolean, use it. Otherwise assume success if no exception.
            if isinstance(result, bool):
                status = NodeStatus.SUCCESS if result else NodeStatus.FAILURE
            else:
                status = NodeStatus.SUCCESS
            
            print(f"    -> Action {self.name} finished: {status.value}")
            return status
        except Exception as e:
            print(f"    -> Action {self.name} EXCEPTION: {e}")
            return NodeStatus.FAILURE
